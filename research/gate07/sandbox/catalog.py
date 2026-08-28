"""Synthetic contract catalog used by the Gate 07 case operators."""

from __future__ import annotations

from dataclasses import dataclass, replace

from research.gate0.contracts import Effect, Precondition

from research.gate07.sandbox.models import ToolDefinition


TOOL_RENAME = "tool_rename"
ARGUMENT_RENAME = "argument_rename"
MULTIPLE_RENAMES = "multiple_simultaneous_renames"
ADDED_REQUIRED = "added_required_field"
ARGUMENT_SPLIT = "argument_split"
ARGUMENT_MERGE = "argument_merge"
OUTPUT_RESTRUCTURE = "output_restructure"
TOOL_REPLACEMENT = "tool_replacement"
ONE_TO_MANY = "one_old_to_multiple_new"
MANY_TO_ONE = "multiple_old_to_one_new"
SEMANTIC_COLLISION = "semantic_near_collision"
NO_EQUIVALENT = "no_equivalent"


@dataclass(frozen=True)
class Lineage:
    family: str
    key: str
    old_names: tuple[str, ...]
    new_names: tuple[str, ...]
    old_operations: tuple[str, ...]
    new_operations: tuple[str, ...]
    old_fields: tuple[tuple[str, str], ...]
    new_fields: tuple[tuple[str, str], ...]
    old_output: tuple[tuple[str, str], ...]
    new_outputs: tuple[tuple[tuple[str, str], ...], ...]
    old_description: str
    new_descriptions: tuple[str, ...]
    old_ids: tuple[str, ...]
    new_ids: tuple[str, ...]


def _fields(*items: tuple[str, str]) -> tuple[tuple[str, str], ...]:
    return items


def _lineages() -> tuple[Lineage, ...]:
    return (
        Lineage(TOOL_RENAME, "course_lookup", ("search_course_catalog",), ("find_course_catalog",), ("course_lookup",), ("course_lookup",), _fields(("course_code", "string")), _fields(("course_code", "string")), _fields(("course_code", "string"), ("title", "string"), ("credits", "integer"), ("department", "string")), (_fields(("course_code", "string"), ("title", "string"), ("credits", "integer"), ("department", "string")),), "Find a course record by its exact course code.", ("Find a module record by its exact course code.",), ("G07_COURSE_LOOKUP",), ("G07_COURSE_LOOKUP",)),
        Lineage(TOOL_RENAME, "student_lookup", ("search_student_directory",), ("find_student_directory",), ("student_lookup",), ("student_lookup",), _fields(("student_id", "string")), _fields(("student_id", "string")), _fields(("student_id", "string"), ("display_name", "string"), ("program_code", "string"), ("status", "string")), (_fields(("student_id", "string"), ("display_name", "string"), ("program_code", "string"), ("status", "string")),), "Look up one learner in the student directory.", ("Find one learner in the student directory.",), ("G07_STUDENT_LOOKUP",), ("G07_STUDENT_LOOKUP",)),
        Lineage(TOOL_RENAME, "room_lookup", ("search_room_directory",), ("find_room_directory",), ("room_lookup",), ("room_lookup",), _fields(("room_code", "string")), _fields(("room_code", "string")), _fields(("room_code", "string"), ("building", "string"), ("capacity", "integer"), ("accessible", "boolean")), (_fields(("room_code", "string"), ("building", "string"), ("capacity", "integer"), ("accessible", "boolean")),), "Look up one teaching room by its room code.", ("Find one teaching room by its room code.",), ("G07_ROOM_LOOKUP",), ("G07_ROOM_LOOKUP",)),
        Lineage(ARGUMENT_RENAME, "eligibility", ("check_module_eligibility",), ("check_module_eligibility",), ("eligibility",), ("eligibility",), _fields(("student_id", "string"), ("course_code", "string")), _fields(("learner_ref", "string"), ("module_ref", "string")), _fields(("eligible", "boolean"), ("reason", "string")), (_fields(("eligible", "boolean"), ("reason", "string")),), "Check whether a learner may take a course.", ("Check whether a learner may take a module.",), ("G07_ELIGIBILITY",), ("G07_ELIGIBILITY",)),
        Lineage(ARGUMENT_RENAME, "grade", ("get_assessment_result",), ("get_assessment_result",), ("grade_lookup",), ("grade_lookup",), _fields(("assessment_id", "string")), _fields(("evaluation_id", "string")), _fields(("assessment_id", "string"), ("score", "integer"), ("released", "boolean")), (_fields(("assessment_id", "string"), ("score", "integer"), ("released", "boolean")),), "Retrieve one assessment result.", ("Retrieve one evaluation result.",), ("G07_GRADE",), ("G07_GRADE",)),
        Lineage(ARGUMENT_RENAME, "invoice", ("check_invoice_status",), ("check_invoice_status",), ("invoice_lookup",), ("invoice_lookup",), _fields(("invoice_id", "string")), _fields(("billing_ref", "string")), _fields(("invoice_id", "string"), ("amount", "integer"), ("status", "string")), (_fields(("invoice_id", "string"), ("amount", "integer"), ("status", "string")),), "Retrieve the status and amount of a student invoice.", ("Retrieve the status and amount of a billing record.",), ("G07_INVOICE",), ("G07_INVOICE",)),
        Lineage(MULTIPLE_RENAMES, "attendance", ("record_class_attendance",), ("log_session_presence",), ("attendance",), ("attendance",), _fields(("student_id", "string"), ("course_code", "string"), ("session_date", "string")), _fields(("learner_ref", "string"), ("module_ref", "string"), ("meeting_day", "string")), _fields(("student_id", "string"), ("attended", "boolean"), ("status", "string")), (_fields(("student_id", "string"), ("attended", "boolean"), ("status", "string")),), "Record attendance for a learner in a class meeting.", ("Log presence for a learner in a module meeting.",), ("G07_ATTENDANCE",), ("G07_ATTENDANCE",)),
        Lineage(MULTIPLE_RENAMES, "schedule", ("read_class_schedule",), ("inspect_module_timetable",), ("schedule",), ("schedule",), _fields(("course_code", "string"), ("term_id", "string"), ("session_day", "string")), _fields(("module_ref", "string"), ("period_ref", "string"), ("meeting_day", "string")), _fields(("day", "string"), ("start_time", "string"), ("room_code", "string")), (_fields(("day", "string"), ("start_time", "string"), ("room_code", "string")),), "Read the scheduled meeting for a course and term.", ("Inspect the timetable for a module and period.",), ("G07_SCHEDULE",), ("G07_SCHEDULE",)),
        Lineage(MULTIPLE_RENAMES, "invoice_audit", ("audit_student_invoice",), ("review_billing_record",), ("invoice_lookup",), ("invoice_lookup",), _fields(("invoice_id", "string"), ("audit_reason", "string")), _fields(("billing_ref", "string"), ("review_note", "string")), _fields(("invoice_id", "string"), ("amount", "integer"), ("status", "string")), (_fields(("invoice_id", "string"), ("amount", "integer"), ("status", "string")),), "Audit a student's invoice using a short reason.", ("Review a billing record using a short note.",), ("G07_INVOICE_AUDIT",), ("G07_INVOICE_AUDIT",)),
        Lineage(ADDED_REQUIRED, "enrollment", ("submit_course_enrollment",), ("submit_course_enrollment",), ("enrollment",), ("enrollment",), _fields(("student_id", "string"), ("course_code", "string"), ("term_id", "string")), _fields(("student_id", "string"), ("course_code", "string"), ("term_id", "string"), ("consent_ack", "boolean")), _fields(("enrollment_id", "string"), ("status", "string")), (_fields(("enrollment_id", "string"), ("status", "string")),), "Enroll a learner in a course for a term.", ("Enroll a learner after explicit consent for a course and term.",), ("G07_ENROLLMENT",), ("G07_ENROLLMENT",)),
        Lineage(ADDED_REQUIRED, "assessment_submit", ("submit_assessment_response",), ("submit_assessment_response",), ("assessment_submit",), ("assessment_submit",), _fields(("student_id", "string"), ("assessment_id", "string"), ("response_text", "string")), _fields(("student_id", "string"), ("assessment_id", "string"), ("response_text", "string"), ("honor_code", "boolean")), _fields(("record_id", "string"), ("status", "string")), (_fields(("record_id", "string"), ("status", "string")),), "Submit a learner's response to an assessment.", ("Submit a learner's response with an honor-code acknowledgement.",), ("G07_ASSESSMENT_SUBMIT",), ("G07_ASSESSMENT_SUBMIT",)),
        Lineage(ADDED_REQUIRED, "payment", ("record_invoice_payment",), ("record_invoice_payment",), ("payment",), ("payment",), _fields(("invoice_id", "string"), ("amount", "integer")), _fields(("invoice_id", "string"), ("amount", "integer"), ("payment_ack", "boolean")), _fields(("payment_id", "string"), ("status", "string")), (_fields(("payment_id", "string"), ("status", "string")),), "Record a payment against an invoice.", ("Record a payment after acknowledgement of the billing amount.",), ("G07_PAYMENT",), ("G07_PAYMENT",)),
        Lineage(ARGUMENT_SPLIT, "prerequisite", ("check_prerequisite_by_code",), ("check_prerequisite_by_parts",), ("eligibility",), ("eligibility",), _fields(("student_id", "string"), ("course_code", "string")), _fields(("student_id", "string"), ("subject_area", "string"), ("catalog_number", "string")), _fields(("eligible", "boolean"), ("reason", "string")), (_fields(("eligible", "boolean"), ("reason", "string")),), "Check a learner's prerequisite eligibility for a course.", ("Check prerequisite eligibility using subject area and catalog number.",), ("G07_PREREQUISITE",), ("G07_PREREQUISITE",)),
        Lineage(ARGUMENT_SPLIT, "module_schedule", ("get_module_schedule",), ("get_module_schedule_parts",), ("schedule",), ("schedule",), _fields(("course_code", "string"), ("term_id", "string")), _fields(("subject_area", "string"), ("catalog_number", "string"), ("period_ref", "string")), _fields(("day", "string"), ("start_time", "string"), ("room_code", "string")), (_fields(("day", "string"), ("start_time", "string"), ("room_code", "string")),), "Get a module meeting schedule for a term.", ("Get a module meeting schedule from split module parts.",), ("G07_MODULE_SCHEDULE",), ("G07_MODULE_SCHEDULE",)),
        Lineage(ARGUMENT_SPLIT, "course_contact", ("get_course_contact",), ("get_course_contact_parts",), ("course_lookup",), ("course_lookup",), _fields(("course_code", "string")), _fields(("subject_area", "string"), ("catalog_number", "string")), _fields(("course_code", "string"), ("title", "string"), ("credits", "integer"), ("department", "string")), (_fields(("course_code", "string"), ("title", "string"), ("credits", "integer"), ("department", "string")),), "Get the course record used by an academic contact.", ("Get the module record from split identifier parts.",), ("G07_COURSE_CONTACT",), ("G07_COURSE_CONTACT",)),
        Lineage(ARGUMENT_MERGE, "exam_schedule", ("get_exam_slot",), ("get_exam_slot_by_section",), ("schedule",), ("schedule",), _fields(("course_code", "string"), ("term_id", "string")), _fields(("section_ref", "string"),), _fields(("day", "string"), ("start_time", "string"), ("room_code", "string")), (_fields(("day", "string"), ("start_time", "string"), ("room_code", "string")),), "Get the exam meeting slot for a course and term.", ("Get the exam meeting slot from one section reference.",), ("G07_EXAM_SCHEDULE",), ("G07_EXAM_SCHEDULE",)),
        Lineage(ARGUMENT_MERGE, "advising_slot", ("get_advising_slot",), ("get_advising_slot_by_reference",), ("schedule",), ("schedule",), _fields(("course_code", "string"), ("term_id", "string")), _fields(("section_ref", "string"),), _fields(("day", "string"), ("start_time", "string"), ("room_code", "string")), (_fields(("day", "string"), ("start_time", "string"), ("room_code", "string")),), "Get an advising meeting slot linked to a course and term.", ("Get an advising meeting slot from one merged reference.",), ("G07_ADVISING_SLOT",), ("G07_ADVISING_SLOT",)),
        Lineage(ARGUMENT_MERGE, "classroom_slot", ("get_classroom_slot",), ("get_classroom_slot_by_section",), ("schedule",), ("schedule",), _fields(("course_code", "string"), ("term_id", "string")), _fields(("section_ref", "string"),), _fields(("day", "string"), ("start_time", "string"), ("room_code", "string")), (_fields(("day", "string"), ("start_time", "string"), ("room_code", "string")),), "Get a classroom slot linked to a course and term.", ("Get a classroom slot from one merged section reference.",), ("G07_CLASSROOM_SLOT",), ("G07_CLASSROOM_SLOT",)),
        Lineage(OUTPUT_RESTRUCTURE, "course_summary", ("get_course_summary",), ("get_course_summary",), ("course_lookup",), ("nested_course",), _fields(("course_code", "string")), _fields(("course_code", "string")), _fields(("course_code", "string"), ("title", "string"), ("credits", "integer"), ("department", "string")), (_fields(("course", "object"),),), "Get the compact course summary.", ("Get the course summary in a nested response.",), ("G07_COURSE_SUMMARY",), ("G07_COURSE_SUMMARY",)),
        Lineage(OUTPUT_RESTRUCTURE, "student_profile", ("get_student_profile",), ("get_student_profile",), ("student_lookup",), ("nested_student",), _fields(("student_id", "string")), _fields(("student_id", "string")), _fields(("student_id", "string"), ("display_name", "string"), ("program_code", "string"), ("status", "string")), (_fields(("profile", "object"),),), "Get a learner profile.", ("Get a learner profile in a nested response.",), ("G07_STUDENT_PROFILE",), ("G07_STUDENT_PROFILE",)),
        Lineage(OUTPUT_RESTRUCTURE, "transcript", ("get_student_transcript",), ("get_student_transcript",), ("transcript",), ("nested_transcript",), _fields(("student_id", "string")), _fields(("student_id", "string")), _fields(("student_id", "string"), ("courses", "array"), ("standing", "string")), (_fields(("transcript", "object"),),), "Get a learner's transcript summary.", ("Get a learner's transcript under a transcript object.",), ("G07_TRANSCRIPT",), ("G07_TRANSCRIPT",)),
        Lineage(TOOL_REPLACEMENT, "registration", ("create_registration",), ("finalize_paid_registration",), ("enrollment",), ("enrollment_replacement",), _fields(("student_id", "string"), ("course_code", "string"), ("term_id", "string")), _fields(("learner_ref", "string"), ("section_ref", "string"), ("payment_status", "string")), _fields(("enrollment_id", "string"), ("status", "string")), (_fields(("registration_id", "string"), ("status", "string")),), "Create a course registration for a learner.", ("Finalize a paid registration for a learner and section.",), ("G07_REGISTRATION",), ("G07_FINALIZE_REGISTRATION",)),
        Lineage(TOOL_REPLACEMENT, "credential", ("issue_completion_certificate",), ("grant_completion_credential",), ("credential",), ("credential",), _fields(("student_id", "string"), ("course_code", "string")), _fields(("learner_ref", "string"), ("course_ref", "string"), ("approval_status", "string")), _fields(("credential_id", "string"), ("status", "string")), (_fields(("credential_id", "string"), ("status", "string")),), "Issue a completion certificate for a learner.", ("Grant a completion credential after academic approval.",), ("G07_CREDENTIAL",), ("G07_GRANT_CREDENTIAL",)),
        Lineage(TOOL_REPLACEMENT, "reservation", ("reserve_teaching_room",), ("confirm_room_booking",), ("reservation",), ("reservation",), _fields(("room_code", "string"), ("term_id", "string")), _fields(("facility_ref", "string"), ("period_ref", "string"), ("approval_status", "string")), _fields(("booking_id", "string"), ("status", "string")), (_fields(("booking_id", "string"), ("status", "string")),), "Reserve a teaching room for a term.", ("Confirm an approved room booking for a period.",), ("G07_RESERVATION",), ("G07_CONFIRM_BOOKING",)),
        Lineage(ONE_TO_MANY, "profile_parts", ("get_complete_learner_profile",), ("get_learner_identity", "get_learner_program"), ("student_lookup",), ("identity_part", "program_part"), _fields(("student_id", "string")), _fields(("student_id", "string")), _fields(("student_id", "string"), ("display_name", "string"), ("program_code", "string"), ("status", "string")), (_fields(("student_id", "string"), ("display_name", "string"), ("status", "string")), _fields(("student_id", "string"), ("program_code", "string"))), "Get the complete learner profile in one response.", ("Get the learner identity portion.", "Get the learner program portion."), ("G07_PROFILE_PARTS",), ("G07_LEARNER_IDENTITY", "G07_LEARNER_PROGRAM")),
        Lineage(ONE_TO_MANY, "course_parts", ("get_course_faculty_record",), ("get_course_instructor", "get_course_department"), ("course_lookup",), ("course_title", "course_lookup"), _fields(("course_code", "string")), _fields(("course_code", "string")), _fields(("course_code", "string"), ("title", "string"), ("credits", "integer"), ("department", "string")), (_fields(("course_code", "string"), ("title", "string")), _fields(("course_code", "string"), ("department", "string"), ("credits", "integer"))), "Get the course faculty record in one response.", ("Get the course's instructor-facing title.", "Get the course's department summary."), ("G07_COURSE_PARTS",), ("G07_COURSE_INSTRUCTOR", "G07_COURSE_DEPARTMENT")),
        Lineage(ONE_TO_MANY, "assessment_parts", ("get_assessment_record",), ("get_assessment_definition", "get_recorded_assessment_result"), ("grade_lookup",), ("assessment_part", "grade_lookup"), _fields(("assessment_id", "string")), _fields(("assessment_id", "string")), _fields(("assessment_id", "string"), ("score", "integer"), ("released", "boolean")), (_fields(("assessment_id", "string"), ("assessment_type", "string")), _fields(("assessment_id", "string"), ("score", "integer"), ("released", "boolean"))), "Get the complete assessment record.", ("Get the assessment definition portion.", "Get the released assessment result portion."), ("G07_ASSESSMENT_PARTS",), ("G07_ASSESSMENT_DEFINITION", "G07_ASSESSMENT_RESULT")),
        Lineage(MANY_TO_ONE, "course_generalized", ("get_course_title", "get_course_credits"), ("get_course_summary_generalized",), ("course_title", "course_credits"), ("course_summary",), _fields(("course_code", "string")), _fields(("course_code", "string")), _fields(("title", "string"),), (_fields(("course_code", "string"), ("title", "string"), ("credits", "integer"), ("department", "string")),), "Get a course title and get its credit count are separate operations.", ("Get the generalized course summary containing title and credits.",), ("G07_COURSE_TITLE", "G07_COURSE_CREDITS"), ("G07_COURSE_SUMMARY_GENERALIZED",)),
        Lineage(MANY_TO_ONE, "invoice_generalized", ("get_invoice_amount", "get_invoice_state"), ("get_invoice_summary_generalized",), ("invoice_lookup", "invoice_lookup"), ("invoice_summary",), _fields(("invoice_id", "string")), _fields(("invoice_id", "string")), _fields(("amount", "integer"),), (_fields(("invoice_id", "string"), ("amount", "integer"), ("status", "string")),), "Get an invoice amount and get its state are separate operations.", ("Get the generalized invoice summary containing amount and state.",), ("G07_INVOICE_AMOUNT", "G07_INVOICE_STATE"), ("G07_INVOICE_SUMMARY_GENERALIZED",)),
        Lineage(MANY_TO_ONE, "student_generalized", ("get_student_name", "get_student_program"), ("get_student_summary_generalized",), ("student_lookup", "program_lookup"), ("student_summary",), _fields(("student_id", "string")), _fields(("student_id", "string")), _fields(("display_name", "string"),), (_fields(("student_id", "string"), ("display_name", "string"), ("program_code", "string"), ("status", "string")),), "Get a learner name and get the learner program are separate operations.", ("Get the generalized learner summary containing identity and program.",), ("G07_STUDENT_NAME", "G07_STUDENT_PROGRAM"), ("G07_STUDENT_SUMMARY_GENERALIZED",)),
        Lineage(SEMANTIC_COLLISION, "course_collision", ("find_exact_course",), ("lookup_exact_course",), ("exact_course_lookup",), ("exact_course_lookup",), _fields(("course_code", "string")), _fields(("course_code", "string")), _fields(("course_code", "string"), ("title", "string"), ("credits", "integer"), ("department", "string")), (_fields(("course_code", "string"), ("title", "string"), ("credits", "integer"), ("department", "string")),), "Find one exact course record by code.", ("Look up one exact module record by code.",), ("G07_EXACT_COURSE",), ("G07_EXACT_COURSE",)),
        Lineage(SEMANTIC_COLLISION, "room_collision", ("find_exact_room",), ("lookup_exact_room",), ("room_lookup",), ("room_lookup",), _fields(("room_code", "string")), _fields(("room_code", "string")), _fields(("room_code", "string"), ("building", "string"), ("capacity", "integer"), ("accessible", "boolean")), (_fields(("room_code", "string"), ("building", "string"), ("capacity", "integer"), ("accessible", "boolean")),), "Find one exact room record by code.", ("Look up one exact facility record by code.",), ("G07_EXACT_ROOM",), ("G07_EXACT_ROOM",)),
        Lineage(SEMANTIC_COLLISION, "student_collision", ("find_exact_learner",), ("lookup_exact_learner",), ("student_lookup",), ("student_lookup",), _fields(("student_id", "string")), _fields(("student_id", "string")), _fields(("student_id", "string"), ("display_name", "string"), ("program_code", "string"), ("status", "string")), (_fields(("student_id", "string"), ("display_name", "string"), ("program_code", "string"), ("status", "string")),), "Find one exact learner record by identifier.", ("Look up one exact learner record by identifier.",), ("G07_EXACT_STUDENT",), ("G07_EXACT_STUDENT",)),
        Lineage(NO_EQUIVALENT, "withdrawal", ("request_course_withdrawal",), (), ("request_only",), (), _fields(("student_id", "string"), ("course_code", "string")), (), _fields(("record_id", "string"), ("status", "string")), (), "Request a course withdrawal that changes enrollment standing.", (), ("G07_WITHDRAWAL",), ()),
        Lineage(NO_EQUIVALENT, "appeal", ("submit_grade_appeal",), (), ("request_only",), (), _fields(("student_id", "string"), ("assessment_id", "string"), ("reason", "string")), (), _fields(("record_id", "string"), ("status", "string")), (), "Submit a grade appeal for formal review.", (), ("G07_APPEAL",), ()),
        Lineage(NO_EQUIVALENT, "transfer", ("request_transfer_credit",), (), ("request_only",), (), _fields(("student_id", "string"), ("course_code", "string"), ("source_institution", "string")), (), _fields(("record_id", "string"), ("status", "string")), (), "Request transfer credit toward a learner record.", (), ("G07_TRANSFER",), ()),
    )


def _opaque_lineages(lineages: tuple[Lineage, ...]) -> tuple[Lineage, ...]:
    """Keep internal lineage identifiers out of every public contract string."""
    return tuple(replace(lineage, key=f"L{index:03d}") for index, lineage in enumerate(lineages, start=1))


LINEAGES = _opaque_lineages(_lineages())


def _schema(fields: tuple[tuple[str, str], ...]) -> dict:
    return {"type": "object", "properties": {name: {"type": kind} for name, kind in fields}, "required": [name for name, _ in fields]}


def _preconditions(fields: tuple[tuple[str, str], ...], operation: str) -> tuple[Precondition, ...]:
    targets = [name for name, _ in fields if name not in {"response_text", "answer", "reason", "audit_reason", "review_note", "session_date", "meeting_day", "source_institution"}]
    if not targets:
        targets = [name for name, _ in fields]
    return tuple(Precondition(kind="resource_exists", target=name) for name in targets[:3])


def _effects(operation: str) -> tuple[Effect, ...]:
    if operation in {"enrollment", "enrollment_replacement", "assessment_submit", "payment", "credential", "reservation", "request_only"}:
        target = {"enrollment": "enrollment", "enrollment_replacement": "registration", "assessment_submit": "submission", "payment": "payment", "credential": "credential", "reservation": "booking", "request_only": "request"}[operation]
        return (Effect(kind="creates_resource", target=target),)
    return (Effect(kind="no_mutation", target="education_records"),)


def _actual_output(operation: str, output: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    overrides = {
        "course_title": _fields(("course_code", "string"), ("title", "string")),
        "course_credits": _fields(("course_code", "string"), ("credits", "integer")),
        "program_lookup": _fields(("program_code", "string"), ("status", "string")),
        "invoice_lookup": _fields(("invoice_id", "string"), ("amount", "integer"), ("status", "string")),
    }
    return overrides.get(operation, output)


def _definition(version: str, name: str, tool_id: str, operation: str, fields: tuple[tuple[str, str], ...], output: tuple[tuple[str, str], ...], description: str, lineage_key: str) -> ToolDefinition:
    return ToolDefinition(tool_id, version, name, description, _schema(fields), _schema(_actual_output(operation, output)), _preconditions(fields, operation), _effects(operation), operation, lineage_key)


def _decoy_definitions(version: str) -> tuple[ToolDefinition, ...]:
    return (
        _definition(version, "browse_course_catalog", "G07_CATALOG_BROWSE", "search_decoy", _fields(("query_text", "string")), _fields(("matches", "array")), "Search the catalog by free text and return possible matches.", "decoy_catalog"),
        _definition(version, "search_room_options", "G07_ROOM_SEARCH", "search_decoy", _fields(("query_text", "string")), _fields(("matches", "array")), "Search room options by a descriptive phrase.", "decoy_room"),
        _definition(version, "search_learner_records", "G07_LEARNER_SEARCH", "search_decoy", _fields(("query_text", "string")), _fields(("matches", "array")), "Search learner records by a free-text phrase.", "decoy_learner"),
    )


def build_definitions(version: str) -> tuple[ToolDefinition, ...]:
    """Build all real contracts for one synthetic API version."""
    if version not in {"v1", "v2", "v3"}:
        raise ValueError(f"Unknown Gate 07 version {version!r}.")
    definitions: list[ToolDefinition] = []
    for lineage in LINEAGES:
        if version == "v1":
            for index, name in enumerate(lineage.old_names):
                definitions.append(_definition(version, name, lineage.old_ids[index], lineage.old_operations[index], lineage.old_fields, lineage.old_output, lineage.old_description, lineage.key))
        else:
            for index, name in enumerate(lineage.new_names):
                definitions.append(_definition(version, name, lineage.new_ids[index], lineage.new_operations[index], lineage.new_fields, lineage.new_outputs[index], lineage.new_descriptions[index], lineage.key))
    if version != "v1":
        definitions.extend(_decoy_definitions(version))
    return tuple(definitions)


def all_lineages() -> tuple[Lineage, ...]:
    return LINEAGES
