"""Reproducible Gate 07 v3 metric report assembly."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import random
from typing import Any, Iterable

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.dataset import build_all_cases
from research.gate07.dataset.models import FAMILY_NAMES
from research.gate07.harness.serialization import task_record
from research.gate07.metrics.execution import evaluate_first_attempt
from research.gate07.metrics.scoring import CaseMetric, score_prediction
from research.gate07.oracle import get_ground_truth


METRIC_FIELDS = {
    "tool_alignment_at_1": "tool_alignment_at_1",
    "tool_alignment_at_3": "tool_alignment_at_3",
    "tool_alignment_at_5": "tool_alignment_at_5",
    "argument_mapping_precision": "argument_precision",
    "argument_mapping_recall": "argument_recall",
    "argument_mapping_f1": "argument_f1",
    "false_alignment_rate": "false_alignment_rate",
    "no_equivalent_accuracy": "no_equivalent_accuracy",
}

LOAD_BEARING_THRESHOLDS = {
    "tool_alignment_at_1": 0.80,
    "argument_mapping_f1": 0.75,
    "no_equivalent_accuracy": 0.80,
    "first_attempt_task_success": 0.80,
}

LLM_ARM_IDS = (
    "llm_new_schema_only",
    "llm_old_new_direct",
    "llm_old_new_history",
    "llm_reasoning",
)


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize_values(values: Iterable[float], *, seed: int, bootstrap_samples: int) -> dict[str, Any]:
    materialized = list(values)
    if not materialized:
        return {"mean": None, "ci95": None, "n": 0}
    rng = random.Random(seed)
    samples = [sum(rng.choice(materialized) for _ in materialized) / len(materialized) for _ in range(bootstrap_samples)]
    samples.sort()
    lower = samples[int(0.025 * (len(samples) - 1))]
    upper = samples[int(0.975 * (len(samples) - 1))]
    return {"mean": sum(materialized) / len(materialized), "ci95": [lower, upper], "n": len(materialized)}


def _outcome_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    failure_kinds: dict[str, int] = {}
    for row in rows:
        counts[row["outcome"]] = counts.get(row["outcome"], 0) + 1
        if row.get("failure_kind"):
            kind = row["failure_kind"]
            failure_kinds[kind] = failure_kinds.get(kind, 0) + 1
    return {"records": len(rows), "outcomes": counts, "failure_kinds": failure_kinds}


def _score_successes(
    rows: list[dict[str, Any]],
    cases: dict[str, Any],
    task_records: dict[str, dict[str, Any]],
    capability: EvaluatorCapability,
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for row in rows:
        if row.get("outcome") != "success" or not isinstance(row.get("prediction"), dict):
            continue
        case = cases[row["case_id"]]
        prediction = row["prediction"]
        metric = score_prediction(prediction, get_ground_truth(case.case_id, capability))
        execution = evaluate_first_attempt(case, task_records[case.case_id], prediction, capability)
        scored.append({"row": row, "metric": metric, "first_attempt": execution})
    return scored


def _family_metrics(scored: list[dict[str, Any]], *, seed: int, bootstrap_samples: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for metric_name, field_name in METRIC_FIELDS.items():
        result[metric_name] = summarize_values(
            (getattr(item["metric"], field_name) for item in scored if getattr(item["metric"], field_name) is not None),
            seed=seed,
            bootstrap_samples=bootstrap_samples,
        )
        seed += 1
    result["first_attempt_task_success"] = summarize_values(
        (float(item["first_attempt"].outcome == "succeeded") for item in scored),
        seed=seed,
        bootstrap_samples=bootstrap_samples,
    )
    return result


def build_arm_report(
    arm_id: str,
    model: str,
    rows: list[dict[str, Any]],
    cases: dict[str, Any],
    task_records: dict[str, dict[str, Any]],
    capability: EvaluatorCapability,
    *,
    bootstrap_samples: int,
) -> dict[str, Any]:
    scored = _score_successes(rows, cases, task_records, capability)
    families: dict[str, Any] = {}
    for index, family in enumerate(FAMILY_NAMES):
        family_scored = [item for item in scored if item["metric"].family == family]
        families[family] = _family_metrics(family_scored, seed=20260827 + index * 100, bootstrap_samples=bootstrap_samples)
    overall = _family_metrics(scored, seed=20260999, bootstrap_samples=bootstrap_samples)
    return {
        "arm_id": arm_id,
        "model": model,
        "outcomes": _outcome_counts(rows),
        "evaluable_success_records": len(scored),
        "families": families,
        "overall": overall,
        "case_metrics": [
            {**asdict(item["metric"]), "first_attempt_outcome": item["first_attempt"].outcome}
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
        result["metrics"][metric_name] = summarize_values(deltas, seed=20262000 + index, bootstrap_samples=bootstrap_samples)
    first_deltas = [
        float(history_by_case[case_id]["first_attempt"].outcome == "succeeded")
        - float(direct_by_case[case_id]["first_attempt"].outcome == "succeeded")
        for case_id in common
    ]
    result["metrics"]["first_attempt_task_success"] = summarize_values(first_deltas, seed=20262099, bootstrap_samples=bootstrap_samples)
    return result


def _failure_region(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for family in FAMILY_NAMES:
        arm_rows = [{"arm_id": report["arm_id"], "model": report["model"], **report["families"][family]} for report in reports]
        survives: dict[str, bool | None] = {}
        for metric_name, threshold in LOAD_BEARING_THRESHOLDS.items():
            values = [row[metric_name] for row in arm_rows if row[metric_name]["n"]]
            survives[metric_name] = (
                all(row[metric_name]["n"] for row in arm_rows)
                and bool(values)
                and all(value["mean"] < threshold for value in values)
            ) if arm_rows else None
        table.append({"family": family, "arms": arm_rows, "survives_all_baselines": survives})
    return table


def build_report(
    protocol_path: str | Path,
    offline_paths: dict[str, str | Path],
    llm_path: str | Path,
    *,
    bootstrap_samples: int = 2000,
) -> dict[str, Any]:
    protocol = json.loads(Path(protocol_path).read_text(encoding="utf-8"))
    cases = {case.case_id: case for case in build_all_cases() if not case.held_out}
    task_records = {case_id: task_record(case) for case_id, case in cases.items()}
    capability = EvaluatorCapability()
    reports: list[dict[str, Any]] = []
    for arm_id, path in offline_paths.items():
        rows = [
            {**row, "outcome": row.get("outcome", "success"), "failure_kind": row.get("failure_kind")}
            for row in load_jsonl(path)
            if row.get("arm_id") == arm_id
        ]
        model = rows[0].get("model", "deterministic_offline") if rows else "deterministic_offline"
        reports.append(build_arm_report(arm_id, model, rows, cases, task_records, capability, bootstrap_samples=bootstrap_samples))
    llm_rows = load_jsonl(llm_path)
    for arm_id in LLM_ARM_IDS:
        for model in protocol["models"]["llm_ids"]:
            rows = [row for row in llm_rows if row.get("arm_id") == arm_id and row.get("model") == model]
            reports.append(build_arm_report(arm_id, model, rows, cases, task_records, capability, bootstrap_samples=bootstrap_samples))

    history_ablation = {}
    for model in protocol["models"]["llm_ids"]:
        direct_rows = [row for row in llm_rows if row.get("arm_id") == "llm_old_new_direct" and row.get("model") == model and row.get("outcome") == "success"]
        history_rows = [row for row in llm_rows if row.get("arm_id") == "llm_old_new_history" and row.get("model") == model and row.get("outcome") == "success"]
        history_ablation[model] = _paired_delta(
            _score_successes(direct_rows, cases, task_records, capability),
            _score_successes(history_rows, cases, task_records, capability),
            bootstrap_samples=bootstrap_samples,
        )
    return {
        "schema": "gate07.metrics.v3",
        "protocol_path": str(protocol_path).replace("\\", "/"),
        "protocol_freeze_commit": protocol["git_head_at_freeze"],
        "dataset_digests": protocol["dataset"],
        "graded_case_count": len(cases),
        "held_out_cases_run": 0,
        "bootstrap_samples": bootstrap_samples,
        "arms": reports,
        "history_ablation_direct_vs_history": history_ablation,
        "failure_region": _failure_region(reports),
        "exclusion_policy": protocol["exclusions"],
        "decision_thresholds": protocol["decision_thresholds"],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--offline-lexical", required=True)
    parser.add_argument("--offline-embedding", required=True)
    parser.add_argument("--offline-cross-encoder", required=True)
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
    )
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(target), "arms": len(report["arms"]), "graded_case_count": report["graded_case_count"]}, sort_keys=True))


if __name__ == "__main__":
    main()
