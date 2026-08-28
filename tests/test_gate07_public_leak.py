"""Value-level checks for the Gate 07 method-facing public surface."""

from __future__ import annotations

from dataclasses import asdict, replace
import json
import re

import pytest

from research.gate07.dataset import build_all_cases
from research.gate07.dataset.models import FAMILY_NAMES
from research.gate07.dataset.operators import case_requests
from research.gate07.harness.method_facing import build_method_facing_task
from research.gate07.sandbox.catalog import all_lineages, build_definitions


def _serialized_task(case_or_task) -> str:
    task = case_or_task if hasattr(case_or_task, "old_contracts") else build_method_facing_task(case_or_task)
    return json.dumps(asdict(task), ensure_ascii=True, sort_keys=True, default=str)


def _token_pattern(token: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", re.IGNORECASE)


def _assert_public_surface_is_clean(rendered: str) -> None:
    forbidden = {
        "seed": {str(request.seed) for request in case_requests()},
        "family": set(FAMILY_NAMES),
        "tool_id": {definition.tool_id for version in ("v1", "v2", "v3") for definition in build_definitions(version)},
        "lineage_key": {lineage.key for lineage in all_lineages()},
        "operator_name": {
            "case_requests",
            "_derive_seed",
            "_resource_index",
            "_field_value",
            "_args_for_fields",
            "_args_for_definition",
            "_transform_args",
            "_argument_pairs",
            "new_field_for",
            "_candidate_names",
            "_task_description",
            "_run",
            "build_case",
        },
        "held_out_indicator": {"held_out", "held-out", "held out"},
    }
    leaks = [
        f"{category}:{token}"
        for category, tokens in forbidden.items()
        for token in sorted(tokens)
        if _token_pattern(token).search(rendered)
    ]
    assert not leaks, f"public surface leaked forbidden values: {leaks}"


def test_gate07_value_level_detector_passes_all_graded_and_held_out_tasks():
    for case in build_all_cases():
        _assert_public_surface_is_clean(_serialized_task(case))


def test_gate07_value_level_detector_rejects_a_deliberate_seed_leak():
    case = build_all_cases()[0]
    task = build_method_facing_task(case)
    leaked_task = replace(task, task_description=f"{task.task_description} {case.seed}")
    with pytest.raises(AssertionError):
        _assert_public_surface_is_clean(_serialized_task(leaked_task))
