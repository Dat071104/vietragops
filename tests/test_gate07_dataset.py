"""Gate 07 deterministic dataset and public-boundary tests."""

from __future__ import annotations

from dataclasses import fields
import json
from pathlib import Path

from research.gate07.dataset import build_all_cases
from research.gate07.dataset.models import FAMILY_NAMES
from research.gate07.harness import MethodFacingTask, build_method_facing_task
from research.gate07.sandbox.catalog import all_lineages, build_definitions
from research.gate07.dataset.operators import _field_value, case_requests


def test_gate07_dataset_has_180_graded_and_36_held_out_cases():
    cases = build_all_cases()
    assert len(cases) == 216
    assert sum(not case.held_out for case in cases) == 180
    assert sum(case.held_out for case in cases) == 36
    assert {case.family for case in cases} == set(FAMILY_NAMES)


def test_gate07_family_balance_is_15_graded_plus_3_held_out():
    cases = build_all_cases()
    for family in FAMILY_NAMES:
        assert sum(case.family == family and not case.held_out for case in cases) == 15
        assert sum(case.family == family and case.held_out for case in cases) == 3


def test_gate07_regeneration_is_byte_stable_and_signatures_are_unique():
    first = build_all_cases()
    second = build_all_cases()
    assert [case.manifest_record() for case in first] == [case.manifest_record() for case in second]
    assert len({case.signature() for case in first}) == 216
    assert not ({case.case_id for case in first if case.held_out} & {case.case_id for case in first if not case.held_out})


def test_gate07_every_case_has_executed_receipts_and_real_candidates():
    for case in build_all_cases():
        assert case.execution_receipts
        assert all(receipt["succeeded"] is True for receipt in case.execution_receipts)
        assert len(case.candidate_new_tool_names) >= 3
        assert set(case.new_tool_names) <= set(case.candidate_new_tool_names)


def test_gate07_many_to_many_shapes_are_frozen_before_metrics():
    cases = build_all_cases()
    one_to_many = next(case for case in cases if case.family == "one_old_to_multiple_new")
    many_to_one = next(case for case in cases if case.family == "multiple_old_to_one_new")
    assert len(one_to_many.old_tool_names) == 1
    assert len(one_to_many.new_tool_names) == 2
    assert len(many_to_one.old_tool_names) == 2
    assert len(many_to_one.new_tool_names) == 1
    assert len(one_to_many.argument_pairs) >= 2
    assert len(many_to_one.argument_pairs) == 2


def test_gate07_public_task_has_no_hidden_generation_fields():
    task = build_method_facing_task(next(case for case in build_all_cases() if not case.held_out))
    assert isinstance(task, MethodFacingTask)
    names = {field.name for field in fields(task)}
    assert not names & {"family", "seed", "lineage_key", "operator_name", "tool_id"}
    assert all(not hasattr(contract, "tool_id") for contract in task.old_contracts + task.new_contracts)
    assert all(not hasattr(trace, "tool_id") for trace in task.verified_old_traces)


def test_gate07_frozen_and_public_manifests_are_redacted_as_declared():
    base = Path(__file__).parents[1] / "research" / "gate07" / "dataset"
    frozen = json.loads((base / "frozen_manifest.json").read_text(encoding="utf-8"))
    public = json.loads((base / "public_manifest.json").read_text(encoding="utf-8"))
    assert len(frozen) == 216
    assert len(public) == 180
    assert "family" in frozen[0] and "seed" in frozen[0]
    assert "family" not in public[0] and "seed" not in public[0]


def test_gate07_frozen_manifest_matches_seed_regeneration():
    path = Path(__file__).parents[1] / "research" / "gate07" / "dataset" / "frozen_manifest.json"
    frozen = json.loads(path.read_text(encoding="utf-8"))
    assert frozen == [case.manifest_record() for case in build_all_cases()]


def test_gate07_every_reachable_field_has_an_explicit_renderer():
    names = {name for lineage in all_lineages() for name, _ in lineage.old_fields + lineage.new_fields}
    names.update(name for definition in build_definitions("v3") for name in definition.input_schema["required"])
    for name in sorted(names):
        assert _field_value(name, 123456789) is not None


def test_gate07_case_seeds_are_not_arithmetic_family_labels():
    requests = case_requests()
    first_seed_by_family = [next(request.seed for request in requests if request.family_index == index) for index in range(len(FAMILY_NAMES))]
    assert first_seed_by_family != sorted(first_seed_by_family)
    for family_index in range(len(FAMILY_NAMES)):
        seeds = [request.seed for request in requests if request.family_index == family_index]
        spacings = {right - left for left, right in zip(seeds, seeds[1:])}
        assert len(spacings) > 1
