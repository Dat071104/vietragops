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
COST_CAP_USD = 1.20
MODEL_PRICING_USD_PER_MILLION = {
    "openai/gpt-oss-120b": {"input": 0.15, "output": 0.60},
    "openai/gpt-oss-20b": {"input": 0.075, "output": 0.30},
}
DAILY_RATE_LIMIT_REASONS = frozenset({"pool_rpd", "pool_tpd", "org_rpd", "org_tpd"})


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
    cost_usd: float | None = None,
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
        cost_usd=cost_usd,
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
        "cost_usd": cost_usd,
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


def _cost_for_tokens(model: str, input_tokens: int, output_tokens: int) -> float:
    try:
        pricing = MODEL_PRICING_USD_PER_MILLION[model]
    except KeyError as exc:
        raise ValueError(f"No frozen cost pricing for model: {model}") from exc
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000


def _cost_from_usage(model: str, token_usage: dict[str, Any]) -> float | None:
    input_tokens = token_usage.get("input_tokens_actual")
    output_tokens = token_usage.get("output_tokens_actual")
    if not all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in (input_tokens, output_tokens)):
        return None
    return _cost_for_tokens(model, input_tokens, output_tokens)


class CostBudget:
    """Reserve a conservative per-request maximum and settle on provider usage."""

    def __init__(self, output: Path, cap_usd: float = COST_CAP_USD) -> None:
        self.output = output
        self.cap_usd = cap_usd
        self.spent_usd = 0.0
        self.reserved_usd = 0.0
        self._load_existing()

    def _load_existing(self) -> None:
        if not self.output.exists():
            return
        for line in self.output.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            stored_cost = row.get("cost_usd")
            if isinstance(stored_cost, (int, float)) and not isinstance(stored_cost, bool) and stored_cost >= 0:
                self.spent_usd += float(stored_cost)
                continue
            usage = row.get("token_usage") or {}
            cost = _cost_from_usage(row.get("model", ""), usage) if row.get("model") in MODEL_PRICING_USD_PER_MILLION else None
            if cost is not None:
                self.spent_usd += cost

    def reserve(self, model: str, input_tokens_estimate: int, output_tokens_max: int) -> tuple[bool, float]:
        estimate = _cost_for_tokens(model, input_tokens_estimate, output_tokens_max)
        allowed = self.spent_usd + self.reserved_usd + estimate <= self.cap_usd + 1e-9
        if allowed:
            self.reserved_usd += estimate
        return allowed, estimate

    def settle(self, reservation_usd: float, model: str, token_usage: dict[str, Any], *, billable: bool) -> tuple[float, bool]:
        self.reserved_usd = max(0.0, self.reserved_usd - reservation_usd)
        actual_cost = _cost_from_usage(model, token_usage)
        if not billable:
            cost = actual_cost or 0.0
            usage_complete = actual_cost is not None
        elif actual_cost is None:
            # A successful/parseable response without provider usage cannot be
            # safely priced; retain the reservation as a conservative charge.
            cost = reservation_usd
            usage_complete = False
        else:
            cost = actual_cost
            usage_complete = True
        self.spent_usd += cost
        return cost, usage_complete


def _write_checkpoint(path: Path, *, reason: str, detail: dict[str, Any], budget: CostBudget, counts: dict[str, int]) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "aborted",
                "reason": reason,
                "detail": detail,
                "spent_usd": round(budget.spent_usd, 10),
                "cost_cap_usd": budget.cap_usd,
                "counts": counts,
                "output": str(budget.output),
            },
            ensure_ascii=True,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
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
    budget = CostBudget(output)
    checkpoint_path = output.with_suffix(".checkpoint.json")
    counts: dict[str, int] = {}
    aborted = False
    abort_reason: str | None = None
    abort_detail: dict[str, Any] = {}
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
                daily_quota_abort = False
                for throttle_check in range(MAX_CLIENT_THROTTLE_CHECKS):
                    allowed, reason = ledger.allow(input_tokens, MAX_TOKENS)
                    if allowed:
                        break
                    if reason in DAILY_RATE_LIMIT_REASONS:
                        wait_seconds = max(0.0, float(ledger.wait_time(input_tokens, MAX_TOKENS)))
                        aborted = True
                        abort_reason = "daily_quota_exhausted"
                        abort_detail = {"rate_limit_reason": reason, "wait_seconds": wait_seconds, "model": model, "arm_id": arm_id, "case_id": task["case_id"]}
                        daily_quota_abort = True
                        break
                    if throttle_check == MAX_CLIENT_THROTTLE_CHECKS - 1:
                        break
                    time.sleep(max(0.0, float(ledger.wait_time(input_tokens, MAX_TOKENS))))
                if daily_quota_abort:
                    break
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

                can_spend, reservation_usd = budget.reserve(model, input_tokens, MAX_TOKENS)
                if not can_spend:
                    aborted = True
                    abort_reason = "cost_cap"
                    abort_detail = {
                        "model": model,
                        "arm_id": arm_id,
                        "case_id": task["case_id"],
                        "estimated_request_cost_usd": round(reservation_usd, 10),
                        "spent_usd": round(budget.spent_usd, 10),
                        "reserved_usd": round(budget.reserved_usd, 10),
                    }
                    break

                invocation = router.generate_json(prompt, model=model, temperature=0.0, max_tokens=MAX_TOKENS)
                latency_ms = (time.perf_counter() - started) * 1000
                raw_response = json.dumps(invocation.payload, ensure_ascii=True, sort_keys=True) if invocation.payload is not None else None
                token_usage = _token_usage(input_tokens, invocation)
                ledger_input_tokens, ledger_output_tokens = _ledger_tokens(token_usage, input_tokens)
                cost_usd, usage_complete = budget.settle(
                    reservation_usd,
                    model,
                    token_usage,
                    billable=invocation.payload is not None or _cost_from_usage(model, token_usage) is not None,
                )
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
                        cost_usd,
                    )
                    ledger.record(arm_id=arm_id, model=model, case_id=task["case_id"], input_tokens=ledger_input_tokens, output_tokens=ledger_output_tokens, outcome=kind)
                    counts[kind] = counts.get(kind, 0) + 1
                else:
                    try:
                        parser = parse_legacy_llm_payload if arm_id == "llm_old_new_direct_v3_legacy" else parse_llm_payload
                        prediction = parser(invocation.payload, task)
                    except ValueError as exc:
                        _append(output, raw_writer, arm_id, model, task, prompt_id, prompt, None, invocation.provider, latency_ms, "parse_failure", "parse_failure", str(exc), raw_response, token_usage, cost_usd=cost_usd)
                        ledger.record(arm_id=arm_id, model=model, case_id=task["case_id"], input_tokens=ledger_input_tokens, output_tokens=ledger_output_tokens, outcome="parse_failure")
                        counts["parse_failure"] = counts.get("parse_failure", 0) + 1
                    else:
                        _append(output, raw_writer, arm_id, model, task, prompt_id, prompt, prediction, invocation.provider, latency_ms, "success", None, None, raw_response, token_usage, cost_usd=cost_usd)
                        ledger.record(arm_id=arm_id, model=model, case_id=task["case_id"], input_tokens=ledger_input_tokens, output_tokens=ledger_output_tokens, outcome="success")
                        counts["success"] = counts.get("success", 0) + 1
                cache.add(key)
                if budget.spent_usd >= COST_CAP_USD:
                    aborted = True
                    abort_reason = "cost_cap"
                    abort_detail = {"model": model, "arm_id": arm_id, "case_id": task["case_id"], "spent_usd": round(budget.spent_usd, 10)}
                    break
            if aborted:
                break
    finally:
        ledger.close()
    if aborted:
        _write_checkpoint(checkpoint_path, reason=abort_reason or "aborted", detail=abort_detail, budget=budget, counts=counts)
    print(json.dumps({"models": models, "arms": ARM_IDS, "tasks": len(tasks), "preflight_only": args.preflight_only, "run_order_seed": RUN_ORDER_SEED, "execution_order": _ordered_arm_models(models), "max_tokens": MAX_TOKENS, "cost_cap_usd": COST_CAP_USD, "spent_usd": round(budget.spent_usd, 10), "aborted": aborted, "abort_reason": abort_reason, "abort_detail": abort_detail, "checkpoint": str(checkpoint_path) if aborted else None, "counts": counts, "output": str(output), "raw": str(raw_path), "preflight": preflight}, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    run()
