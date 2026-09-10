"""Bounded Gate 19 diagnostic probe for hidden separator conventions.

This is deliberately separate from the frozen Gate 07/Gate 08 research
configuration. It records only synthetic prompts, typed outcomes, and parsed
synthetic values; it never records credentials or provider raw bodies.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - the workspace normally bundles dotenv
    load_dotenv = None

from rag.generation.openrouter_client import I2_FREE_MODEL_CATALOG, OpenRouterClient, RequestRateGovernor


MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
MAX_REQUESTS = 60
STRATUM_SIZE = 30
ALTERNATIVE_SEPARATORS = (":", "|", "/", "-", "_", ".", "~", ",")


def _prompt(left: str, right: str) -> str:
    return (
        "Return a single JSON object with exactly one key named section_ref. "
        "The old interface exposed two visible string values: "
        f"course_code={left!r} and term_id={right!r}. "
        "The new interface exposes one string field named section_ref. "
        "Construct the value using only the information in this prompt. "
        "Do not add explanations or markdown."
    )


def _classify(value: Any, left: str, right: str, gold_separator: str) -> dict[str, Any]:
    value_text = value if isinstance(value, str) else None
    exact_gold = value_text == f"{left}{gold_separator}{right}"
    emits_double_colon = isinstance(value_text, str) and "::" in value_text
    return {
        "returned_value": value_text,
        "exact_gold": exact_gold,
        "emits_double_colon": emits_double_colon,
        "shape": "valid_string" if value_text is not None else "invalid_value",
    }


def _load_owner_environment() -> None:
    if load_dotenv is not None:
        load_dotenv(dotenv_path=Path(".env"), override=False)


def _build_client() -> tuple[OpenRouterClient | None, str | None]:
    _load_owner_environment()
    client = OpenRouterClient(
        model=MODEL,
        fallback_model="",
        max_requests_per_day=MAX_REQUESTS,
        max_retries=0,
        allow_paid_models=False,
        reasoning={"effort": "none"},
        free_catalog=I2_FREE_MODEL_CATALOG,
        rate_governor=RequestRateGovernor(requests_per_minute=19, min_interval_seconds=3.2),
    )
    if not client.available():
        return None, "OPENROUTER_API_KEY was not available to the diagnostic process"
    try:
        live_catalog = client._fetch_live_catalog()
        client._validate_catalog([MODEL], live_catalog, "live diagnostic catalog")
    except Exception as exc:  # catalog failure must fail closed before generation
        return None, f"free catalog guard failed: {type(exc).__name__}"
    client._catalog_loader = lambda: live_catalog
    return client, None


def _cases() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(STRATUM_SIZE):
        left = f"L{index:03d}"
        right = f"R{index:03d}"
        rows.append(
            {
                "case_id": f"G19-P-SANDBOX-{index + 1:02d}",
                "stratum": "hidden_sandbox_convention",
                "gold_separator": "::",
                "left": left,
                "right": right,
                "prompt": _prompt(left, right),
            }
        )
    for index in range(STRATUM_SIZE):
        left = f"L{index + STRATUM_SIZE:03d}"
        right = f"R{index + STRATUM_SIZE:03d}"
        rows.append(
            {
                "case_id": f"G19-P-ARBITRARY-{index + 1:02d}",
                "stratum": "hidden_arbitrary_convention",
                "gold_separator": ALTERNATIVE_SEPARATORS[index % len(ALTERNATIVE_SEPARATORS)],
                "left": left,
                "right": right,
                "prompt": _prompt(left, right),
            }
        )
    return rows


def run(output_path: str | Path) -> dict[str, Any]:
    logging.disable(logging.CRITICAL)
    started = datetime.now(timezone.utc).isoformat()
    client, guard_error = _build_client()
    cases = _cases()
    rows: list[dict[str, Any]] = []
    if client is None:
        result = {
            "schema": "gate19.diagnostic_probe.v1",
            "status": "NOT_RUN",
            "label": "DIAGNOSTIC_PROBE_ONLY",
            "started_at_utc": started,
            "model": MODEL,
            "request_budget": MAX_REQUESTS,
            "dispatched_requests": 0,
            "guard_error": guard_error,
            "cases": cases,
            "rows": rows,
            "chance_baseline": {"reference_set_size": 9, "p_double_colon": 1 / 9},
            "ledger": None,
            "interpretation": "No generation request was made because the free-only guard did not pass.",
        }
    else:
        for index, case in enumerate(cases, start=1):
            row: dict[str, Any] = {
                "case_id": case["case_id"],
                "stratum": case["stratum"],
                "gold_separator": case["gold_separator"],
                "left": case["left"],
                "right": case["right"],
            }
            try:
                payload = client.generate_json(case["prompt"], temperature=0.0, max_tokens=128)
                row["outcome"] = "success"
                row["served_model"] = client.last_served_model
                row["parsed"] = _classify(payload.get("section_ref"), case["left"], case["right"], case["gold_separator"])
            except Exception as exc:
                row["outcome"] = "provider_or_parse_failure"
                row["error_type"] = type(exc).__name__
                row["failure_kind"] = getattr(exc, "failure_kind", None)
            rows.append(row)
            print(f"probe_progress={index}/{len(cases)}", flush=True)
        ledger = client.status()
        by_stratum: dict[str, dict[str, Any]] = {}
        for stratum in ("hidden_sandbox_convention", "hidden_arbitrary_convention"):
            subset = [row for row in rows if row["stratum"] == stratum]
            valid = [row for row in subset if row.get("outcome") == "success" and "parsed" in row]
            by_stratum[stratum] = {
                "dispatched": len(subset),
                "valid_json": len(valid),
                "double_colon_all_dispatched_rate": sum(bool(row.get("parsed", {}).get("emits_double_colon")) for row in subset) / len(subset) if subset else None,
                "double_colon_valid_json_rate": sum(bool(row.get("parsed", {}).get("emits_double_colon")) for row in valid) / len(valid) if valid else None,
                "exact_gold_valid_json_rate": sum(bool(row.get("parsed", {}).get("exact_gold")) for row in valid) / len(valid) if valid else None,
                "outcomes": dict(Counter(row.get("outcome") for row in subset)),
            }
        result = {
            "schema": "gate19.diagnostic_probe.v1",
            "status": "COMPLETE" if len(rows) == len(cases) else "INCONCLUSIVE",
            "label": "DIAGNOSTIC_PROBE_ONLY",
            "started_at_utc": started,
            "model": MODEL,
            "request_budget": MAX_REQUESTS,
            "dispatched_requests": len(rows),
            "cases": cases,
            "rows": rows,
            "chance_baseline": {"reference_set_size": 9, "p_double_colon": 1 / 9},
            "strata": by_stratum,
            "ledger": {
                "probe_local": ledger,
                "provider_daily_receipt_reference": "gates/results/GATE_18R_RESULT.md recorded 4/1000 used and 996 remaining for its observed UTC day; this probe does not claim a fresh provider account balance.",
            },
            "interpretation": "Diagnostic only; not a Gate 07 or Gate 08 result and not evidence of training-data contamination by itself.",
        }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({"status": result["status"], "dispatched_requests": result["dispatched_requests"], "model": result["model"]}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
