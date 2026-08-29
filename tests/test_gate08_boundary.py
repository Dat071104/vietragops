"""Gate 08 information-rights and frozen-artifact boundaries.

These are the tests that keep the gate honest: the method must not be able to
reach the oracle, must not be keyed to a drift family or a case id, and must not
have moved anything Gate 07 froze.
"""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from research.gate07.dataset.models import FAMILY_NAMES
from research.gate08.ablations import INFORMATION_RIGHTS
from research.gate08.harness import CLAIM_FAMILIES, EVAL_FAMILIES, calibration_cases, eval_cases

REPO_ROOT = Path(__file__).resolve().parents[1]
METHOD_DIR = REPO_ROOT / "research" / "gate08" / "method"
FROZEN_GATE07_PATHS = (
    "research/gate07/dataset",
    "research/gate07/oracle",
    "research/gate07/sandbox",
    "research/gate0",
)
FORBIDDEN_IMPORTS = (
    "research.gate07.oracle",
    "research.gate07.dataset.generator",
    "research.gate07.metrics",
    "EvaluatorCapability",
    "get_ground_truth",
)


def _method_sources() -> list[Path]:
    return sorted(path for path in METHOD_DIR.glob("*.py"))


def test_method_package_has_sources():
    assert _method_sources(), "no Gate 08 method sources found"


@pytest.mark.parametrize("needle", FORBIDDEN_IMPORTS)
def test_method_never_reaches_the_oracle(needle):
    for path in _method_sources():
        assert needle not in path.read_text(encoding="utf-8"), f"{path.name} references {needle}"


def test_method_is_not_keyed_to_a_drift_family_or_case_id():
    for path in _method_sources():
        text = path.read_text(encoding="utf-8")
        assert "G07-G-" not in text and "G07-H-" not in text, f"{path.name} names a case id"
        for family in FAMILY_NAMES:
            assert family not in text, f"{path.name} names the drift family {family}"


def test_every_arm_declares_information_rights():
    for arm_id, rights in INFORMATION_RIGHTS.items():
        assert rights, f"{arm_id} declares no rights"
        assert len(set(rights)) == len(rights)


def test_reduced_rights_arms_are_strict_subsets_of_the_method_arm():
    full = set(INFORMATION_RIGHTS["gate08_method"])
    assert set(INFORMATION_RIGHTS["ablate_no_history"]) < full
    assert set(INFORMATION_RIGHTS["ablate_schema_only"]) < set(INFORMATION_RIGHTS["ablate_no_history"])


def test_evaluation_surface_matches_the_narrow_gate07_go():
    assert CLAIM_FAMILIES == ("argument_split", "tool_replacement")
    cases = eval_cases()
    assert len(cases) == 45
    assert {case.family for case in cases} == set(EVAL_FAMILIES)
    assert all(not case.held_out for case in cases)


def test_calibration_split_is_held_out_only_and_disjoint_from_the_surface():
    calibration = calibration_cases()
    assert len(calibration) == 36
    assert all(case.held_out for case in calibration)
    assert not {case.case_id for case in calibration} & {case.case_id for case in eval_cases()}


def test_gate07_and_gate0_sources_are_unmodified_in_the_working_tree():
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *FROZEN_GATE07_PATHS],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", f"frozen Gate 07/Gate 0 sources changed:\n{result.stdout}"
