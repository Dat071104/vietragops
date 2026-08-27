"""Education sandbox API v2 (Phase 6.2). Evolves v1 with controlled drift.

Relative to v1: `search_course` is renamed to `find_module` (tool rename);
`check_prerequisite`'s arguments are renamed (argument rename);
`create_enrollment` gains a new required `consent_ack` field (added
required field); `get_timetable`'s output is restructured to a nested
shape (output restructure); `submit_leave_request` has no v2 successor
(no-equivalent). `log_advisor_note` is renamed with its argument also
renamed (held-out compound case, not part of the graded manifest).
"""

from __future__ import annotations

from typing import Any

from research.gate0.contracts import Effect, Precondition, ToolContract
from research.gate0.sandbox.store import EducationSandboxStore, SandboxStateError


class EducationApiV2:
    def __init__(self, store: EducationSandboxStore) -> None:
        self.store = store

    def find_module(self, course_code: str) -> dict[str, Any]:
        course = self.store.courses.get(course_code)
        if course is None:
            raise SandboxStateError(f"Unknown course_code {course_code!r}.")
        return {"title": course["title"], "credits": course["credits"], "seats_available": course["seats_available"]}

    def check_prerequisite(self, program_code: str, module_code: str) -> dict[str, Any]:
        if module_code not in self.store.courses:
            raise SandboxStateError(f"Unknown module_code {module_code!r}.")
        if program_code not in {"PROG-CS", "PROG-EDU"}:
            raise SandboxStateError(f"Unknown program_code {program_code!r}.")
        completed = {"CRS-101"} if program_code == "PROG-CS" else set()
        missing = [c for c in self.store.prerequisites.get(module_code, []) if c not in completed]
        return {"eligible": not missing, "missing": missing}

    def create_enrollment(self, student_id: str, course_code: str, semester: str, consent_ack: bool) -> dict[str, Any]:
        if consent_ack is not True:
            raise SandboxStateError("consent_ack must be true to enroll.")
        course = self.store.courses.get(course_code)
        if course is None:
            raise SandboxStateError(f"Unknown course_code {course_code!r}.")
        if student_id not in self.store.student_programs:
            raise SandboxStateError(f"Unknown student_id {student_id!r}.")
        if course["seats_available"] <= 0:
            raise SandboxStateError(f"No seats available for {course_code!r}.")
        course["seats_available"] -= 1
        enrollment_id = self.store.next_id("ENR")
        self.store.enrollments[enrollment_id] = {
            "enrollment_id": enrollment_id,
            "student_id": student_id,
            "course_code": course_code,
            "semester": semester,
            "status": "enrolled",
        }
        return {"enrollment_id": enrollment_id, "status": "enrolled"}

    def get_timetable(self, course_code: str, semester: str) -> dict[str, Any]:
        schedule = self.store.schedules.get((course_code, semester))
        if schedule is None:
            raise SandboxStateError(f"No schedule for {course_code!r}/{semester!r}.")
        return {"schedule": {"days": schedule["days"], "start_time": schedule["start_time"], "location": {"room": schedule["room"]}}}

    def record_advising_note(self, learner_ref: str, note_text: str) -> dict[str, Any]:
        if learner_ref not in self.store.student_programs:
            raise SandboxStateError(f"Unknown learner_ref {learner_ref!r}.")
        note_id = self.store.next_id("NOTE")
        return {"note_id": note_id, "status": "logged"}

    def contracts(self) -> tuple[ToolContract, ...]:
        return (
            ToolContract(
                tool_id="TOOL_COURSE_LOOKUP",
                version="v2",
                name="find_module",
                description="Find a module (course) by its code.",
                input_schema={"type": "object", "properties": {"course_code": {"type": "string"}}, "required": ["course_code"]},
                output_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "credits": {"type": "integer"},
                        "seats_available": {"type": "integer"},
                    },
                    "required": ["title", "credits", "seats_available"],
                },
                preconditions=(Precondition(kind="resource_exists", target="course_code"),),
                effects=(Effect(kind="no_mutation", target="course_catalog"),),
            ),
            ToolContract(
                tool_id="TOOL_PREREQ_CHECK",
                version="v2",
                name="check_prerequisite",
                description="Check whether a program satisfies a module's prerequisites.",
                input_schema={
                    "type": "object",
                    "properties": {"program_code": {"type": "string"}, "module_code": {"type": "string"}},
                    "required": ["program_code", "module_code"],
                },
                output_schema={
                    "type": "object",
                    "properties": {"eligible": {"type": "boolean"}, "missing": {"type": "array"}},
                    "required": ["eligible", "missing"],
                },
                preconditions=(
                    Precondition(kind="resource_exists", target="module_code"),
                    Precondition(kind="resource_exists", target="program_code"),
                ),
                effects=(Effect(kind="no_mutation", target="prerequisite_rules"),),
            ),
            ToolContract(
                tool_id="TOOL_ENROLLMENT",
                version="v2",
                name="create_enrollment",
                description="Enroll a student into a course section for a semester, with explicit consent.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "string"},
                        "course_code": {"type": "string"},
                        "semester": {"type": "string"},
                        "consent_ack": {"type": "boolean"},
                    },
                    "required": ["student_id", "course_code", "semester", "consent_ack"],
                },
                output_schema={
                    "type": "object",
                    "properties": {"enrollment_id": {"type": "string"}, "status": {"type": "string"}},
                    "required": ["enrollment_id", "status"],
                },
                preconditions=(
                    Precondition(kind="resource_exists", target="course_code"),
                    Precondition(kind="resource_exists", target="student_id"),
                    Precondition(kind="field_type", target="consent_ack", expected=True),
                    Precondition(kind="state_flag", target="state:seats_available"),
                ),
                effects=(Effect(kind="creates_resource", target="enrollment", detail={"status": "enrolled"}),),
            ),
            ToolContract(
                tool_id="TOOL_TIMETABLE",
                version="v2",
                name="get_timetable",
                description="Get the meeting schedule for a course section in a semester (nested shape).",
                input_schema={
                    "type": "object",
                    "properties": {"course_code": {"type": "string"}, "semester": {"type": "string"}},
                    "required": ["course_code", "semester"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "schedule": {
                            "type": "object",
                            "properties": {
                                "days": {"type": "array"},
                                "start_time": {"type": "string"},
                                "location": {"type": "object"},
                            },
                        }
                    },
                    "required": ["schedule"],
                },
                preconditions=(Precondition(kind="resource_exists", target="course_code"),),
                effects=(Effect(kind="no_mutation", target="schedule"),),
            ),
            ToolContract(
                tool_id="TOOL_ADVISOR_NOTE",
                version="v2",
                name="record_advising_note",
                description="Record an advising note for a learner (held-out lineage, not part of the graded manifest).",
                input_schema={
                    "type": "object",
                    "properties": {"learner_ref": {"type": "string"}, "note_text": {"type": "string"}},
                    "required": ["learner_ref", "note_text"],
                },
                output_schema={
                    "type": "object",
                    "properties": {"note_id": {"type": "string"}, "status": {"type": "string"}},
                    "required": ["note_id", "status"],
                },
                preconditions=(Precondition(kind="resource_exists", target="learner_ref"),),
                effects=(Effect(kind="creates_resource", target="advisor_note", detail={"status": "logged"}),),
            ),
        )
