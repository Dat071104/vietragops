"""Frozen drift-case manifest (Phase 6.3).

Every case here is derived directly from the contract/effect model in
`research/gate0/sandbox/api_v{1,2,3}.py` -- none was designed around any
proposed alignment method (none exists yet in this gate). Cases are
public/method-facing: `old_tool_name` and `candidate_new_tool_names` are
plain surface names (no `tool_id`), safe to hand to an evaluated method.
The correct answer for each case lives only in
`research/gate0/oracle/ground_truth.py`, gated behind an evaluator
capability (see that module and `research/gate0/harness/method_facing.py`).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DriftCase:
    case_id: str
    family: str
    old_version: str
    new_version: str
    old_tool_name: str
    candidate_new_tool_names: tuple[str, ...]
    seed: int
    notes: str
    held_out: bool = False


_CASES: tuple[DriftCase, ...] = (
    DriftCase(
        case_id="GATE06-CASE-001",
        family="tool_rename",
        old_version="v1",
        new_version="v2",
        old_tool_name="search_course",
        candidate_new_tool_names=("find_module", "check_prerequisite", "create_enrollment", "get_timetable"),
        seed=1,
        notes="Course lookup renamed between v1 and v2; arguments/behavior otherwise unchanged.",
    ),
    DriftCase(
        case_id="GATE06-CASE-002",
        family="argument_rename",
        old_version="v1",
        new_version="v2",
        old_tool_name="check_prerequisite",
        candidate_new_tool_names=("check_prerequisite",),
        seed=2,
        notes="Prerequisite check keeps its name in v2; both arguments are renamed.",
    ),
    DriftCase(
        case_id="GATE06-CASE-003",
        family="added_required_field",
        old_version="v1",
        new_version="v2",
        old_tool_name="create_enrollment",
        candidate_new_tool_names=("create_enrollment",),
        seed=3,
        notes="Enrollment keeps its name and original arguments in v2, plus one new required field.",
    ),
    DriftCase(
        case_id="GATE06-CASE-004",
        family="output_restructure",
        old_version="v1",
        new_version="v2",
        old_tool_name="get_timetable",
        candidate_new_tool_names=("get_timetable",),
        seed=4,
        notes="Timetable lookup keeps its name/arguments in v2; only the output shape is restructured.",
    ),
    DriftCase(
        case_id="GATE06-CASE-005",
        family="no_equivalent",
        old_version="v1",
        new_version="v2",
        old_tool_name="submit_leave_request",
        candidate_new_tool_names=("find_module", "check_prerequisite", "create_enrollment", "get_timetable"),
        seed=5,
        notes="Leave-request submission has no v2 successor of any kind.",
    ),
    DriftCase(
        case_id="GATE06-CASE-006",
        family="argument_split",
        old_version="v2",
        new_version="v3",
        old_tool_name="check_prerequisite",
        candidate_new_tool_names=("check_prerequisite",),
        seed=6,
        notes="Prerequisite check keeps its name in v3; module_code splits into two arguments.",
    ),
    DriftCase(
        case_id="GATE06-CASE-007",
        family="argument_merge",
        old_version="v2",
        new_version="v3",
        old_tool_name="get_timetable",
        candidate_new_tool_names=("get_timetable",),
        seed=7,
        notes="Timetable lookup keeps its name in v3; course_code+semester merge into one argument.",
    ),
    DriftCase(
        case_id="GATE06-CASE-008",
        family="tool_replacement",
        old_version="v2",
        new_version="v3",
        old_tool_name="create_enrollment",
        candidate_new_tool_names=("finalize_registration", "find_module", "browse_catalog"),
        seed=8,
        notes="Enrollment is replaced by a differently-scoped registration tool with an added payment precondition.",
    ),
    DriftCase(
        case_id="GATE06-CASE-009",
        family="semantic_near_collision",
        old_version="v2",
        new_version="v3",
        old_tool_name="find_module",
        candidate_new_tool_names=("find_module", "browse_catalog"),
        seed=9,
        notes=(
            "v3 adds a free-text 'browse_catalog' tool that superficially resembles a course-lookup tool; "
            "it is not behaviorally equivalent to the exact-lookup 'find_module'."
        ),
    ),
    DriftCase(
        case_id="GATE06-CASE-010",
        family="no_equivalent",
        old_version="v1",
        new_version="v3",
        old_tool_name="submit_leave_request",
        candidate_new_tool_names=("find_module", "browse_catalog", "check_prerequisite", "finalize_registration", "get_timetable"),
        seed=10,
        notes="Leave-request submission still has no successor by v3 either.",
    ),
)

_HELD_OUT_CASES: tuple[DriftCase, ...] = (
    DriftCase(
        case_id="GATE06-HELDOUT-001",
        family="tool_rename",
        old_version="v1",
        new_version="v2",
        old_tool_name="log_advisor_note",
        candidate_new_tool_names=("record_advising_note", "find_module", "check_prerequisite"),
        seed=101,
        notes="Held out for later Gate-0 work: compound tool-rename + argument-rename, not in the graded manifest.",
        held_out=True,
    ),
    DriftCase(
        case_id="GATE06-HELDOUT-002",
        family="argument_merge",
        old_version="v2",
        new_version="v3",
        old_tool_name="record_advising_note",
        candidate_new_tool_names=("record_advising_note",),
        seed=102,
        notes="Held out for later Gate-0 work: a second argument-merge instance on a different tool lineage.",
        held_out=True,
    ),
)


def build_case_manifest() -> tuple[DriftCase, ...]:
    """The frozen, graded case manifest. Never includes held-out cases."""
    return _CASES


def held_out_cases() -> tuple[DriftCase, ...]:
    """Structurally separate from the graded manifest; for later Gate-0 work only."""
    return _HELD_OUT_CASES
