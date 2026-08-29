"""Phase 8.1 collection -- one sequential, resumable, cost-capped signature run.

Old-side and new-side signatures are collected in separate requests that never
see each other's input. New-side signatures are keyed by contract, not by case,
so one contract is abstracted once per model however many cases show it.

Re-uses Gate 07's provider router, rate ledger, cost budget, and append-only raw
writer unchanged.
"""

from __future__ import annotations

import argparse
import json
from math import ceil
from pathlib import Path
import time
from typing import Any

from dotenv import load_dotenv

from rag.generation.groq_client import GroqClient
from rag.generation.provider_router import ProviderRouter
from research.gate07.baselines.models import RawOutputRecord
from research.gate07.runner.artifacts import RawArtifactWriter
from research.gate07.runner.llm import CostBudget
from research.gate07.runner.rate_ledger import RateLimitLedger, limits_from_environment
from research.gate08.harness import load_tasks
from research.gate08.method.prompts import NEW_SIDE_PROMPT, OLD_SIDE_PROMPTS
from research.gate08.method.signature import (
    SignatureParseError,
    parse_signature,
    precondition_targets,
    render_new_signature_prompt,
    render_old_signature_prompt,
    schema_fields,
)
from research.gate08.protocol import preflight_gate08_run


DEFAULT_MODELS = ("openai/gpt-oss-120b", "openai/gpt-oss-20b")
OLD_VARIANTS = ("full", "no_history", "task_only")
MAX_TOKENS = 900
COST_CAP_USD = 1.20
MAX_THROTTLE_CHECKS = 5
DAILY_RATE_LIMIT_REASONS = frozenset({"pool_rpd", "pool_tpd", "org_rpd", "org_tpd"})


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--request-ledger", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS))
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args()


def _load_cache(path: Path) -> set[tuple[str, ...]]:
    if not path.exists():
        return set()
    cache: set[tuple[str, ...]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("outcome") == "success":
            cache.add(_key(row))
    return cache


def _key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row.get("kind")),
        str(row.get("variant")),
        str(row.get("model")),
        str(row.get("case_id")),
        str(row.get("tool_name")),
        str(row.get("schema_hash")),
    )


def _old_units(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for task in tasks:
        contracts = {contract["name"]: contract for contract in task.get("old_contracts", [])}
        for tool_name in task.get("old_tool_names", []):
            contract = contracts.get(tool_name)
            units.append(
                {
                    "kind": "old",
                    "case_id": task["case_id"],
                    "tool_name": tool_name,
                    "schema_hash": contract.get("schema_hash") if contract else None,
                    "task": task,
                    "contract": contract,
                }
            )
    return units


def _new_units(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for task in tasks:
        for contract in task.get("new_contracts", []):
            key = (contract["name"], contract["schema_hash"])
            seen.setdefault(
                key,
                {
                    "kind": "new",
                    "case_id": None,
                    "tool_name": contract["name"],
                    "schema_hash": contract["schema_hash"],
                    "contract": contract,
                },
            )
    return [seen[key] for key in sorted(seen)]


def _render(unit: dict[str, Any], variant: str) -> tuple[str, str]:
    if unit["kind"] == "new":
        return render_new_signature_prompt(unit["contract"])
    task = unit["task"]
    scoped = dict(task)
    if unit["contract"] is not None:
        scoped["old_contracts"] = [unit["contract"]]
    return render_old_signature_prompt(variant, scoped)


def _append(output: Path, row: dict[str, Any]) -> None:
    with output.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")


def _parse(unit: dict[str, Any], variant: str, payload: Any):
    contract = unit["contract"]
    allowed = schema_fields(contract) if contract is not None and variant != "task_only" else None
    targets = precondition_targets(contract) if contract is not None else ()
    return parse_signature(
        payload,
        side="new" if unit["kind"] == "new" else "old",
        tool_name=unit["tool_name"],
        precondition_targets=targets,
        allowed_fields=allowed,
    )


def run() -> None:
    args = _args()
    preflight = preflight_gate08_run(args.protocol)
    project_root = Path(__file__).resolve().parents[3]
    load_dotenv(project_root / ".env", override=False)

    tasks: list[dict[str, Any]] = []
    for path in args.tasks:
        tasks.extend(load_tasks(path))
    if args.preflight_only:
        tasks = tasks[:1]

    models = tuple(model.strip() for model in args.models.split(",") if model.strip())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    raw_writer = RawArtifactWriter(args.raw)
    ledger = RateLimitLedger(args.ledger, args.request_ledger, limits_from_environment())
    cache = _load_cache(output)
    budget = CostBudget(output, cap_usd=COST_CAP_USD)

    work: list[tuple[dict[str, Any], str]] = []
    for unit in _new_units(tasks):
        work.append((unit, "-"))
    for variant in OLD_VARIANTS:
        for unit in _old_units(tasks):
            work.append((unit, variant))

    counts: dict[str, int] = {}
    aborted = False
    abort_reason: str | None = None
    abort_detail: dict[str, Any] = {}
    try:
        for model in models:
            router = ProviderRouter(provider="groq", mode="research", groq_client=GroqClient(model=model))
            for unit, variant in work:
                prompt_id, prompt = _render(unit, variant if unit["kind"] == "old" else "-")
                row_stub = {
                    "kind": unit["kind"],
                    "variant": variant,
                    "model": model,
                    "case_id": unit["case_id"],
                    "tool_name": unit["tool_name"],
                    "schema_hash": unit["schema_hash"],
                }
                if _key(row_stub) in cache:
                    continue
                input_tokens = max(1, ceil(len(prompt) / 4))
                started = time.perf_counter()
                allowed = False
                reason: str | None = None
                stop_for_quota = False
                for check in range(MAX_THROTTLE_CHECKS):
                    allowed, reason = ledger.allow(input_tokens, MAX_TOKENS)
                    if allowed:
                        break
                    if reason in DAILY_RATE_LIMIT_REASONS:
                        aborted = True
                        abort_reason = "daily_quota_exhausted"
                        abort_detail = {"rate_limit_reason": reason, "model": model, **row_stub}
                        stop_for_quota = True
                        break
                    if check == MAX_THROTTLE_CHECKS - 1:
                        break
                    time.sleep(max(0.0, float(ledger.wait_time(input_tokens, MAX_TOKENS))))
                if stop_for_quota:
                    break
                token_usage: dict[str, Any] = {
                    "input_tokens_estimate": input_tokens,
                    "input_tokens_actual": None,
                    "output_tokens_actual": None,
                    "total_tokens_actual": None,
                }
                if not allowed:
                    _append(
                        output,
                        {
                            **row_stub,
                            "prompt_id": prompt_id,
                            "signature": None,
                            "outcome": "provider_failure",
                            "failure_kind": "client_throttled",
                            "error": f"client rate limit blocked after {MAX_THROTTLE_CHECKS} checks: {reason}",
                            "latency_ms": (time.perf_counter() - started) * 1000,
                            "token_usage": token_usage,
                            "cost_usd": None,
                        },
                    )
                    counts["client_throttled"] = counts.get("client_throttled", 0) + 1
                    continue

                can_spend, reservation = budget.reserve(model, input_tokens, MAX_TOKENS)
                if not can_spend:
                    aborted = True
                    abort_reason = "cost_cap"
                    abort_detail = {"spent_usd": round(budget.spent_usd, 10), **row_stub}
                    break

                invocation = router.generate_json(prompt, model=model, temperature=0.0, max_tokens=MAX_TOKENS)
                latency_ms = (time.perf_counter() - started) * 1000
                usage = getattr(invocation, "usage", None) or {}
                token_usage = {
                    "input_tokens_estimate": input_tokens,
                    "input_tokens_actual": usage.get("input_tokens_actual"),
                    "output_tokens_actual": usage.get("output_tokens_actual"),
                    "total_tokens_actual": usage.get("total_tokens_actual"),
                }
                raw_response = (
                    json.dumps(invocation.payload, ensure_ascii=True, sort_keys=True)
                    if invocation.payload is not None
                    else None
                )
                cost_usd, _complete = budget.settle(reservation, model, token_usage, billable=invocation.payload is not None)
                signature_record = None
                if invocation.payload is None:
                    outcome, failure_kind, error = "provider_failure", (invocation.failure_kind or "provider_error"), invocation.error
                else:
                    try:
                        signature = _parse(unit, variant, invocation.payload)
                    except SignatureParseError as exc:
                        outcome, failure_kind, error = "parse_failure", "parse_failure", str(exc)
                    else:
                        outcome, failure_kind, error = "success", None, None
                        signature_record = signature.to_record()
                raw_writer.append(
                    RawOutputRecord(
                        arm_id=f"gate08_signature_{unit['kind']}_{variant}",
                        model=model,
                        case_id=unit["case_id"] or unit["tool_name"],
                        prompt_id=prompt_id,
                        rendered_prompt=prompt,
                        raw_response=raw_response,
                        provider=invocation.provider,
                        latency_ms=latency_ms,
                        token_usage=token_usage,
                        outcome=outcome,
                        failure_kind=failure_kind,
                        error=error,
                        provider_error_body=getattr(invocation, "provider_error_body", None),
                        cost_usd=cost_usd,
                    )
                )
                _append(
                    output,
                    {
                        **row_stub,
                        "prompt_id": prompt_id,
                        "signature": signature_record,
                        "outcome": outcome,
                        "failure_kind": failure_kind,
                        "error": error,
                        "latency_ms": latency_ms,
                        "token_usage": token_usage,
                        "cost_usd": cost_usd,
                    },
                )
                ledger.record(
                    arm_id=f"gate08_signature_{unit['kind']}",
                    model=model,
                    case_id=unit["case_id"] or unit["tool_name"],
                    input_tokens=token_usage["input_tokens_actual"] or input_tokens,
                    output_tokens=token_usage["output_tokens_actual"] or 0,
                    outcome=outcome,
                )
                counts[outcome if outcome != "provider_failure" else (failure_kind or "provider_error")] = (
                    counts.get(outcome if outcome != "provider_failure" else (failure_kind or "provider_error"), 0) + 1
                )
                if outcome == "success":
                    cache.add(_key(row_stub))
                if budget.spent_usd >= COST_CAP_USD:
                    aborted = True
                    abort_reason = "cost_cap"
                    abort_detail = {"spent_usd": round(budget.spent_usd, 10), **row_stub}
                    break
            if aborted:
                break
    finally:
        ledger.close()

    if aborted:
        Path(str(output) + ".checkpoint.json").write_text(
            json.dumps(
                {"status": "aborted", "reason": abort_reason, "detail": abort_detail, "counts": counts, "spent_usd": round(budget.spent_usd, 10)},
                ensure_ascii=True,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "models": list(models),
                "variants": list(OLD_VARIANTS),
                "tasks": len(tasks),
                "units": len(work),
                "max_tokens": MAX_TOKENS,
                "cost_cap_usd": COST_CAP_USD,
                "spent_usd": round(budget.spent_usd, 10),
                "aborted": aborted,
                "abort_reason": abort_reason,
                "abort_detail": abort_detail,
                "counts": counts,
                "output": str(output),
                "preflight": preflight,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    run()
