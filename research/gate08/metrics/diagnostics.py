"""Evaluator-lane diagnostics for reading a Gate 08 number honestly.

`oracle_reachability` answers one question the Gate 08 comparison cannot be read
without: how many of the frozen ground-truth argument pairs name a field that
does not exist in the correct new contract. Such a pair cannot be produced by
any method that only emits fields it was shown, so it caps recall -- and
therefore Argument Mapping F1 -- for every arm on both sides of the comparison.

This is a post-hoc measurement of the dataset, not a filter. Nothing is dropped
from any numerator or denominator because of it.
"""

from __future__ import annotations

from typing import Any

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.harness.serialization import task_record
from research.gate07.oracle.ground_truth import get_ground_truth
from research.gate08.harness import EVAL_FAMILIES, eval_cases


def oracle_reachability() -> dict[str, Any]:
    capability = EvaluatorCapability()
    per_family: dict[str, dict[str, Any]] = {family: {"pairs": 0, "unreachable_pairs": 0} for family in EVAL_FAMILIES}
    for case in eval_cases():
        task = task_record(case)
        fields = {
            contract["name"]: set((contract.get("input_schema", {}) or {}).get("properties", {}) or {})
            for contract in task["new_contracts"]
        }
        truth = get_ground_truth(case.case_id, capability)
        bucket = per_family[case.family]
        for _old_tool, _old_arg, new_tool, new_arg in truth.argument_pairs:
            bucket["pairs"] += 1
            if new_arg not in fields.get(new_tool, set()):
                bucket["unreachable_pairs"] += 1
    for family, bucket in per_family.items():
        pairs = bucket["pairs"]
        bucket["unreachable_share"] = round(bucket["unreachable_pairs"] / pairs, 10) if pairs else None
        bucket["max_attainable_recall"] = round(1.0 - bucket["unreachable_pairs"] / pairs, 10) if pairs else None
    return {
        "definition": (
            "A ground-truth argument pair is unreachable when its new_arg is not a field of the "
            "new contract the method is shown. No arm can emit it without inventing a field name."
        ),
        "families": per_family,
    }


__all__ = ["oracle_reachability"]
