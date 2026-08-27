"""Gate 07 evaluator capability and harness-boundary tests."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.dataset import build_all_cases
from research.gate07.harness import build_method_facing_task
from research.gate07.oracle import all_ground_truth, get_ground_truth, ground_truth_digest


def test_gate07_oracle_rejects_missing_capability():
    case_id = build_all_cases()[0].case_id
    with pytest.raises(PermissionError):
        get_ground_truth(case_id, object())  # type: ignore[arg-type]


def test_gate07_oracle_has_all_cases_and_stable_digest():
    capability = EvaluatorCapability()
    values = all_ground_truth(capability)
    assert len(values) == 216
    assert ground_truth_digest(capability) == ground_truth_digest(capability)


def test_gate07_d9_d10_truth_is_not_forced_to_one_to_one():
    capability = EvaluatorCapability()
    d9 = next(value for value in all_ground_truth(capability) if value.family == "one_old_to_multiple_new")
    d10 = next(value for value in all_ground_truth(capability) if value.family == "multiple_old_to_one_new")
    assert len(d9.correct_new_tool_names) == 2
    assert len(d10.old_tool_names) == 2
    assert len(d10.correct_new_tool_names) == 1


def test_gate07_harness_source_does_not_import_evaluator_data_module():
    source = (Path(__file__).parents[1] / "research" / "gate07" / "harness" / "method_facing.py").read_text(encoding="utf-8")
    assert "oracle" not in source.casefold()
    task = build_method_facing_task(next(case for case in build_all_cases() if case.family == "no_equivalent"))
    assert not {field.name for field in fields(task)} & {"family", "seed", "lineage_key"}
