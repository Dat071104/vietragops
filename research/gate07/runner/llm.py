"""Sequential Groq research-mode runner with typed failures and resume cache."""

from __future__ import annotations

import argparse
from dotenv import load_dotenv
import json
from math import ceil
from pathlib import Path
import time

from rag.generation.groq_client import GroqClient
from rag.generation.provider_router import ProviderRouter
from research.gate07.baselines.llm import parse_llm_payload, render_llm_prompt
from research.gate07.baselines.models import RawOutputRecord
from research.gate07.harness.serialization import load_public_tasks
from research.gate07.runner.artifacts import RawArtifactWriter
from research.gate07.runner.rate_ledger import RateLimitLedger, limits_from_environment


ARM_IDS = ("llm_new_schema_only", "llm_old_new_direct", "llm_old_new_history", "llm_reasoning")
DEFAULT_MODELS = ("openai/gpt-oss-120b", "openai/gpt-oss-20b")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--request-ledger", required=True)
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS))
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args()


def _load_cache(path: Path) -> set[tuple[str, str, str, str]]:
    if not path.exists():
        return set()
    cache = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        cache.add((row["arm_id"], row["model"], row["case_id"], row["prompt_id"]))
    return cache


def _failure_kind(invocation) -> str:
    kind = invocation.failure_kind or "provider_error"
    return "provider_error" if kind == "config_error" else kind


def _append(output: Path, raw: RawArtifactWriter, arm_id: str, model: str, task: dict, prompt_id: str, prompt: str, prediction: dict | None, provider: str, latency_ms: float, outcome: str, failure_kind: str | None, error: str | None, raw_response: str | None, token_usage: dict[str, int]) -> None:
    raw_record = RawOutputRecord(arm_id, model, task["case_id"], prompt_id, prompt, raw_response, provider, latency_ms, token_usage, outcome, failure_kind, error)
    raw.append(raw_record)
    row = {"arm_id": arm_id, "model": model, "case_id": task["case_id"], "prompt_id": prompt_id, "prediction": prediction, "provider": provider, "latency_ms": latency_ms, "token_usage": token_usage, "outcome": outcome, "failure_kind": failure_kind, "error": error}
    with output.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")


def run() -> None:
    args = _args()
    project_root = Path(__file__).resolve().parents[3]
    load_dotenv(project_root / ".env", override=False)
    tasks = load_public_tasks(args.tasks)
    if args.preflight_only:
        tasks = tasks[:1]
    models = tuple(model.strip() for model in args.models.split(",") if model.strip())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    raw_path = Path(args.raw)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    ledger = RateLimitLedger(args.ledger, args.request_ledger, limits_from_environment())
    raw_writer = RawArtifactWriter(raw_path)
    cache = _load_cache(output)
    counts: dict[str, int] = {}
    try:
        for model in models:
            router = ProviderRouter(provider="groq", mode="research", groq_client=GroqClient(model=model))
            for arm_id in ARM_IDS:
                for task in tasks:
                    prompt_id, prompt = render_llm_prompt(arm_id, task)
                    key = (arm_id, model, task["case_id"], prompt_id)
                    if key in cache:
                        continue
                    input_tokens = max(1, ceil(len(prompt) / 4))
                    allowed, reason = ledger.allow(input_tokens, 512)
                    started = time.perf_counter()
                    if not allowed:
                        latency_ms = (time.perf_counter() - started) * 1000
                        _append(output, raw_writer, arm_id, model, task, prompt_id, prompt, None, "groq", latency_ms, "provider_failure", "rate_limited", f"preflight budget stop: {reason}", None, {"input_tokens_estimate": input_tokens, "output_tokens_actual": None})
                        ledger.record(arm_id=arm_id, model=model, case_id=task["case_id"], input_tokens=input_tokens, output_tokens=0, outcome="rate_limited")
                        cache.add(key)
                        counts["rate_limited"] = counts.get("rate_limited", 0) + 1
                        continue
                    invocation = router.generate_json(prompt, model=model, temperature=0.0, max_tokens=512)
                    latency_ms = (time.perf_counter() - started) * 1000
                    raw_response = json.dumps(invocation.payload, ensure_ascii=True, sort_keys=True) if invocation.payload is not None else None
                    if invocation.payload is None:
                        kind = _failure_kind(invocation)
                        _append(output, raw_writer, arm_id, model, task, prompt_id, prompt, None, invocation.provider, latency_ms, "provider_failure", kind, invocation.error, raw_response, {"input_tokens_estimate": input_tokens, "output_tokens_actual": None})
                        ledger.record(arm_id=arm_id, model=model, case_id=task["case_id"], input_tokens=input_tokens, output_tokens=512, outcome=kind)
                        counts[kind] = counts.get(kind, 0) + 1
                    else:
                        try:
                            prediction = parse_llm_payload(invocation.payload, task)
                        except ValueError as exc:
                            _append(output, raw_writer, arm_id, model, task, prompt_id, prompt, None, invocation.provider, latency_ms, "parse_failure", "parse_failure", str(exc), raw_response, {"input_tokens_estimate": input_tokens, "output_tokens_actual": None})
                            ledger.record(arm_id=arm_id, model=model, case_id=task["case_id"], input_tokens=input_tokens, output_tokens=512, outcome="parse_failure")
                            counts["parse_failure"] = counts.get("parse_failure", 0) + 1
                        else:
                            _append(output, raw_writer, arm_id, model, task, prompt_id, prompt, prediction, invocation.provider, latency_ms, "success", None, None, raw_response, {"input_tokens_estimate": input_tokens, "output_tokens_actual": None})
                            ledger.record(arm_id=arm_id, model=model, case_id=task["case_id"], input_tokens=input_tokens, output_tokens=512, outcome="success")
                            counts["success"] = counts.get("success", 0) + 1
                    cache.add(key)
    finally:
        ledger.close()
    print(json.dumps({"models": models, "arms": ARM_IDS, "tasks": len(tasks), "preflight_only": args.preflight_only, "counts": counts, "output": str(output), "raw": str(raw_path)}, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    run()
