"""Proves the Phase 6.4 public/oracle boundary: a method-facing harness
never imports, holds, or can be made to return oracle content.

"Hidden" is documented (and tested) as an execution/import-access
boundary the harness enforces -- not cryptographic secrecy against a
developer with unrestricted repository access, who can always open
`research/gate0/oracle/ground_truth.py` directly. What must never happen
is the *harness* (the only thing an evaluated method is ever given)
doing so.
"""

from __future__ import annotations

import ast
import inspect

import pytest

from research.gate0 import harness as harness_package
from research.gate0.contracts import PublicToolContract
from research.gate0.drift import build_case_manifest
from research.gate0.evaluator import EvaluatorCapability
from research.gate0.harness import MethodFacingHarness
from research.gate0.oracle import get_ground_truth
from research.gate0.sandbox import SandboxStateError


def _harness_module_files():
    import research.gate0.harness.method_facing as mf

    return [inspect.getsourcefile(mf), inspect.getsourcefile(harness_package)]


def test_harness_source_never_imports_the_oracle_package():
    for path in _harness_module_files():
        source = open(path, encoding="utf-8").read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "oracle" not in node.module, f"{path} imports oracle: {node.module}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "oracle" not in alias.name, f"{path} imports oracle: {alias.name}"
        assert "get_ground_truth" not in source
        assert "MigrationGroundTruth" not in source
        assert "EvaluatorCapability" not in source


def test_harness_module_never_ends_up_with_oracle_in_sys_modules_by_itself():
    import sys

    for name in list(sys.modules):
        if name.startswith("research.gate0.oracle"):
            del sys.modules[name]

    case = build_case_manifest()[0]
    harness = MethodFacingHarness(case)
    harness.task()

    assert not any(name.startswith("research.gate0.oracle") for name in sys.modules)


@pytest.mark.parametrize("case", build_case_manifest(), ids=lambda c: c.case_id)
def test_harness_task_never_exposes_a_correct_answer_field(case):
    harness = MethodFacingHarness(case)
    task = harness.task()

    assert not hasattr(task, "correct_new_tool_name")
    assert not hasattr(task, "argument_mapping")
    assert not hasattr(task, "ground_truth")
    for contract in task.old_contracts + task.new_contracts:
        assert isinstance(contract, PublicToolContract)
        assert not hasattr(contract, "tool_id")


def test_harness_public_api_has_no_oracle_accessor():
    harness = MethodFacingHarness(build_case_manifest()[0])
    public_attrs = [name for name in dir(harness) if not name.startswith("_")]
    for name in public_attrs:
        assert "oracle" not in name.lower()
        assert "ground_truth" not in name.lower()


def test_oracle_accessor_rejects_a_non_capability_caller():
    case_id = build_case_manifest()[0].case_id
    with pytest.raises(PermissionError):
        get_ground_truth(case_id, capability="not-a-real-capability")  # type: ignore[arg-type]
    with pytest.raises(PermissionError):
        get_ground_truth(case_id, capability=None)  # type: ignore[arg-type]


def test_oracle_accessor_works_for_a_real_capability():
    case_id = build_case_manifest()[0].case_id
    gt = get_ground_truth(case_id, EvaluatorCapability())
    assert gt.case_id == case_id


def test_calling_an_unknown_tool_through_the_harness_fails_safely():
    harness = MethodFacingHarness(build_case_manifest()[0])
    with pytest.raises(SandboxStateError):
        harness.call_new_tool("definitely_not_a_real_tool", x=1)


def test_harness_writes_never_reach_a_second_harness_instance():
    from research.gate0.sandbox import EducationSandboxStore

    case = build_case_manifest()[2]  # added_required_field, create_enrollment
    a = MethodFacingHarness(case)
    b = MethodFacingHarness(case)
    a.call_old_tool("create_enrollment", student_id="STU-0001", course_code="CRS-101", semester="TERM-2026A")
    # b's isolated store must be unaffected by a's mutation -- same hash as a brand-new store.
    assert b._old_store.state_hash() == EducationSandboxStore().state_hash()  # noqa: SLF001
