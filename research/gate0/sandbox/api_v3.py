"""Education sandbox API v3 (Phase 6.2). Further controlled drift from v2.

Relative to v2: `find_module` is carried forward unchanged (needed as the
true correspondent for the semantic-near-collision case below); a new,
unrelated `browse_catalog` free-text search tool is added that
superficially resembles a course-lookup tool but has different
preconditions/effects (semantic near-collision decoy);
`check_prerequisite`'s `module_code` argument splits into `subject_area`
+ `catalog_number` (argument split); `get_timetable`'s `course_code` +
`semester` arguments merge into one `section_code` (argument merge);
`create_enrollment` is replaced outright by `finalize_registration`, a
genuinely different tool with a new identity and an added payment
precondition (tool replacement); `submit_leave_request` still has no
successor (no-equivalent, confirmed at both v1->v2 and v1->v3).
`record_advising_note`'s two arguments merge into one held-out variant.
"""

from __future__ import annotations

from typing import Any

from research.gate0.contracts import Effect, Precondition, ToolContract
from research.gate0.sandbox.store import EducationSandboxStore, SandboxStateError


class EducationApiV3:
    def __init__(self, store: EducationSandboxStore) -> None:
        self.store = store

    def find_module(self, course_code: str) -> dict[str, Any]:
        course = self.store.courses.get(course_code)
        if course is None:
            raise SandboxStateError(f"Unknown course_code {course_code!r}.")
        return {"title": course["title"], "credits": course["credits"], "seats_available": course["seats_available"]}

    def browse_catalog(self, query_text: str) -> dict[str, Any]:
        if not query_text:
            raise SandboxStateError("query_text must be non-empty.")
        needle = query_text.strip().casefold()
        matches = [
            {"course_code": code, "title": info["title"]}
            for code, info in self.store.courses.items()
            if needle in info["title"].casefold() or needle in code.casefold()
        ]
        return {"matches": matches}

    def check_prerequisite(self, program_code: str, subject_area: str, catalog_number: str) -> dict[str, Any]:
        module_code = f"{subject_area}-{catalog_number}"
        if module_code not in self.store.courses:
            raise SandboxStateError(f"Unknown course {module_code!r}.")
        if program_code not in {"PROG-CS", "PROG-EDU"}:
            raise SandboxStateError(f"Unknown program_code {program_code!r}.")
        completed = {"CRS-101"} if program_code == "PROG-CS" else set()
        missing = [c for c in self.store.prerequisites.get(module_code, []) if c not in completed]
        return {"eligible": not missing, "missing": missing}

    def get_timetable(self, section_code: str) -> dict[str, Any]:
        try:
            course_code, semester = section_code.split("::", 1)
        except ValueError as exc:
            raise SandboxStateError(f"section_code {section_code!r} must be '<course_code>::<semester>'.") from exc
        schedule = self.store.schedules.get((course_code, semester))
        if schedule is None:
            raise SandboxStateError(f"No schedule for section {section_code!r}.")
        return {"schedule": {"days": schedule["days"], "start_time": schedule["start_time"], "location": {"room": schedule["room"]}}}

    def finalize_registration(self, learner_ref: str, section_code: str, payment_status: str) -> dict[str, Any]:
        if payment_status != "paid":
            raise SandboxStateError("payment_status must be 'paid' to finalize registration.")
        try:
            course_code, semester = section_code.split("::", 1)
        except ValueError as exc:
            raise SandboxStateError(f"section_code {section_code!r} must be '<course_code>::<semester>'.") from exc
        course = self.store.courses.get(course_code)
        if course is None:
            raise SandboxStateError(f"Unknown course_code {course_code!r}.")
        if learner_ref not in self.store.student_programs:
            raise SandboxStateError(f"Unknown learner_ref {learner_ref!r}.")
        if course["seats_available"] <= 0:
            raise SandboxStateError(f"No seats available for {course_code!r}.")
        course["seats_available"] -= 1
        registration_id = self.store.next_id("REG")
        self.store.registrations[registration_id] = {
            "registration_id": registration_id,
            "learner_ref": learner_ref,
            "section_code": section_code,
            "status": "registered",
        }
        return {"registration_id": registration_id, "status": "registered"}

    def record_advising_note(self, note_payload: str) -> dict[str, Any]:
        try:
            learner_ref, _note_text = note_payload.split("|", 1)
        except ValueError as exc:
            raise SandboxStateError(f"note_payload {note_payload!r} must be '<learner_ref>|<note_text>'.") from exc
        if learner_ref not in self.store.student_programs:
            raise SandboxStateError(f"Unknown learner_ref {learner_ref!r}.")
        note_id = self.store.next_id("NOTE")
        return {"note_id": note_id, "status": "logged"}

    def contracts(self) -> tuple[ToolContract, ...]:
        return (
            ToolContract(
                tool_id="TOOL_COURSE_LOOKUP",
                version="v3",
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
                tool_id="TOOL_CATALOG_SEARCH",
                version="v3",
                name="browse_catalog",
                description="Free-text search across the course catalog, returning candidate matches.",
                input_schema={"type": "object", "properties": {"query_text": {"type": "string"}}, "required": ["query_text"]},
                output_schema={"type": "object", "properties": {"matches": {"type": "array"}}, "required": ["matches"]},
                preconditions=(Precondition(kind="field_type", target="query_text", expected="non_empty_string"),),
                effects=(Effect(kind="no_mutation", target="course_catalog", detail={"result_shape": "list"}),),
            ),
            ToolContract(
                tool_id="TOOL_PREREQ_CHECK",
                version="v3",
                name="check_prerequisite",
                description="Check whether a program satisfies a course's prerequisites, given a split course identifier.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "program_code": {"type": "string"},
                        "subject_area": {"type": "string"},
                        "catalog_number": {"type": "string"},
                    },
                    "required": ["program_code", "subject_area", "catalog_number"],
                },
                output_schema={
                    "type": "object",
                    "properties": {"eligible": {"type": "boolean"}, "missing": {"type": "array"}},
                    "required": ["eligible", "missing"],
                },
                preconditions=(
                    Precondition(kind="resource_exists", target="subject_area"),
                    Precondition(kind="resource_exists", target="catalog_number"),
                    Precondition(kind="resource_exists", target="program_code"),
                ),
                effects=(Effect(kind="no_mutation", target="prerequisite_rules"),),
            ),
            ToolContract(
                tool_id="TOOL_TIMETABLE",
                version="v3",
                name="get_timetable",
                description="Get the meeting schedule for a merged section identifier.",
                input_schema={"type": "object", "properties": {"section_code": {"type": "string"}}, "required": ["section_code"]},
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
                preconditions=(Precondition(kind="resource_exists", target="section_code"),),
                effects=(Effect(kind="no_mutation", target="schedule"),),
            ),
            ToolContract(
                tool_id="TOOL_FINALIZE_REGISTRATION",
                version="v3",
                name="finalize_registration",
                description="Finalize a paid registration into a course section.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "learner_ref": {"type": "string"},
                        "section_code": {"type": "string"},
                        "payment_status": {"type": "string"},
                    },
                    "required": ["learner_ref", "section_code", "payment_status"],
                },
                output_schema={
                    "type": "object",
                    "properties": {"registration_id": {"type": "string"}, "status": {"type": "string"}},
                    "required": ["registration_id", "status"],
                },
                preconditions=(
                    Precondition(kind="resource_exists", target="section_code"),
                    Precondition(kind="resource_exists", target="learner_ref"),
                    Precondition(kind="enum_member", target="payment_status", expected=["paid"]),
                    Precondition(kind="state_flag", target="state:seats_available"),
                ),
                effects=(Effect(kind="creates_resource", target="registration", detail={"status": "registered"}),),
            ),
            ToolContract(
                tool_id="TOOL_ADVISOR_NOTE",
                version="v3",
                name="record_advising_note",
                description="Record an advising note from a merged payload (held-out lineage, not part of the graded manifest).",
                input_schema={"type": "object", "properties": {"note_payload": {"type": "string"}}, "required": ["note_payload"]},
                output_schema={
                    "type": "object",
                    "properties": {"note_id": {"type": "string"}, "status": {"type": "string"}},
                    "required": ["note_id", "status"],
                },
                preconditions=(Precondition(kind="resource_exists", target="note_payload"),),
                effects=(Effect(kind="creates_resource", target="advisor_note", detail={"status": "logged"}),),
            ),
        )
