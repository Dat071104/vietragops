"""Reproducible Gate 19-C analysis over frozen Gate 07/08/19 artifacts.

This module is intentionally offline.  It reads frozen JSON/JSONL artifacts,
does not call a provider, and writes only the caller-selected output path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any


CASE_IDS = (
    "G07-G-0127",
    "G07-G-0130",
    "G07-G-0133",
    "G07-G-0136",
    "G07-G-0139",
)

Z95 = NormalDist().inv_cdf(0.975)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _target_section_refs(root: Path) -> dict[str, str]:
    records = _load(root / "research/gate07/dataset/frozen_manifest.json")
    targets: dict[str, str] = {}
    for record in records:
        case_id = record.get("case_id")
        if case_id not in CASE_IDS:
            continue
        for receipt in record.get("execution_receipts", []):
            if receipt.get("role") != "new_correct":
                continue
            value = (receipt.get("input") or {}).get("section_ref")
            if value is not None:
                targets[case_id] = str(value)
    missing = sorted(set(CASE_IDS) - set(targets))
    if missing:
        raise ValueError(f"missing frozen section_ref targets: {missing}")
    return targets


def _section_observation(row: dict[str, Any]) -> dict[str, Any]:
    literals: list[dict[str, Any]] = []
    for item in row.get("constructed_argument_values") or []:
        arguments = item.get("arguments") if isinstance(item, dict) else None
        if isinstance(arguments, dict) and "section_ref" in arguments:
            literals.append(
                {
                    "new_tool": item.get("new_tool"),
                    "value": arguments["section_ref"],
                }
            )
    joins = [
        {
            "delimiter": item.get("delimiter"),
            "order": item.get("order"),
        }
        for item in row.get("value_transforms") or []
        if isinstance(item, dict) and item.get("kind") == "join"
    ]
    if literals:
        return {"kind": "constructed_literal", "literals": literals, "joins": []}
    if joins:
        return {"kind": "join_transform", "literals": [], "joins": joins}
    return {"kind": "not_constructed", "literals": [], "joins": []}


def _score_record(metric_row: dict[str, Any] | None) -> dict[str, Any]:
    if metric_row is None:
        return {"score": None, "outcome": None, "argument_f1": None, "argument_recall": None}
    outcome = metric_row.get("first_attempt_outcome")
    score = None if outcome is None else int(outcome == "succeeded")
    return {
        "score": score,
        "outcome": outcome,
        "argument_f1": metric_row.get("argument_f1"),
        "argument_recall": metric_row.get("argument_recall"),
    }


def c1_extract(root: Path) -> dict[str, Any]:
    convention = _load(root / "gates/results/GATE_19_FROZEN_CONVENTION_AUDIT.json")
    metrics = _load(root / "gates/artifacts/gate07/v4/metrics_v4_1_run1.json")
    targets = _target_section_refs(root)
    metric_rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    for arm in metrics["arms"]:
        arm_id = arm.get("arm_id")
        model = arm.get("model")
        for row in arm.get("case_metrics", []):
            metric_rows[(arm_id, model, row.get("case_id"))] = row

    rows: list[dict[str, Any]] = []
    for row in convention["rows"]:
        if row.get("case_id") not in CASE_IDS:
            continue
        metric_model = row.get("model")
        if row.get("arm_id") in {
            "lexical_name",
            "lexical_serialized",
            "embed_name_desc",
            "embed_serialized_schema",
            "cross_encoder",
        }:
            metric_model = "deterministic_offline"
        elif row.get("arm_id") in {"positional_prior", "random_choice"}:
            metric_model = "deterministic_control"
        key = (row.get("arm_id"), metric_model, row.get("case_id"))
        rows.append(
            {
                "case_id": row.get("case_id"),
                "arm_id": row.get("arm_id"),
                "model": row.get("model"),
                "source": row.get("source"),
                "target_section_ref": targets[row["case_id"]],
                "section_observation": _section_observation(row),
                "join_classification": row.get("join_classification"),
                "score": _score_record(metric_rows.get(key)),
            }
        )
    rows.sort(key=lambda item: (item["arm_id"], item["model"], item["case_id"]))
    return {
        "cases": [
            {"case_id": case_id, "target_section_ref": targets[case_id]}
            for case_id in CASE_IDS
        ],
        "row_count": len(rows),
        "literal_join_count": sum(
            row["join_classification"] == "sandbox_join" for row in rows
        ),
        "different_separator_count": sum(
            row["join_classification"] == "different_separator" for row in rows
        ),
        "no_join_count": sum(row["join_classification"] == "no_join" for row in rows),
        "score_success_count": sum(row["score"]["score"] == 1 for row in rows),
        "rows": rows,
    }


def _case_complete(
    family: str,
    case_id: str,
    pair_items: list[dict[str, Any]],
    required_items: list[dict[str, Any]],
) -> bool:
    pair_rows = [row for row in pair_items if row.get("case_id") == case_id]
    required_rows = [row for row in required_items if row.get("case_id") == case_id]
    return all(row.get("status") == "REACHABLE" for row in pair_rows + required_rows)


def c2_surface(root: Path) -> dict[str, Any]:
    pair_audit = _load(root / "gates/results/GATE_19_AUDIT.json")
    required_audit = _load(root / "gates/results/GATE_19_REQUIRED_FIELD_AUDIT.json")
    protocol = _load(root / "gates/baselines/GATE_07_PROTOCOL_V4.json")
    pair_items = pair_audit["items"]
    required_items = required_audit["items"]
    pair_by_family: dict[str, list[dict[str, Any]]] = {}
    required_by_family: dict[str, list[dict[str, Any]]] = {}
    for item in pair_items:
        pair_by_family.setdefault(item.get("family"), []).append(item)
    for item in required_items:
        required_by_family.setdefault(item.get("family"), []).append(item)

    rows: list[dict[str, Any]] = []
    for family, case_count in sorted(protocol["dataset"]["family_counts"].items()):
        pair_rows = pair_by_family.get(family, [])
        required_rows = required_by_family.get(family, [])
        statuses = {
            "REACHABLE": sum(row.get("status") == "REACHABLE" for row in pair_rows),
            "UNREACHABLE-TARGET-ABSENT": sum(
                row.get("status") == "UNREACHABLE-TARGET-ABSENT" for row in pair_rows
            ),
            "UNREACHABLE-CONVENTION-UNOBSERVABLE": sum(
                row.get("status") == "UNREACHABLE-CONVENTION-UNOBSERVABLE"
                for row in pair_rows
            ),
        }
        pair_count = len(pair_rows)
        cases = sorted({row.get("case_id") for row in pair_rows if row.get("case_id")})
        complete_cases = None
        if pair_rows:
            complete_cases = sum(
                _case_complete(family, case_id, pair_rows, required_rows)
                for case_id in cases
            )
        rows.append(
            {
                "family": family,
                "total_graded_cases": case_count,
                "total_pairs": pair_count,
                "reachable": statuses["REACHABLE"],
                "unreachable_target_absent": statuses["UNREACHABLE-TARGET-ABSENT"],
                "unreachable_convention_unobservable": statuses[
                    "UNREACHABLE-CONVENTION-UNOBSERVABLE"
                ],
                "retained_after_repair": statuses["REACHABLE"],
                "pair_loss_percent": (
                    100.0 * (pair_count - statuses["REACHABLE"]) / pair_count
                    if pair_count
                    else None
                ),
                "required_field_unreachable": sum(
                    row.get("status") != "REACHABLE" for row in required_rows
                ),
                "required_field_reachable": sum(
                    row.get("status") == "REACHABLE" for row in required_rows
                ),
                "strict_complete_call_cases": complete_cases,
                "strict_case_loss_percent": (
                    100.0 * (case_count - complete_cases) / case_count
                    if complete_cases is not None and case_count
                    else None
                ),
            }
        )

    defaults: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for item in required_items:
        key = (
            item.get("family"),
            item.get("new_tool"),
            item.get("new_arg"),
            json.dumps(item.get("target_value"), ensure_ascii=True, sort_keys=True),
        )
        grouped.setdefault(key, []).append(item)
    for (family, tool, field, target), items in sorted(grouped.items()):
        defaults.append(
            {
                "family": family,
                "new_tool": tool,
                "new_arg": field,
                "target_value": json.loads(target),
                "case_count": len(items),
                "status_counts": {
                    "REACHABLE": sum(item.get("status") == "REACHABLE" for item in items),
                    "UNREACHABLE": sum(item.get("status") != "REACHABLE" for item in items),
                },
                "classification": (
                    "derivable_from_declared_information_rights"
                    if all(item.get("status") == "REACHABLE" for item in items)
                    else "item_unreachable_under_declared_information_rights"
                ),
                "case_ids": sorted(item.get("case_id") for item in items),
            }
        )
    return {
        "families": rows,
        "required_field_defaults": defaults,
        "pair_item_count": len(pair_items),
        "required_field_item_count": len(required_items),
    }


def wilson_interval(p: float, n: int) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("n must be positive")
    z2 = Z95 * Z95
    denominator = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denominator
    half = Z95 * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def two_arm_power(n: int, p_bar: float, difference: float) -> float:
    """Two-sided normal-approximation power for equal-size independent arms."""

    p_low = p_bar - difference / 2.0
    p_high = p_bar + difference / 2.0
    if not (0.0 <= p_low <= p_high <= 1.0):
        return float("nan")
    if p_bar in {0.0, 1.0}:
        return 1.0 if difference else 0.0
    se_null = math.sqrt(2.0 * p_bar * (1.0 - p_bar) / n)
    se_alt = math.sqrt(
        (p_low * (1.0 - p_low) + p_high * (1.0 - p_high)) / n
    )
    mu = difference / se_null
    scale = se_alt / se_null
    return NormalDist().cdf((-Z95 - mu) / scale) + 1.0 - NormalDist().cdf(
        (Z95 - mu) / scale
    )


def minimum_detectable_difference(n: int, p_bar: float, target_power: float = 0.8) -> float:
    upper = min(2.0 * p_bar, 2.0 * (1.0 - p_bar), 1.0)
    low = 0.0
    for _ in range(100):
        mid = (low + upper) / 2.0
        if two_arm_power(n, p_bar, mid) >= target_power:
            upper = mid
        else:
            low = mid
    return upper


def required_n(p_bar: float, difference: float = 0.2, target_power: float = 0.8) -> int:
    for n in range(1, 100_001):
        if two_arm_power(n, p_bar, difference) >= target_power:
            return n
    raise ValueError("required n exceeds search limit")


def _first_attempt_stats(metrics: dict[str, Any], family: str, arm: str, model: str) -> dict[str, Any] | None:
    for record in metrics["arms"]:
        if record.get("arm_id") != arm or record.get("model") != model:
            continue
        rows = [
            row
            for row in record.get("case_metrics", [])
            if row.get("family") == family and row.get("first_attempt_outcome") is not None
        ]
        if not rows:
            return None
        successes = sum(row.get("first_attempt_outcome") == "succeeded" for row in rows)
        return {"arm_id": arm, "model": model, "successes": successes, "n": len(rows), "rate": successes / len(rows)}
    return None


def _best_stats(metrics: dict[str, Any], family: str, predicate) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for record in metrics["arms"]:
        stats = _first_attempt_stats(metrics, family, record.get("arm_id"), record.get("model"))
        if stats is not None and predicate(record):
            candidates.append(stats)
    if not candidates:
        raise ValueError(f"no first-attempt baseline for {family}")
    return max(candidates, key=lambda item: (item["rate"], item["n"], item["arm_id"], item["model"]))


def c3_power(root: Path, surfaces: dict[str, Any]) -> dict[str, Any]:
    metrics = _load(root / "gates/artifacts/gate07/v4/metrics_v4_1_run1.json")
    # Every deterministic offline/control arm is 0.0 on both retained families;
    # use the named lexical arm as a stable representative of that tied maximum.
    offline = _first_attempt_stats(
        metrics, "argument_split", "lexical_name", "deterministic_offline"
    )
    direct_split = _best_stats(
        metrics,
        "argument_split",
        lambda record: str(record.get("model", "")).startswith("openai/")
        and record.get("arm_id") != "llm_new_schema_only",
    )
    offline_repl = _first_attempt_stats(
        metrics, "tool_replacement", "lexical_name", "deterministic_offline"
    )
    direct_repl = _best_stats(
        metrics,
        "tool_replacement",
        lambda record: str(record.get("model", "")).startswith("openai/")
        and record.get("arm_id") != "llm_new_schema_only",
    )
    if offline is None or offline_repl is None:
        raise ValueError("lexical offline anchor is not evaluable")
    anchors = {
        "argument_split": {"direct": direct_split, "offline": offline},
        "tool_replacement": {"direct": direct_repl, "offline": offline_repl},
    }
    p_bar_by_family = {
        family: (pair["direct"]["rate"] + pair["offline"]["rate"]) / 2.0
        for family, pair in anchors.items()
    }
    retained = {
        row["family"]: row["retained_after_repair"]
        for row in surfaces["families"]
        if row["family"] in {"argument_split", "tool_replacement"}
    }
    pooled_p = (
        retained["argument_split"] * p_bar_by_family["argument_split"]
        + retained["tool_replacement"] * p_bar_by_family["tool_replacement"]
    ) / (retained["argument_split"] + retained["tool_replacement"])
    p_bar_by_family["pooled_retained"] = pooled_p
    retained["pooled_retained"] = retained["argument_split"] + retained["tool_replacement"]

    rows: list[dict[str, Any]] = []
    for family in ("argument_split", "tool_replacement", "pooled_retained"):
        n = retained[family]
        p_bar = p_bar_by_family[family]
        d = 0.2
        lower, upper = wilson_interval(p_bar, n)
        rows.append(
            {
                "surface": family,
                "retained_n_per_arm": n,
                "baseline_p_bar": p_bar,
                "mde_absolute_difference": minimum_detectable_difference(n, p_bar),
                "power_at_difference_0_20": two_arm_power(n, p_bar, d),
                "required_n_per_arm_for_difference_0_20": required_n(p_bar, d),
                "wilson_at_p_bar": {"lower": lower, "upper": upper, "full_width": upper - lower},
                "go_surface_pass": (
                    minimum_detectable_difference(n, p_bar) <= d
                    and required_n(p_bar, d) <= n
                ),
            }
        )
    observed_wilson: list[dict[str, Any]] = []
    for family, pair in anchors.items():
        for label, stats in pair.items():
            lower, upper = wilson_interval(stats["rate"], stats["n"])
            observed_wilson.append(
                {
                    "surface": family,
                    "arm_role": label,
                    "arm_id": stats["arm_id"],
                    "model": stats["model"],
                    "successes": stats["successes"],
                    "n": stats["n"],
                    "rate": stats["rate"],
                    "wilson_lower": lower,
                    "wilson_upper": upper,
                    "wilson_full_width": upper - lower,
                    "width_exceeds_practical_effect_0_20": upper - lower > 0.2,
                }
            )
    return {
        "method": {
            "test": "two-sided two-sample normal approximation for independent proportions, equal n per arm, no continuity correction",
            "alpha": 0.05,
            "target_power": 0.8,
            "practical_absolute_difference": 0.2,
            "baseline_anchor": "strongest applicable direct LLM versus strongest applicable offline/control arm under the frozen Gate 07 baseline rule; pooled p_bar is retained-n weighted",
            "alternative": "symmetric p_low=p_bar-d/2 and p_high=p_bar+d/2",
        },
        "anchors": anchors,
        "rows": rows,
        "observed_baseline_wilson": observed_wilson,
        "n15_width_sentence_trigger": any(
            row["surface"] == "tool_replacement" and row["wilson_full_width"] > 0.2
            for row in observed_wilson
        ),
        "decision_rule_pass": all(row["go_surface_pass"] for row in rows),
    }


def build_report(root: str | Path = ".", protocol_commit: str = "4e7a58f") -> dict[str, Any]:
    root = Path(root)
    surfaces = c2_surface(root)
    return {
        "schema": "gate19c.analysis.v1",
        "protocol": {
            "path": "gates/baselines/GATE_19C_PROTOCOL.json",
            "sha256": _sha256(root / "gates/baselines/GATE_19C_PROTOCOL.json"),
            "commit": protocol_commit,
        },
        "c1": c1_extract(root),
        "c2": surfaces,
        "c3": c3_power(root, surfaces),
        "inputs": {
            "gate19_audit_sha256": _sha256(root / "gates/results/GATE_19_AUDIT.json"),
            "gate19_required_field_audit_sha256": _sha256(root / "gates/results/GATE_19_REQUIRED_FIELD_AUDIT.json"),
            "gate19_convention_audit_sha256": _sha256(root / "gates/results/GATE_19_FROZEN_CONVENTION_AUDIT.json"),
            "gate07_v41_metrics_sha256": _sha256(root / "gates/artifacts/gate07/v4/metrics_v4_1_run1.json"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = build_report(args.repo_root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": output.as_posix(), "schema": report["schema"], "c1_rows": report["c1"]["row_count"], "c2_pair_items": report["c2"]["pair_item_count"], "decision_rule_pass": report["c3"]["decision_rule_pass"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
