"""Gate 08 metric assembly.

Every estimator, interval, and applicability rule is imported from the frozen
Gate 07 report so that a Gate 08 number and a Gate 07 number are computed the
same way. The Gate 07 baselines are not re-run: their frozen result rows are
re-scored on the Gate 08 evaluation surface, which is a strict subset of the
surface they were collected on.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.harness.serialization import task_record
from research.gate07.metrics.report import (
    LLM_ARM_IDS,
    build_arm_report,
    latest_attempts,
    load_jsonl,
)
from research.gate08.ablations import ALL_CONFIGS, INFORMATION_RIGHTS, REUSED_ABLATION
from research.gate08.harness import CLAIM_FAMILIES, CONTROL_FAMILIES, EVAL_FAMILIES, eval_cases
from research.gate08.method.pipeline import SELECTION_CONTRACT

OFFLINE_ARMS = {
    "lexical_name": "offline_lexical",
    "lexical_serialized": "offline_lexical",
    "embed_name_desc": "offline_embedding",
    "embed_serialized_schema": "offline_embedding",
    "cross_encoder": "offline_cross_encoder",
}
CONTROL_ARMS = ("positional_prior", "random_choice")
LOWER_IS_BETTER = frozenset({"false_alignment_rate"})
COMPARED_METRICS = (
    "tool_alignment_at_1",
    "argument_mapping_f1",
    "false_alignment_rate",
    "first_attempt_task_success",
)


def _decision_rows(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for row in load_jsonl(path):
        rows.append(
            {
                "arm_id": row["arm_id"],
                "model": row["model"],
                "case_id": row["case_id"],
                "prediction": row.get("prediction"),
                "outcome": row.get("outcome", "success"),
                "failure_kind": None if row.get("outcome") == "success" else row.get("outcome"),
            }
        )
    return rows


def _best_cell(reports: list[dict[str, Any]], family: str, metric: str) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for report in reports:
        summary = report["families"].get(family, {}).get(metric)
        if not summary or summary.get("mean") is None or not summary.get("n"):
            continue
        candidate = {
            "arm_id": report["arm_id"],
            "model": report["model"],
            "mean": summary["mean"],
            "ci95": summary["ci95"],
            "n": summary["n"],
        }
        if best is None:
            best = candidate
            continue
        better = candidate["mean"] < best["mean"] if metric in LOWER_IS_BETTER else candidate["mean"] > best["mean"]
        if better:
            best = candidate
    return best


def _signature_outcomes(path: str | Path | None) -> dict[str, Any]:
    if not path or not Path(path).exists():
        return {"status": "absent"}
    counts: dict[str, int] = {}
    for row in load_jsonl(path):
        key = f"{row.get('kind')}|{row.get('variant')}|{row.get('model')}|{row.get('outcome')}"
        counts[key] = counts.get(key, 0) + 1
    totals: dict[str, int] = {}
    for key, value in counts.items():
        outcome = key.rsplit("|", 1)[1]
        totals[outcome] = totals.get(outcome, 0) + value
    return {"status": "present", "totals": totals, "by_key": counts}


def build_report(
    protocol_path: str | Path,
    decisions_path: str | Path,
    gate07_paths: dict[str, str | Path],
    *,
    thresholds_path: str | Path | None = None,
    signatures_path: str | Path | None = None,
    bootstrap_samples: int = 2000,
) -> dict[str, Any]:
    protocol = json.loads(Path(protocol_path).read_text(encoding="utf-8"))
    if protocol.get("schema") != "gate08.protocol.v1":
        raise ValueError("Gate 08 report requires a gate08.protocol.v1 protocol")
    cases = {case.case_id: case for case in eval_cases()}
    task_records = {case_id: task_record(case) for case_id, case in cases.items()}
    capability = EvaluatorCapability()
    surface = frozenset(cases)

    method_reports: list[dict[str, Any]] = []
    decision_rows = _decision_rows(decisions_path)
    models = list(protocol["provider"]["models"])
    for config in ALL_CONFIGS:
        for model in models:
            rows = [row for row in decision_rows if row["arm_id"] == config.arm_id and row["model"] == model]
            if not rows:
                continue
            method_reports.append(
                build_arm_report(
                    config.arm_id,
                    model,
                    rows,
                    cases,
                    task_records,
                    capability,
                    selection_contract=SELECTION_CONTRACT,
                    bootstrap_samples=bootstrap_samples,
                )
            )

    baseline_reports: list[dict[str, Any]] = []
    for arm_id, key in OFFLINE_ARMS.items():
        path = gate07_paths.get(key)
        if not path:
            continue
        rows = [
            {**row, "outcome": row.get("outcome", "success")}
            for row in load_jsonl(path)
            if row.get("arm_id") == arm_id and row.get("case_id") in surface
        ]
        baseline_reports.append(
            build_arm_report(arm_id, "deterministic_offline", rows, cases, task_records, capability, selection_contract="v4_forced", bootstrap_samples=bootstrap_samples)
        )
    control_path = gate07_paths.get("offline_controls")
    if control_path:
        control_rows = [row for row in load_jsonl(control_path) if row.get("case_id") in surface]
        for arm_id in CONTROL_ARMS:
            rows = [{**row, "outcome": row.get("outcome", "success")} for row in control_rows if row.get("arm_id") == arm_id]
            baseline_reports.append(
                build_arm_report(arm_id, "deterministic_control", rows, cases, task_records, capability, selection_contract="v4_control", bootstrap_samples=bootstrap_samples)
            )
    llm_path = gate07_paths.get("llm")
    if llm_path:
        llm_rows = [row for row in latest_attempts(load_jsonl(llm_path)) if row.get("case_id") in surface]
        for arm_id in LLM_ARM_IDS:
            for model in models:
                rows = [row for row in llm_rows if row.get("arm_id") == arm_id and row.get("model") == model]
                if not rows:
                    continue
                contract = "v3_legacy" if arm_id.endswith("_v3_legacy") else "v4_forced"
                baseline_reports.append(
                    build_arm_report(arm_id, model, rows, cases, task_records, capability, selection_contract=contract, bootstrap_samples=bootstrap_samples)
                )

    comparison: dict[str, Any] = {}
    for family in EVAL_FAMILIES:
        comparison[family] = {}
        for metric in COMPARED_METRICS:
            method_best = _best_cell(method_reports, family, metric)
            baseline_best = _best_cell(baseline_reports, family, metric)
            delta = None
            if method_best and baseline_best:
                raw = method_best["mean"] - baseline_best["mean"]
                delta = -raw if metric in LOWER_IS_BETTER else raw
            comparison[family][metric] = {
                "gate08_best": method_best,
                "gate07_frozen_best": baseline_best,
                "delta_in_favour_of_gate08": None if delta is None else round(delta, 10),
            }

    thresholds = json.loads(Path(thresholds_path).read_text(encoding="utf-8")) if thresholds_path else None
    return {
        "schema": "gate08.metrics.v1",
        "protocol_path": str(protocol_path).replace("\\", "/"),
        "protocol_freeze_commit": protocol["git_head_at_freeze"],
        "dataset_digests": protocol["dataset"],
        "method_interface_digest": protocol["method"]["interface_digest"],
        "evaluation_surface": {
            "claim_families": list(CLAIM_FAMILIES),
            "control_families": list(CONTROL_FAMILIES),
            "case_count": len(cases),
            "case_ids": sorted(cases),
        },
        "information_rights": INFORMATION_RIGHTS,
        "bootstrap_samples": bootstrap_samples,
        "arms": method_reports,
        "gate07_frozen_baselines_on_this_surface": baseline_reports,
        "reused_ablation": REUSED_ABLATION,
        "comparison": comparison,
        "calibration": thresholds,
        "signature_collection": _signature_outcomes(signatures_path),
        "exclusion_policy": protocol["exclusions"],
        "metric_thresholds": protocol["metrics"]["thresholds"],
    }


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--decisions", required=True)
    parser.add_argument("--gate07-llm")
    parser.add_argument("--gate07-offline-lexical")
    parser.add_argument("--gate07-offline-embedding")
    parser.add_argument("--gate07-offline-cross-encoder")
    parser.add_argument("--gate07-offline-controls")
    parser.add_argument("--thresholds")
    parser.add_argument("--signatures")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = _args()
    report = build_report(
        args.protocol,
        args.decisions,
        {
            "llm": args.gate07_llm,
            "offline_lexical": args.gate07_offline_lexical,
            "offline_embedding": args.gate07_offline_embedding,
            "offline_cross_encoder": args.gate07_offline_cross_encoder,
            "offline_controls": args.gate07_offline_controls,
        },
        thresholds_path=args.thresholds,
        signatures_path=args.signatures,
    )
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(target),
                "method_arms": len(report["arms"]),
                "baseline_arms": len(report["gate07_frozen_baselines_on_this_surface"]),
                "case_count": report["evaluation_surface"]["case_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
