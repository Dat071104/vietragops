"""Reproducible Gate 07 V4 metric report assembly."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import statistics
from typing import Any, Iterable

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.dataset import build_v4_cases
from research.gate07.dataset.models import FAMILY_NAMES
from research.gate07.harness.serialization import task_record
from research.gate07.metrics.execution import FirstAttemptResult, evaluate_first_attempt
from research.gate07.metrics.scoring import CaseMetric, _proportion_summary, _summary, score_prediction
from research.gate07.oracle import get_ground_truth


METRIC_FIELDS = {
    "tool_alignment_at_1": "tool_alignment_at_1",
    "argument_mapping_precision": "argument_precision",
    "argument_mapping_recall": "argument_recall",
    "argument_mapping_f1": "argument_f1",
    "false_alignment_rate": "false_alignment_rate",
    "no_equivalent_accuracy": "no_equivalent_accuracy",
    "abstention_rate": "abstention_rate",
}
PROPORTION_METRICS = {"tool_alignment_at_1", "no_equivalent_accuracy", "abstention_rate"}
CONTINUOUS_METRICS = {"argument_mapping_precision", "argument_mapping_recall", "argument_mapping_f1", "false_alignment_rate"}
ALL_METRICS = tuple(METRIC_FIELDS) + ("first_attempt_task_success",)
LLM_ARM_IDS = (
    "llm_new_schema_only",
    "llm_old_new_direct",
    "llm_old_new_history",
    "llm_reasoning",
    "llm_old_new_direct_v3_legacy",
)


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def latest_attempts(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve append-only retries to one latest row per logical call key."""
    latest: dict[tuple[Any, Any, Any, Any], dict[str, Any]] = {}
    for row in rows:
        key = (row.get("arm_id"), row.get("model"), row.get("case_id"), row.get("prompt_id"))
        latest[key] = row
    return list(latest.values())


def summarize_values(values: Iterable[float], *, seed: int, bootstrap_samples: int) -> dict[str, Any]:
    """Compatibility wrapper for the V4 continuous-score estimator."""
    return _summary(list(values), seed=seed, bootstrap_samples=bootstrap_samples)


def _empty_summary(status: str) -> dict[str, Any]:
    return {"mean": None, "ci95": None, "n": 0, "interval_method": status, "degenerate": False, "status": status}


def _summary_metric(values: list[float], metric_name: str, *, seed: int, bootstrap_samples: int) -> dict[str, Any]:
    if metric_name in PROPORTION_METRICS:
        result = _proportion_summary(values)
    else:
        result = _summary(values, seed=seed, bootstrap_samples=bootstrap_samples)
    result["status"] = "observed"
    return result


def _outcome_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    failure_kinds: dict[str, int] = {}
    for row in rows:
        outcome = row.get("outcome", "success")
        counts[outcome] = counts.get(outcome, 0) + 1
        if row.get("failure_kind"):
            kind = row["failure_kind"]
            failure_kinds[kind] = failure_kinds.get(kind, 0) + 1
    return {"records": len(rows), "outcomes": counts, "failure_kinds": failure_kinds}


def _metric_applicability(arm_id: str, selection_contract: str) -> dict[str, bool]:
    applicable = {metric: True for metric in ALL_METRICS}
    if arm_id == "llm_new_schema_only":
        for metric in ("argument_mapping_precision", "argument_mapping_recall", "argument_mapping_f1", "false_alignment_rate", "first_attempt_task_success"):
            applicable[metric] = False
    if selection_contract == "v3_legacy":
        applicable["first_attempt_task_success"] = False
    return applicable


def _score_successes(
    rows: list[dict[str, Any]],
    cases: dict[str, Any],
    task_records: dict[str, dict[str, Any]],
    capability: EvaluatorCapability,
    *,
    first_attempt_applicable: bool,
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for row in rows:
        if row.get("outcome") != "success" or not isinstance(row.get("prediction"), dict):
            continue
        case = cases[row["case_id"]]
        prediction = row["prediction"]
        metric = score_prediction(prediction, get_ground_truth(case.case_id, capability))
        execution: FirstAttemptResult | None = None
        if first_attempt_applicable:
            execution = evaluate_first_attempt(case, task_records[case.case_id], prediction, capability)
        scored.append({"row": row, "metric": metric, "first_attempt": execution})
    return scored


def _family_metrics(
    scored: list[dict[str, Any]],
    applicability: dict[str, bool],
    *,
    seed: int,
    bootstrap_samples: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for index, (metric_name, field_name) in enumerate(METRIC_FIELDS.items()):
        if not applicability.get(metric_name, True):
            result[metric_name] = _empty_summary("not_applicable")
            continue
        values = [getattr(item["metric"], field_name) for item in scored if getattr(item["metric"], field_name) is not None]
        result[metric_name] = _summary_metric(values, metric_name, seed=seed + index, bootstrap_samples=bootstrap_samples)
    if not applicability.get("first_attempt_task_success", True):
        result["first_attempt_task_success"] = _empty_summary("not_applicable")
    else:
        values = [float(item["first_attempt"].outcome == "succeeded") for item in scored if item["first_attempt"] is not None]
        result["first_attempt_task_success"] = _summary_metric(values, "first_attempt_task_success", seed=seed + 100, bootstrap_samples=bootstrap_samples)
    return result


def _target_count(cases: dict[str, Any], family: str, metric_name: str) -> int:
    if metric_name == "no_equivalent_accuracy":
        return sum(case.family == family and not case.new_tool_names for case in cases.values())
    return sum(case.family == family for case in cases.values())


def _imputation_sensitivity(
    scored: list[dict[str, Any]],
    cases: dict[str, Any],
    family: str,
    applicability: dict[str, bool],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for metric_name, field_name in METRIC_FIELDS.items():
        if not applicability.get(metric_name, True):
            result[metric_name] = _empty_summary("not_applicable")
            continue
        values = [getattr(item["metric"], field_name) for item in scored if getattr(item["metric"], field_name) is not None]
        target_count = _target_count(cases, family, metric_name)
        if not target_count:
            result[metric_name] = _empty_summary("not_applicable")
            continue
        excluded = max(0, target_count - len(values))
        observed_sum = sum(values)
        result[metric_name] = {
            "complete_case_mean": observed_sum / len(values) if values else None,
            "observed_n": len(values),
            "target_n": target_count,
            "excluded_n": excluded,
            "best_case_mean": (observed_sum + excluded) / target_count,
            "worst_case_mean": observed_sum / target_count,
            "status": "range_includes_excluded_records" if excluded else "complete",
        }
    if applicability.get("first_attempt_task_success", True):
        values = [float(item["first_attempt"].outcome == "succeeded") for item in scored if item["first_attempt"] is not None]
        target_count = _target_count(cases, family, "first_attempt_task_success")
        excluded = max(0, target_count - len(values))
        observed_sum = sum(values)
        result["first_attempt_task_success"] = {
            "complete_case_mean": observed_sum / len(values) if values else None,
            "observed_n": len(values),
            "target_n": target_count,
            "excluded_n": excluded,
            "best_case_mean": (observed_sum + excluded) / target_count if target_count else None,
            "worst_case_mean": observed_sum / target_count if target_count else None,
            "status": "range_includes_excluded_records" if excluded else "complete",
        }
    else:
        result["first_attempt_task_success"] = _empty_summary("not_applicable")
    return result


def build_arm_report(
    arm_id: str,
    model: str,
    rows: list[dict[str, Any]],
    cases: dict[str, Any],
    task_records: dict[str, dict[str, Any]],
    capability: EvaluatorCapability,
    *,
    selection_contract: str,
    bootstrap_samples: int,
) -> dict[str, Any]:
    applicability = _metric_applicability(arm_id, selection_contract)
    scored = _score_successes(
        rows,
        cases,
        task_records,
        capability,
        first_attempt_applicable=applicability["first_attempt_task_success"],
    )
    families: dict[str, Any] = {}
    imputation: dict[str, Any] = {}
    for index, family in enumerate(FAMILY_NAMES):
        family_scored = [item for item in scored if item["metric"].family == family]
        families[family] = _family_metrics(family_scored, applicability, seed=20260827 + index * 100, bootstrap_samples=bootstrap_samples)
        imputation[family] = _imputation_sensitivity(family_scored, cases, family, applicability)
    return {
        "arm_id": arm_id,
        "model": model,
        "selection_contract": selection_contract,
        "metric_applicability": applicability,
        "outcomes": _outcome_counts(rows),
        "evaluable_success_records": len(scored),
        "families": families,
        "imputation_sensitivity": imputation,
        "overall": _family_metrics(scored, applicability, seed=20260999, bootstrap_samples=bootstrap_samples),
        "case_metrics": [
            {
                **asdict(item["metric"]),
                "first_attempt_outcome": item["first_attempt"].outcome if item["first_attempt"] is not None else None,
            }
            for item in scored
        ],
    }


def _paired_delta(
    direct: list[dict[str, Any]],
    history: list[dict[str, Any]],
    *,
    bootstrap_samples: int,
) -> dict[str, Any]:
    direct_by_case = {item["row"]["case_id"]: item for item in direct}
    history_by_case = {item["row"]["case_id"]: item for item in history}
    common = sorted(set(direct_by_case) & set(history_by_case))
    result: dict[str, Any] = {"paired_case_count": len(common), "metrics": {}}
    for index, (metric_name, field_name) in enumerate(METRIC_FIELDS.items()):
        deltas = [
            getattr(history_by_case[case_id]["metric"], field_name) - getattr(direct_by_case[case_id]["metric"], field_name)
            for case_id in common
            if getattr(history_by_case[case_id]["metric"], field_name) is not None
            and getattr(direct_by_case[case_id]["metric"], field_name) is not None
        ]
        result["metrics"][metric_name] = _summary(deltas, seed=20262000 + index, bootstrap_samples=bootstrap_samples)
    first_deltas = [
        float(history_by_case[case_id]["first_attempt"].outcome == "succeeded")
        - float(direct_by_case[case_id]["first_attempt"].outcome == "succeeded")
        for case_id in common
        if history_by_case[case_id]["first_attempt"] is not None and direct_by_case[case_id]["first_attempt"] is not None
    ]
    result["metrics"]["first_attempt_task_success"] = _summary(first_deltas, seed=20262099, bootstrap_samples=bootstrap_samples)
    return result


def _strongest_baselines(reports: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any] | None]]:
    result: dict[str, dict[str, dict[str, Any] | None]] = {}
    for family in FAMILY_NAMES:
        result[family] = {}
        for metric_name in ALL_METRICS:
            eligible = [
                report
                for report in reports
                if report["metric_applicability"].get(metric_name, True)
                and report["families"][family][metric_name].get("n", 0)
                and report["families"][family][metric_name].get("mean") is not None
            ]
            if not eligible:
                result[family][metric_name] = None
                continue
            best = max(eligible, key=lambda report: report["families"][family][metric_name]["mean"])
            result[family][metric_name] = {
                "arm_id": best["arm_id"],
                "model": best["model"],
                "mean": best["families"][family][metric_name]["mean"],
                "ci95": best["families"][family][metric_name]["ci95"],
            }
    return result


def _failure_region(reports: list[dict[str, Any]], protocol: dict[str, Any]) -> list[dict[str, Any]]:
    thresholds = protocol["decision_thresholds"]["practically_meaningful_failure"]
    saturation = protocol["decision_thresholds"]["strong_llm_saturates"]
    strongest = _strongest_baselines(reports)
    table: list[dict[str, Any]] = []
    controls = [report for report in reports if report["selection_contract"] == "v4_control"]
    forced = [report for report in reports if report["selection_contract"] == "v4_forced"]
    for family in FAMILY_NAMES:
        metrics: dict[str, Any] = {}
        for metric_name in ("tool_alignment_at_1", "argument_mapping_f1", "no_equivalent_accuracy", "first_attempt_task_success"):
            best = strongest[family][metric_name]
            threshold = thresholds.get(f"{metric_name}_below")
            if threshold is None:
                threshold = thresholds.get(metric_name)
            saturation_bar = saturation[metric_name]
            if best is None:
                metrics[metric_name] = {"status": "not_observed", "stable": False}
                continue
            interval = best["ci95"]
            interval_ok = interval is not None and interval[1] < saturation_bar
            degenerate = any(
                report["families"][family][metric_name].get("degenerate", False)
                for report in reports
                if report["arm_id"] == best["arm_id"] and report["model"] == best["model"]
            )
            metrics[metric_name] = {
                "strongest_baseline": best,
                "below_practical_threshold": best["mean"] < threshold,
                "upper_bound_below_saturation": interval_ok,
                "degenerate_interval": degenerate,
                "stable": bool(best["mean"] < threshold and interval_ok and not degenerate),
            }
        forced_tool = [report["families"][family]["tool_alignment_at_1"]["mean"] for report in forced if report["families"][family]["tool_alignment_at_1"].get("n", 0)]
        control_tool = [report["families"][family]["tool_alignment_at_1"]["mean"] for report in controls if report["families"][family]["tool_alignment_at_1"].get("n", 0)]
        beats_controls = bool(forced_tool and control_tool and max(forced_tool) > max(control_tool))
        table.append({"family": family, "metrics": metrics, "beats_controls_on_tool_alignment_at_1": beats_controls, "strongest_baseline": strongest[family]})
    return table


def _missingness_analysis(rows: list[dict[str, Any]], cases: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for family in FAMILY_NAMES:
        family_rows = [row for row in rows if cases[row["case_id"]].family == family]
        success_tokens = [row.get("token_usage", {}).get("input_tokens_estimate") for row in family_rows if row.get("outcome") == "success"]
        excluded_tokens = [row.get("token_usage", {}).get("input_tokens_estimate") for row in family_rows if row.get("outcome") != "success"]
        provider_errors = sum(row.get("failure_kind") == "provider_error" for row in family_rows)
        excluded = len(excluded_tokens)
        result[family] = {
            "records": len(family_rows),
            "success": len(success_tokens),
            "excluded": excluded,
            "provider_error": provider_errors,
            "parse_failure": sum(row.get("failure_kind") == "parse_failure" for row in family_rows),
            "rate_limited": sum(row.get("failure_kind") == "rate_limited" for row in family_rows),
            "mean_input_tokens_success": statistics.mean(success_tokens) if success_tokens else None,
            "mean_input_tokens_excluded": statistics.mean(excluded_tokens) if excluded_tokens else None,
            "content_correlated_drop": bool(success_tokens and excluded_tokens and statistics.mean(excluded_tokens) > statistics.mean(success_tokens)),
        }
    return result


def build_report(
    protocol_path: str | Path,
    offline_paths: dict[str, str | Path],
    llm_path: str | Path,
    *,
    offline_control_path: str | Path | None = None,
    bootstrap_samples: int = 2000,
) -> dict[str, Any]:
    protocol = json.loads(Path(protocol_path).read_text(encoding="utf-8"))
    if protocol.get("schema") != "gate07.protocol.v4":
        raise ValueError("V4 report requires a gate07.protocol.v4 protocol")
    cases = {case.case_id: case for case in build_v4_cases() if not case.held_out}
    task_records = {case_id: task_record(case) for case_id, case in cases.items()}
    capability = EvaluatorCapability()
    reports: list[dict[str, Any]] = []
    for arm_id, path in offline_paths.items():
        rows = [
            {**row, "outcome": row.get("outcome", "success"), "failure_kind": row.get("failure_kind")}
            for row in load_jsonl(path)
            if row.get("arm_id") == arm_id
        ]
        reports.append(build_arm_report(arm_id, "deterministic_offline", rows, cases, task_records, capability, selection_contract="v4_forced", bootstrap_samples=bootstrap_samples))
    if offline_control_path:
        control_rows = [
            {**row, "outcome": row.get("outcome", "success"), "failure_kind": row.get("failure_kind")}
            for row in load_jsonl(offline_control_path)
        ]
        for arm_id in ("positional_prior", "random_choice"):
            rows = [row for row in control_rows if row.get("arm_id") == arm_id]
            reports.append(build_arm_report(arm_id, "deterministic_control", rows, cases, task_records, capability, selection_contract="v4_control", bootstrap_samples=bootstrap_samples))
    llm_rows = latest_attempts(load_jsonl(llm_path))
    prompt_templates = protocol["prompt_templates"]
    for arm_id in LLM_ARM_IDS:
        for model in protocol["models"]["llm_ids"]:
            rows = [row for row in llm_rows if row.get("arm_id") == arm_id and row.get("model") == model]
            reports.append(
                build_arm_report(
                    arm_id,
                    model,
                    rows,
                    cases,
                    task_records,
                    capability,
                    selection_contract=prompt_templates[arm_id]["selection_contract"],
                    bootstrap_samples=bootstrap_samples,
                )
            )
    history_ablation: dict[str, Any] = {}
    for model in protocol["models"]["llm_ids"]:
        direct_rows = [row for row in llm_rows if row.get("arm_id") == "llm_old_new_direct" and row.get("model") == model and row.get("outcome") == "success"]
        history_rows = [row for row in llm_rows if row.get("arm_id") == "llm_old_new_history" and row.get("model") == model and row.get("outcome") == "success"]
        history_ablation[model] = _paired_delta(
            _score_successes(direct_rows, cases, task_records, capability, first_attempt_applicable=True),
            _score_successes(history_rows, cases, task_records, capability, first_attempt_applicable=True),
            bootstrap_samples=bootstrap_samples,
        )
    return {
        "schema": "gate07.metrics.v4",
        "protocol_path": str(protocol_path).replace("\\", "/"),
        "protocol_freeze_commit": protocol["git_head_at_freeze"],
        "dataset_digests": protocol["dataset"],
        "graded_case_count": len(cases),
        "held_out_cases_run": 0,
        "bootstrap_samples": bootstrap_samples,
        "interval_policy": {"proportion": "wilson", "continuous": "bootstrap", "degenerate": "explicitly marked; not independently boundary-supporting"},
        "arms": reports,
        "history_ablation_direct_vs_history": history_ablation,
        "failure_region": _failure_region(reports, protocol),
        "strongest_baseline": _strongest_baselines(reports),
        "missingness_analysis": _missingness_analysis(llm_rows, cases),
        "exclusion_policy": protocol["exclusions"],
        "decision_thresholds": protocol["decision_thresholds"],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--offline-lexical", required=True)
    parser.add_argument("--offline-embedding", required=True)
    parser.add_argument("--offline-cross-encoder", required=True)
    parser.add_argument("--offline-controls")
    parser.add_argument("--llm", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    report = build_report(
        args.protocol,
        {
            "lexical_name": args.offline_lexical,
            "lexical_serialized": args.offline_lexical,
            "embed_name_desc": args.offline_embedding,
            "embed_serialized_schema": args.offline_embedding,
            "cross_encoder": args.offline_cross_encoder,
        },
        args.llm,
        offline_control_path=args.offline_controls,
    )
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(target), "arms": len(report["arms"]), "graded_case_count": report["graded_case_count"], "schema": report["schema"]}, sort_keys=True))


if __name__ == "__main__":
    main()
