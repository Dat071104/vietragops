"""Phase 8.5 fitting -- thresholds from the held-out split only.

The graded cases are never read here. `retrieval_floor` is fitted against
held-out labels; `abstain_floor` is a label-free coverage quantile, so the
abstention rule cannot be tuned toward a score.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.oracle.ground_truth import get_ground_truth
from research.gate08.ablations import ALL_CONFIGS, config_by_id
from research.gate08.harness import load_tasks
from research.gate08.method.calibration import (
    ABSTAIN_COVERAGE_TARGET,
    RETRIEVAL_FLOOR_GRID,
    Thresholds,
)
from research.gate08.protocol import preflight_gate08_run
from research.gate08.runner.decide import decide_tasks
from research.gate08.runner.store import SignatureStore

PERMISSIVE = Thresholds(retrieval_floor=0.0, abstain_floor=0.0)


def _has_equivalent(case_id: str, capability: EvaluatorCapability) -> bool:
    return bool(get_ground_truth(case_id, capability).correct_new_tool_names)


def _balanced_accuracy(rows: list[tuple[float, bool]], floor: float) -> float:
    positives = [row for row in rows if row[1]]
    negatives = [row for row in rows if not row[1]]
    if not positives or not negatives:
        return 0.0
    true_positive = sum(1 for score, _ in positives if score >= floor) / len(positives)
    true_negative = sum(1 for score, _ in negatives if score < floor) / len(negatives)
    return (true_positive + true_negative) / 2


def _quantile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round(fraction * (len(ordered) - 1)))))
    return ordered[index]


def fit(
    tasks: list[dict[str, Any]],
    store: SignatureStore,
    *,
    model: str,
    arm_id: str,
) -> tuple[Thresholds, dict[str, Any]]:
    capability = EvaluatorCapability()
    config = config_by_id(arm_id)
    rows = decide_tasks(tasks, store, model=model, config=config, thresholds=PERMISSIVE, execute=False)
    usable = [row for row in rows if row["outcome"] == "success" and row["decision"]["ranked"]]
    labelled = [
        (float(row["decision"]["ranked"][0]["total"]), _has_equivalent(row["case_id"], capability))
        for row in usable
    ]
    best_floor, best_score = RETRIEVAL_FLOOR_GRID[0], -1.0
    for floor in RETRIEVAL_FLOOR_GRID:
        score = _balanced_accuracy(labelled, floor)
        if score > best_score:
            best_floor, best_score = floor, score
    retained = [row for row in usable if float(row["decision"]["ranked"][0]["total"]) >= best_floor]
    abstain_floor = _quantile([float(row["decision"]["confidence"]) for row in retained], ABSTAIN_COVERAGE_TARGET)
    diagnostics = {
        "calibration_cases": len(rows),
        "usable_cases": len(usable),
        "signature_unavailable": sum(1 for row in rows if row["outcome"] != "success"),
        "positives": sum(1 for _, label in labelled if label),
        "negatives": sum(1 for _, label in labelled if not label),
        "retrieval_floor_balanced_accuracy": round(best_score, 6),
        "retained_after_floor": len(retained),
        "abstain_coverage_target": ABSTAIN_COVERAGE_TARGET,
    }
    return Thresholds(retrieval_floor=best_floor, abstain_floor=round(abstain_floor, 10)), diagnostics


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--signatures", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--models", required=True)
    parser.add_argument("--arms", default=",".join(config.arm_id for config in ALL_CONFIGS))
    return parser.parse_args()


def main() -> None:
    args = _args()
    preflight = preflight_gate08_run(args.protocol)
    tasks = load_tasks(args.tasks)
    store = SignatureStore.load(args.signatures)
    thresholds: dict[str, Any] = {}
    diagnostics: dict[str, Any] = {}
    for model in (value.strip() for value in args.models.split(",") if value.strip()):
        for arm_id in (value.strip() for value in args.arms.split(",") if value.strip()):
            fitted, detail = fit(tasks, store, model=model, arm_id=arm_id)
            thresholds[f"{model}|{arm_id}"] = fitted.to_record()
            diagnostics[f"{model}|{arm_id}"] = detail
    payload = {
        "split": "held_out",
        "calibration_case_count": len(tasks),
        "grid": list(RETRIEVAL_FLOOR_GRID),
        "thresholds": thresholds,
        "diagnostics": diagnostics,
        "preflight": preflight,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": args.output, "thresholds": thresholds}, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
