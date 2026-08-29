"""Sequential Groq research-mode runner with typed failures and resume cache."""

from __future__ import annotations

import argparse
from dotenv import load_dotenv
import json
from math import ceil
from pathlib import Path
import random
import time
from typing import Any

from rag.generation.groq_client import GroqClient
from rag.generation.provider_router import ProviderRouter
from research.gate07.baselines.llm import parse_legacy_llm_payload, parse_llm_payload, render_llm_prompt
from research.gate07.baselines.models import RawOutputRecord
from research.gate07.harness.serialization import load_public_tasks
from research.gate07.protocol import preflight_headline_run
from research.gate07.runner.artifacts import RawArtifactWriter
from research.gate07.runner.rate_ledger import RateLimitLedger, limits_from_environment


ARM_IDS = ("llm_new_schema_only", "llm_old_new_direct", "llm_old_new_history", "llm_reasoning", "llm_old_new_direct_v3_legacy")
DEFAULT_MODELS = ("openai/gpt-oss-120b", "openai/gpt-oss-20b")
RUN_ORDER_SEED = 20260827
MAX_TOKENS = 1536
MAX_CLIENT_THROTTLE_CHECKS = 5


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--request-ledger", required=True)
    parser.add_argument("--protocol", required=True)
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
        if row.get("outcome", "success") == "success":
            cache.add((row["arm_id"], row["model"], row["case_id"], row["prompt_id"]))
    return cache


def _failure_kind(invocation) -> str:
    kind = invocation.failure_kind or "provider_error"
    return "provider_error" if kind == "config_error" else kind


def _append(
    output: Path,
    raw: RawArtifactWriter,
    arm_id: str,
    model: str,
    task: dict,
    prompt_id: str,
    prompt: str,
    prediction: dict | None,
    provider: str,
    latency_ms: float,
    outcome: str,
    failure_kind: str | None,
    error: str | None,
    raw_response: str | None,
    token_usage: dict[str, Any],
    provider_error_body: str | None = None,
) -> None:
    raw_record = RawOutputRecord(
        arm_id=arm_id,
        model=model,
        case_id=task["case_id"],
        prompt_id=prompt_id,
        rendered_prompt=prompt,
        raw_response=raw_response,
        provider=provider,
        latency_ms=latency_ms,
        token_usage=token_usage,
        outcome=outcome,
        failure_kind=failure_kind,
        error=error,
        provider_error_body=provider_error_body,
    )
    raw.append(raw_record)
    row = {
        "arm_id": arm_id,
        "model": model,
        "case_id": task["case_id"],
        "prompt_id": prompt_id,
        "prediction": prediction,
        "provider": provider,
        "latency_ms": latency_ms,
        "token_usage": token_usage,
        "outcome": outcome,
        "failure_kind": failure_kind,
        "error": error,
        "provider_error_body": provider_error_body,
    }
    with output.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")


def _ordered_arm_models(models: tuple[str, ...], *, seed: int = RUN_ORDER_SEED) -> tuple[tuple[str, str], ...]:
    order = [(arm_id, model) for arm_id in ARM_IDS for model in models]
    random.Random(seed).shuffle(order)
    return tuple(order)


def _token_usage(input_tokens_estimate: int, invocation) -> dict[str, Any]:
    usage = getattr(invocation, "usage", None) or {}
    return {
        "input_tokens_estimate": input_tokens_estimate,
        "input_tokens_actual": usage.get("input_tokens_actual"),
        "output_tokens_actual": usage.get("output_tokens_actual"),
        "total_tokens_actual": usage.get("total_tokens_actual"),
    }


def _ledger_tokens(token_usage: dict[str, Any], input_tokens_estimate: int) -> tuple[int, int]:
    input_tokens = token_usage.get("input_tokens_actual")
    output_tokens = token_usage.get("output_tokens_actual")
    return (
        input_tokens if isinstance(input_tokens, int) and input_tokens >= 0 else input_tokens_estimate,
        output_tokens if isinstance(output_tokens, int) and output_tokens >= 0 else 0,
    )


def run() -> None:
    args = _args()
    preflight = preflight_headline_run(args.protocol)
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
        for arm_id, model in _ordered_arm_models(models):
            router = ProviderRouter(provider="groq", mode="research", groq_client=GroqClient(model=model))
            for task in tasks:
                prompt_id, prompt = render_llm_prompt(arm_id, task)
                key = (arm_id, model, task["case_id"], prompt_id)
                if key in cache:
                    continue
                input_tokens = max(1, ceil(len(prompt) / 4))
                started = time.perf_counter()
                allowed = False
                reason = None
                for throttle_check in range(MAX_CLIENT_THROTTLE_CHECKS):
                    allowed, reason = ledger.allow(input_tokens, MAX_TOKENS)
                    if allowed:
                        break
                    if throttle_check == MAX_CLIENT_THROTTLE_CHECKS - 1:
                        break
                    time.sleep(max(0.0, float(ledger.wait_time(input_tokens, MAX_TOKENS))))
                if not allowed:
                    latency_ms = (time.perf_counter() - started) * 1000
                    token_usage = {
                        "input_tokens_estimate": input_tokens,
                        "input_tokens_actual": None,
                        "output_tokens_actual": None,
                        "total_tokens_actual": None,
                    }
                    _append(
                        output,
                        raw_writer,
                        arm_id,
                        model,
                        task,
                        prompt_id,
                        prompt,
                        None,
                        "groq",
                        latency_ms,
                        "provider_failure",
                        "client_throttled",
                        f"client rate limit remained blocked after {MAX_CLIENT_THROTTLE_CHECKS} checks: {reason}",
                        None,
                        token_usage,
                    )
                    counts["client_throttled"] = counts.get("client_throttled", 0) + 1
                    continue

                invocation = router.generate_json(prompt, model=model, temperature=0.0, max_tokens=MAX_TOKENS)
                latency_ms = (time.perf_counter() - started) * 1000
                raw_response = json.dumps(invocation.payload, ensure_ascii=True, sort_keys=True) if invocation.payload is not None else None
                token_usage = _token_usage(input_tokens, invocation)
                ledger_input_tokens, ledger_output_tokens = _ledger_tokens(token_usage, input_tokens)
                if invocation.payload is None:
                    kind = _failure_kind(invocation)
                    _append(
                        output,
                        raw_writer,
                        arm_id,
                        model,
                        task,
                        prompt_id,
                        prompt,
                        None,
                        invocation.provider,
                        latency_ms,
                        "provider_failure",
                        kind,
                        invocation.error,
                        raw_response,
                        token_usage,
                        getattr(invocation, "provider_error_body", None),
                    )
                    ledger.record(arm_id=arm_id, model=model, case_id=task["case_id"], input_tokens=ledger_input_tokens, output_tokens=ledger_output_tokens, outcome=kind)
                    counts[kind] = counts.get(kind, 0) + 1
                else:
                    try:
                        parser = parse_legacy_llm_payload if arm_id == "llm_old_new_direct_v3_legacy" else parse_llm_payload
                        prediction = parser(invocation.payload, task)
                    except ValueError as exc:
                        _append(output, raw_writer, arm_id, model, task, prompt_id, prompt, None, invocation.provider, latency_ms, "parse_failure", "parse_failure", str(exc), raw_response, token_usage)
                        ledger.record(arm_id=arm_id, model=model, case_id=task["case_id"], input_tokens=ledger_input_tokens, output_tokens=ledger_output_tokens, outcome="parse_failure")
                        counts["parse_failure"] = counts.get("parse_failure", 0) + 1
                    else:
                        _append(output, raw_writer, arm_id, model, task, prompt_id, prompt, prediction, invocation.provider, latency_ms, "success", None, None, raw_response, token_usage)
                        ledger.record(arm_id=arm_id, model=model, case_id=task["case_id"], input_tokens=ledger_input_tokens, output_tokens=ledger_output_tokens, outcome="success")
                        counts["success"] = counts.get("success", 0) + 1
                cache.add(key)
    finally:
        ledger.close()
    print(json.dumps({"models": models, "arms": ARM_IDS, "tasks": len(tasks), "preflight_only": args.preflight_only, "run_order_seed": RUN_ORDER_SEED, "execution_order": _ordered_arm_models(models), "max_tokens": MAX_TOKENS, "counts": counts, "output": str(output), "raw": str(raw_path), "preflight": preflight}, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    run()
