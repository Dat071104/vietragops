"""Phases 8.2-8.6 -- decide, then execute once.

The decision is recorded before the adapted call is attempted, and exactly one
call is attempted per case. There is no retry and no second candidate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.dataset.generator import build_all_cases
from research.gate07.metrics.execution import evaluate_first_attempt
from research.gate08.ablations import ALL_CONFIGS, config_by_id
from research.gate08.harness import load_tasks
from research.gate08.method.calibration import Thresholds
from research.gate08.method.pipeline import MethodConfig, run_case
from research.gate08.protocol import preflight_gate08_run
from research.gate08.runner.store import (
    SignatureStore,
    literal_candidate_signatures,
    literal_old_signature,
)


def _cases_by_id() -> dict[str, Any]:
    return {case.case_id: case for case in build_all_cases()}


def _signatures(store: SignatureStore, task: dict[str, Any], model: str, config: MethodConfig):
    with_traces = config.old_variant == "full"
    if not config.use_intent_abstraction:
        return literal_old_signature(task, with_traces=with_traces), literal_candidate_signatures(task)
    old = store.old_signature(model=model, variant=config.old_variant, task=task, with_traces=with_traces)
    return old, store.candidate_signatures(model=model, task=task)


def decide_tasks(
    tasks: list[dict[str, Any]],
    store: SignatureStore,
    *,
    model: str,
    config: MethodConfig,
    thresholds: Thresholds,
    execute: bool,
) -> list[dict[str, Any]]:
    capability = EvaluatorCapability()
    cases = _cases_by_id() if execute else {}
    rows: list[dict[str, Any]] = []
    for task in tasks:
        old, candidates = _signatures(store, task, model, config)
        if old is None:
            rows.append(
                {
                    "arm_id": config.arm_id,
                    "model": model,
                    "case_id": task["case_id"],
                    "outcome": "signature_unavailable",
                    "decision": None,
                    "prediction": None,
                    "first_attempt": None,
                }
            )
            continue
        decision, prediction = run_case(task, old, candidates, thresholds, config)
        prediction = {**prediction, "case_id": task["case_id"]}
        first_attempt = None
        if execute:
            result = evaluate_first_attempt(cases[task["case_id"]], task, prediction, capability)
            first_attempt = {
                "outcome": result.outcome,
                "attempted_tool_names": list(result.attempted_tool_names),
                "attempted_inputs": list(result.attempted_inputs),
                "error": result.error,
            }
        rows.append(
            {
                "arm_id": config.arm_id,
                "model": model,
                "case_id": task["case_id"],
                "outcome": "success",
                "decision": decision.to_record(),
                "prediction": prediction,
                "first_attempt": first_attempt,
            }
        )
    return rows


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--signatures", required=True)
    parser.add_argument("--thresholds", required=True)
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
    fitted = json.loads(Path(args.thresholds).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    models = [model.strip() for model in args.models.split(",") if model.strip()]
    arms = [arm.strip() for arm in args.arms.split(",") if arm.strip()]

    counts: dict[str, int] = {}
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for model in models:
            for arm_id in arms:
                config = config_by_id(arm_id)
                entry = fitted["thresholds"].get(f"{model}|{arm_id}")
                if entry is None:
                    raise SystemExit(f"No fitted thresholds for {model}|{arm_id}")
                thresholds = Thresholds(entry["retrieval_floor"], entry["abstain_floor"])
                for row in decide_tasks(
                    tasks,
                    store,
                    model=model,
                    config=config,
                    thresholds=thresholds,
                    execute=True,
                ):
                    handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")
                    key = f"{arm_id}|{row['outcome']}"
                    counts[key] = counts.get(key, 0) + 1
    print(
        json.dumps(
            {"models": models, "arms": arms, "tasks": len(tasks), "counts": counts, "output": str(output), "preflight": preflight},
            ensure_ascii=True,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
