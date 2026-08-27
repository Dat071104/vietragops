"""Education sandbox API v1 (Phase 6.2). Fictional, local-only, deterministic."""

from __future__ import annotations

from typing import Any

from research.gate0.contracts import Effect, Precondition, ToolContract
from research.gate0.sandbox.store import EducationSandboxStore, SandboxStateError


class EducationApiV1:
    def __init__(self, store: EducationSandboxStore) -> None:
        self.store = store

    def search_course(self, course_code: str) -> dict[str, Any]:
        course = self.store.courses.get(course_code)
        if course is None:
            raise SandboxStateError(f"Unknown course_code {course_code!r}.")
        return {"title": course["title"], "credits": course["credits"], "seats_available": course["seats_available"]}

    def check_prerequisite(self, student_program: str, course_code: str) -> dict[str, Any]:
        if course_code not in self.store.courses:
            raise SandboxStateError(f"Unknown course_code {course_code!r}.")
        if student_program not in {p for p in self.store.student_programs.values()} | {"PROG-CS", "PROG-EDU"}:
            raise SandboxStateError(f"Unknown student_program {student_program!r}.")
        missing = [c for c in self.store.prerequisites.get(course_code, []) if c not in self._completed_courses(student_program)]
        return {"eligible": not missing, "missing": missing}

    def _completed_courses(self, student_program: str) -> set[str]:
        # Deterministic sandbox rule: a program's own intro course is always
        # considered completed, so PROG-CS is eligible for CRS-201 by default.
        return {"CRS-101"} if student_program == "PROG-CS" else set()

    def create_enrollment(self, student_id: str, course_code: str, semester: str) -> dict[str, Any]:
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
        return {"days": schedule["days"], "start_time": schedule["start_time"], "room": schedule["room"]}

    def submit_leave_request(self, student_id: str, reason: str) -> dict[str, Any]:
        if student_id not in self.store.student_programs:
            raise SandboxStateError(f"Unknown student_id {student_id!r}.")
        if not reason:
            raise SandboxStateError("reason must be non-empty.")
        request_id = self.store.next_id("LVR")
        self.store.leave_requests[request_id] = {"request_id": request_id, "student_id": student_id, "reason": reason, "status": "submitted"}
        return {"request_id": request_id, "status": "submitted"}

    def contracts(self) -> tuple[ToolContract, ...]:
        return (
            ToolContract(
                tool_id="TOOL_COURSE_LOOKUP",
                version="v1",
                name="search_course",
                description="Look up a course by its code.",
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
                version="v1",
                name="check_prerequisite",
                description="Check whether a student's program satisfies a course's prerequisites.",
                input_schema={
                    "type": "object",
                    "properties": {"student_program": {"type": "string"}, "course_code": {"type": "string"}},
                    "required": ["student_program", "course_code"],
                },
                output_schema={
                    "type": "object",
                    "properties": {"eligible": {"type": "boolean"}, "missing": {"type": "array"}},
                    "required": ["eligible", "missing"],
                },
                preconditions=(
                    Precondition(kind="resource_exists", target="course_code"),
                    Precondition(kind="resource_exists", target="student_program"),
                ),
                effects=(Effect(kind="no_mutation", target="prerequisite_rules"),),
            ),
            ToolContract(
                tool_id="TOOL_ENROLLMENT",
                version="v1",
                name="create_enrollment",
                description="Enroll a student into a course section for a semester.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "string"},
                        "course_code": {"type": "string"},
                        "semester": {"type": "string"},
                    },
                    "required": ["student_id", "course_code", "semester"],
                },
                output_schema={
                    "type": "object",
                    "properties": {"enrollment_id": {"type": "string"}, "status": {"type": "string"}},
                    "required": ["enrollment_id", "status"],
                },
                preconditions=(
                    Precondition(kind="resource_exists", target="course_code"),
                    Precondition(kind="resource_exists", target="student_id"),
                    Precondition(kind="state_flag", target="state:seats_available"),
                ),
                effects=(Effect(kind="creates_resource", target="enrollment", detail={"status": "enrolled"}),),
            ),
            ToolContract(
                tool_id="TOOL_TIMETABLE",
                version="v1",
                name="get_timetable",
                description="Get the meeting schedule for a course section in a semester.",
                input_schema={
                    "type": "object",
                    "properties": {"course_code": {"type": "string"}, "semester": {"type": "string"}},
                    "required": ["course_code", "semester"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "days": {"type": "array"},
                        "start_time": {"type": "string"},
                        "room": {"type": "string"},
                    },
                    "required": ["days", "start_time", "room"],
                },
                preconditions=(Precondition(kind="resource_exists", target="course_code"),),
                effects=(Effect(kind="no_mutation", target="schedule"),),
            ),
            ToolContract(
                tool_id="TOOL_LEAVE_REQUEST",
                version="v1",
                name="submit_leave_request",
                description="Submit a leave-of-absence request for a student.",
                input_schema={
                    "type": "object",
                    "properties": {"student_id": {"type": "string"}, "reason": {"type": "string"}},
                    "required": ["student_id", "reason"],
                },
                output_schema={
                    "type": "object",
                    "properties": {"request_id": {"type": "string"}, "status": {"type": "string"}},
                    "required": ["request_id", "status"],
                },
                preconditions=(
                    Precondition(kind="resource_exists", target="student_id"),
                    Precondition(kind="field_type", target="reason", expected="non_empty_string"),
                ),
                effects=(Effect(kind="creates_resource", target="leave_request", detail={"status": "submitted"}),),
            ),
            ToolContract(
                tool_id="TOOL_ADVISOR_NOTE",
                version="v1",
                name="log_advisor_note",
                description="Log an advising note for a student (held-out lineage, not part of the graded manifest).",
                input_schema={
                    "type": "object",
                    "properties": {"student_id": {"type": "string"}, "note_text": {"type": "string"}},
                    "required": ["student_id", "note_text"],
                },
                output_schema={
                    "type": "object",
                    "properties": {"note_id": {"type": "string"}, "status": {"type": "string"}},
                    "required": ["note_id", "status"],
                },
                preconditions=(Precondition(kind="resource_exists", target="student_id"),),
                effects=(Effect(kind="creates_resource", target="advisor_note", detail={"status": "logged"}),),
            ),
        )

    def log_advisor_note(self, student_id: str, note_text: str) -> dict[str, Any]:
        if student_id not in self.store.student_programs:
            raise SandboxStateError(f"Unknown student_id {student_id!r}.")
        note_id = self.store.next_id("NOTE")
        return {"note_id": note_id, "status": "logged"}
