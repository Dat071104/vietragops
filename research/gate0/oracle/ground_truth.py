"""Evaluator-only migration ground truth (Phase 6.4).

**Honest scope of "hidden".** This module is an ordinary, readable Python
file: anyone with unrestricted access to this repository (its owner, a
reviewer, this agent) can open it. "Hidden" here means something
narrower and real: nothing under `research/gate0/harness/` (the only
interface an evaluated method is ever given) imports this module, holds a
reference to its contents, or can reach it through any method it exposes
-- enforced by `tests/test_gate06_oracle_boundary.py` via both static
source-scanning and runtime introspection of the harness. It is an
execution/import-access boundary the test harness enforces, not
cryptographic secrecy against a developer with full repository access.

`get_ground_truth` additionally requires a real `EvaluatorCapability`
instance (from `research.gate0.evaluator.evaluator`) -- a runtime
capability check, not a security boundary on its own, that makes it
structurally impossible to call this accessor by accident from code that
was never handed a capability.
"""

from __future__ import annotations

from dataclasses import dataclass

from research.gate0.evaluator.capability import EvaluatorCapability


@dataclass(frozen=True)
class MigrationGroundTruth:
    case_id: str
    family: str
    old_tool_id: str
    correct_new_tool_id: str | None
    correct_new_tool_name: str | None
    argument_mapping: dict[str, tuple[str, ...]]
    new_only_required_fields: tuple[str, ...]
    expected_effect_kind: str | None
    output_field_mapping: dict[str, str] | None
    rationale: str


_GROUND_TRUTH: dict[str, MigrationGroundTruth] = {
    gt.case_id: gt
    for gt in (
        MigrationGroundTruth(
            case_id="GATE06-CASE-001",
            family="tool_rename",
            old_tool_id="TOOL_COURSE_LOOKUP",
            correct_new_tool_id="TOOL_COURSE_LOOKUP",
            correct_new_tool_name="find_module",
            argument_mapping={"course_code": ("course_code",)},
            new_only_required_fields=(),
            expected_effect_kind="no_mutation",
            output_field_mapping=None,
            rationale="Pure rename: identity, arguments, schema, preconditions and effects are unchanged.",
        ),
        MigrationGroundTruth(
            case_id="GATE06-CASE-002",
            family="argument_rename",
            old_tool_id="TOOL_PREREQ_CHECK",
            correct_new_tool_id="TOOL_PREREQ_CHECK",
            correct_new_tool_name="check_prerequisite",
            argument_mapping={"student_program": ("program_code",), "course_code": ("module_code",)},
            new_only_required_fields=(),
            expected_effect_kind="no_mutation",
            output_field_mapping=None,
            rationale="Same tool, same behavior; both argument names change.",
        ),
        MigrationGroundTruth(
            case_id="GATE06-CASE-003",
            family="added_required_field",
            old_tool_id="TOOL_ENROLLMENT",
            correct_new_tool_id="TOOL_ENROLLMENT",
            correct_new_tool_name="create_enrollment",
            argument_mapping={
                "student_id": ("student_id",),
                "course_code": ("course_code",),
                "semester": ("semester",),
            },
            new_only_required_fields=("consent_ack",),
            expected_effect_kind="creates_resource",
            output_field_mapping=None,
            rationale="Original arguments unchanged; one new required field with no old counterpart.",
        ),
        MigrationGroundTruth(
            case_id="GATE06-CASE-004",
            family="output_restructure",
            old_tool_id="TOOL_TIMETABLE",
            correct_new_tool_id="TOOL_TIMETABLE",
            correct_new_tool_name="get_timetable",
            argument_mapping={"course_code": ("course_code",), "semester": ("semester",)},
            new_only_required_fields=(),
            expected_effect_kind="no_mutation",
            output_field_mapping={
                "days": "schedule.days",
                "start_time": "schedule.start_time",
                "room": "schedule.location.room",
            },
            rationale="Same tool/arguments; output nested under 'schedule'/'location'.",
        ),
        MigrationGroundTruth(
            case_id="GATE06-CASE-005",
            family="no_equivalent",
            old_tool_id="TOOL_LEAVE_REQUEST",
            correct_new_tool_id=None,
            correct_new_tool_name=None,
            argument_mapping={},
            new_only_required_fields=(),
            expected_effect_kind=None,
            output_field_mapping=None,
            rationale="Leave-request submission was deprecated with no v2 migration path.",
        ),
        MigrationGroundTruth(
            case_id="GATE06-CASE-006",
            family="argument_split",
            old_tool_id="TOOL_PREREQ_CHECK",
            correct_new_tool_id="TOOL_PREREQ_CHECK",
            correct_new_tool_name="check_prerequisite",
            argument_mapping={
                "program_code": ("program_code",),
                "module_code": ("subject_area", "catalog_number"),
            },
            new_only_required_fields=(),
            expected_effect_kind="no_mutation",
            output_field_mapping=None,
            rationale="module_code (e.g. 'CRS-101') splits into subject_area ('CRS') + catalog_number ('101').",
        ),
        MigrationGroundTruth(
            case_id="GATE06-CASE-007",
            family="argument_merge",
            old_tool_id="TOOL_TIMETABLE",
            correct_new_tool_id="TOOL_TIMETABLE",
            correct_new_tool_name="get_timetable",
            argument_mapping={"course_code": ("section_code",), "semester": ("section_code",)},
            new_only_required_fields=(),
            expected_effect_kind="no_mutation",
            output_field_mapping=None,
            rationale="course_code + semester merge into one 'section_code' ('<course_code>::<semester>').",
        ),
        MigrationGroundTruth(
            case_id="GATE06-CASE-008",
            family="tool_replacement",
            old_tool_id="TOOL_ENROLLMENT",
            correct_new_tool_id="TOOL_FINALIZE_REGISTRATION",
            correct_new_tool_name="finalize_registration",
            argument_mapping={
                "student_id": ("learner_ref",),
                "course_code": ("section_code",),
                "semester": ("section_code",),
                "consent_ack": (),
            },
            new_only_required_fields=("payment_status",),
            expected_effect_kind="creates_resource",
            output_field_mapping=None,
            rationale=(
                "Genuine replacement, not a rename: new tool_id, consent_ack has no successor, "
                "a new payment precondition is required, and the created resource is a 'registration', not an 'enrollment'."
            ),
        ),
        MigrationGroundTruth(
            case_id="GATE06-CASE-009",
            family="semantic_near_collision",
            old_tool_id="TOOL_COURSE_LOOKUP",
            correct_new_tool_id="TOOL_COURSE_LOOKUP",
            correct_new_tool_name="find_module",
            argument_mapping={"course_code": ("course_code",)},
            new_only_required_fields=(),
            expected_effect_kind="no_mutation",
            output_field_mapping=None,
            rationale=(
                "'browse_catalog' is a plausible decoy (free-text search, different tool_id "
                "TOOL_CATALOG_SEARCH) but returns a list of candidate matches rather than one exact "
                "resource and lacks the resource_exists precondition -- not behaviorally equivalent."
            ),
        ),
        MigrationGroundTruth(
            case_id="GATE06-CASE-010",
            family="no_equivalent",
            old_tool_id="TOOL_LEAVE_REQUEST",
            correct_new_tool_id=None,
            correct_new_tool_name=None,
            argument_mapping={},
            new_only_required_fields=(),
            expected_effect_kind=None,
            output_field_mapping=None,
            rationale="Still no successor by v3.",
        ),
    )
}


def get_ground_truth(case_id: str, capability: EvaluatorCapability) -> MigrationGroundTruth:
    if not isinstance(capability, EvaluatorCapability):
        raise PermissionError("get_ground_truth requires a real EvaluatorCapability instance.")
    try:
        return _GROUND_TRUTH[case_id]
    except KeyError as exc:
        raise KeyError(f"No ground truth recorded for case_id {case_id!r}.") from exc


def all_case_ids(capability: EvaluatorCapability) -> tuple[str, ...]:
    if not isinstance(capability, EvaluatorCapability):
        raise PermissionError("all_case_ids requires a real EvaluatorCapability instance.")
    return tuple(_GROUND_TRUTH.keys())
