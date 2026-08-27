"""Real deterministic executions for Gate 07 tool definitions."""

from __future__ import annotations

from typing import Any

from research.gate07.sandbox.models import ToolDefinition
from research.gate07.sandbox.store import Gate07SandboxStore, SandboxStateError


def _required_args(definition: ToolDefinition, args: dict[str, Any]) -> None:
    required = definition.input_schema.get("required", [])
    properties = definition.input_schema.get("properties", {})
    missing = [name for name in required if name not in args]
    if missing:
        raise TypeError(f"Missing required arguments: {', '.join(missing)}")
    for name, value in args.items():
        expected = properties.get(name, {}).get("type")
        if expected == "string" and not isinstance(value, str):
            raise TypeError(f"{name} must be a string")
        if expected == "boolean" and not isinstance(value, bool):
            raise TypeError(f"{name} must be a boolean")
        if expected == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
            raise TypeError(f"{name} must be an integer")


def _value(args: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in args:
            return args[name]
    return None


def _course_code(args: dict[str, Any]) -> str:
    direct = _value(args, "course_code", "module_code", "module_ref", "course_ref")
    if direct is not None:
        return str(direct).split("::", 1)[0]
    subject = _value(args, "subject_area", "department_code")
    number = _value(args, "catalog_number", "course_number")
    if subject is not None and number is not None:
        return f"{subject}-{number}"
    section = _value(args, "section_code", "section_ref", "class_ref")
    if section is not None:
        return str(section).split("::", 1)[0]
    raise SandboxStateError("No course identifier was provided.")


def _term_id(args: dict[str, Any]) -> str:
    direct = _value(args, "term_id", "semester", "period_id", "term_ref", "period_ref")
    if direct is not None:
        return str(direct)
    section = _value(args, "section_code", "section_ref", "class_ref")
    if section is not None and "::" in str(section):
        return str(section).split("::", 1)[1]
    raise SandboxStateError("No term identifier was provided.")


def _student_id(args: dict[str, Any]) -> str:
    value = _value(args, "student_id", "learner_ref", "student_ref", "learner_id")
    if value is None:
        raise SandboxStateError("No learner identifier was provided.")
    return str(value)


def _room_code(args: dict[str, Any]) -> str:
    value = _value(args, "room_code", "facility_ref", "room_ref")
    if value is None:
        raise SandboxStateError("No room identifier was provided.")
    return str(value)


def _assessment_id(args: dict[str, Any]) -> str:
    value = _value(args, "assessment_id", "assessment_ref", "evaluation_id")
    if value is None:
        raise SandboxStateError("No assessment identifier was provided.")
    return str(value)


def _invoice_id(args: dict[str, Any]) -> str:
    value = _value(args, "invoice_id", "billing_ref", "invoice_ref")
    if value is None:
        raise SandboxStateError("No invoice identifier was provided.")
    return str(value)


def _course(store: Gate07SandboxStore, args: dict[str, Any]) -> dict[str, Any]:
    code = _course_code(args)
    try:
        return store.courses[code]
    except KeyError as exc:
        raise SandboxStateError(f"Unknown course {code!r}.") from exc


def _student(store: Gate07SandboxStore, args: dict[str, Any]) -> dict[str, Any]:
    student_id = _student_id(args)
    try:
        return store.students[student_id]
    except KeyError as exc:
        raise SandboxStateError(f"Unknown student {student_id!r}.") from exc


def _schedule(store: Gate07SandboxStore, args: dict[str, Any]) -> dict[str, Any]:
    key = f"{_course_code(args)}|{_term_id(args)}"
    try:
        return store.schedules[key]
    except KeyError as exc:
        raise SandboxStateError(f"No schedule for {key!r}.") from exc


def _course_view(course: dict[str, Any]) -> dict[str, Any]:
    return {
        "course_code": course["course_code"],
        "title": course["title"],
        "credits": course["credits"],
        "department": course["department"],
    }


def _create_record(
    store: Gate07SandboxStore,
    collection: dict[str, dict[str, Any]],
    prefix: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    record_id = store.next_id(prefix)
    collection[record_id] = {"record_id": record_id, **payload}
    return {"record_id": record_id, "status": "created"}


def _execute_mutation(store: Gate07SandboxStore, definition: ToolDefinition, args: dict[str, Any]) -> dict[str, Any]:
    operation = definition.operation
    for acknowledgment in ("consent_ack", "honor_code", "payment_ack"):
        if acknowledgment in args and args[acknowledgment] is not True:
            raise SandboxStateError(f"{acknowledgment} must be true.")
    if "approval_status" in args and args["approval_status"] != "approved":
        raise SandboxStateError("approval_status must be 'approved'.")
    if operation == "enrollment":
        course = _course(store, args)
        student = _student(store, args)
        if course["seats_available"] <= 0:
            raise SandboxStateError("No seats available.")
        course["seats_available"] -= 1
        record_id = store.next_id("ENR")
        store.enrollments[record_id] = {
            "enrollment_id": record_id,
            "student_id": student["student_id"],
            "course_code": course["course_code"],
            "term_id": _term_id(args),
            "status": "enrolled",
        }
        return {"enrollment_id": record_id, "status": "enrolled"}
    if operation == "enrollment_replacement":
        if args.get("payment_status") != "paid":
            raise SandboxStateError("payment_status must be 'paid'.")
        course = _course(store, args)
        student = _student(store, args)
        if course["seats_available"] <= 0:
            raise SandboxStateError("No seats available.")
        course["seats_available"] -= 1
        record_id = store.next_id("REG")
        store.enrollments[record_id] = {
            "registration_id": record_id,
            "learner_ref": student["student_id"],
            "section_code": f"{course['course_code']}::{_term_id(args)}",
            "status": "registered",
        }
        return {"registration_id": record_id, "status": "registered"}
    if operation == "assessment_submit":
        student = _student(store, args)
        if "honor_code" in args and args["honor_code"] is not True:
            raise SandboxStateError("honor_code must be true.")
        assessment_id = _assessment_id(args)
        if assessment_id not in store.assessments:
            raise SandboxStateError(f"Unknown assessment {assessment_id!r}.")
        return _create_record(
            store,
            store.submissions,
            "SUB",
            {"student_id": student["student_id"], "assessment_id": assessment_id, "status": "submitted"},
        )
    if operation == "payment":
        invoice_id = _invoice_id(args)
        if invoice_id not in store.invoices:
            raise SandboxStateError(f"Unknown invoice {invoice_id!r}.")
        store.invoices[invoice_id]["status"] = "paid"
        return {"payment_id": store.next_id("PAY"), "status": "paid"}
    if operation == "credential":
        student = _student(store, args)
        credential_id = store.next_id("CRD")
        store.credentials[credential_id] = {"credential_id": credential_id, "student_id": student["student_id"], "status": "issued"}
        return {"credential_id": credential_id, "status": "issued"}
    if operation == "reservation":
        room = _room_code(args)
        if room not in store.rooms:
            raise SandboxStateError(f"Unknown room {room!r}.")
        booking_id = store.next_id("RSV")
        store.reservations[booking_id] = {"booking_id": booking_id, "room_code": room, "status": "reserved"}
        return {"booking_id": booking_id, "status": "reserved"}
    if operation == "request_only":
        student = _student(store, args)
        return _create_record(store, store.requests, "REQ", {"student_id": student["student_id"], "status": "requested"})
    raise SandboxStateError(f"Unsupported mutation operation {operation!r}.")


def execute_operation(store: Gate07SandboxStore, definition: ToolDefinition, args: dict[str, Any]) -> dict[str, Any]:
    """Execute one real contract-backed operation against live sandbox state."""
    _required_args(definition, args)
    operation = definition.operation
    if operation in {"enrollment", "enrollment_replacement", "assessment_submit", "payment", "credential", "reservation", "request_only"}:
        return _execute_mutation(store, definition, args)
    if operation in {"course_lookup", "exact_course_lookup"}:
        return _course_view(_course(store, args))
    if operation == "student_lookup":
        return dict(_student(store, args))
    if operation == "room_lookup":
        code = _room_code(args)
        try:
            return dict(store.rooms[code])
        except KeyError as exc:
            raise SandboxStateError(f"Unknown room {code!r}.") from exc
    if operation == "program_lookup":
        student = _student(store, args)
        return {"program_code": student["program_code"], "status": "active"}
    if operation == "eligibility":
        course = _course(store, args)
        student = _student(store, args)
        eligible = course["program_code"] == student["program_code"] or course["credits"] <= 3
        return {"eligible": eligible, "reason": "program_match" if eligible else "program_mismatch"}
    if operation == "attendance":
        student = _student(store, args)
        _course(store, args)
        return {"student_id": student["student_id"], "attended": True, "status": "recorded"}
    if operation == "schedule":
        schedule = _schedule(store, args)
        return {"day": schedule["day"], "start_time": schedule["start_time"], "room_code": schedule["room_code"]}
    if operation == "nested_schedule":
        schedule = _schedule(store, args)
        return {"schedule": {"day": schedule["day"], "start_time": schedule["start_time"], "location": {"room": schedule["room_code"]}}}
    if operation == "transcript":
        student = _student(store, args)
        return {"student_id": student["student_id"], "courses": [], "standing": "good"}
    if operation == "nested_transcript":
        student = _student(store, args)
        return {"transcript": {"student_id": student["student_id"], "courses": [], "standing": "good"}}
    if operation == "nested_course":
        return {"course": _course_view(_course(store, args))}
    if operation == "nested_student":
        return {"profile": dict(_student(store, args))}
    if operation == "grade_lookup":
        assessment_id = _assessment_id(args)
        if assessment_id not in store.assessments:
            raise SandboxStateError(f"Unknown assessment {assessment_id!r}.")
        return {"assessment_id": assessment_id, "score": 80, "released": True}
    if operation == "invoice_lookup":
        invoice_id = _invoice_id(args)
        try:
            invoice = store.invoices[invoice_id]
        except KeyError as exc:
            raise SandboxStateError(f"Unknown invoice {invoice_id!r}.") from exc
        return {"invoice_id": invoice_id, "amount": invoice["amount"], "status": invoice["status"]}
    if operation == "identity_part":
        student = _student(store, args)
        return {"student_id": student["student_id"], "display_name": student["display_name"], "status": student["status"]}
    if operation == "program_part":
        student = _student(store, args)
        return {"student_id": student["student_id"], "program_code": student["program_code"]}
    if operation == "assessment_part":
        assessment_id = _assessment_id(args)
        try:
            assessment = store.assessments[assessment_id]
        except KeyError as exc:
            raise SandboxStateError(f"Unknown assessment {assessment_id!r}.") from exc
        return {"assessment_id": assessment_id, "assessment_type": assessment["assessment_type"]}
    if operation == "course_title":
        course = _course(store, args)
        return {"course_code": course["course_code"], "title": course["title"]}
    if operation == "course_credits":
        course = _course(store, args)
        return {"course_code": course["course_code"], "credits": course["credits"]}
    if operation == "course_summary":
        return _course_view(_course(store, args))
    if operation == "invoice_summary":
        invoice_id = _invoice_id(args)
        try:
            invoice = store.invoices[invoice_id]
        except KeyError as exc:
            raise SandboxStateError(f"Unknown invoice {invoice_id!r}.") from exc
        return {"invoice_id": invoice_id, "amount": invoice["amount"], "status": invoice["status"]}
    if operation == "student_summary":
        student = _student(store, args)
        return dict(student)
    if operation == "search_decoy":
        query = _value(args, "query_text", "search_text", "keyword")
        if not isinstance(query, str) or not query.strip():
            raise SandboxStateError("Search text must be non-empty.")
        needle = query.strip().casefold()
        matches = [{"course_code": code, "title": course["title"]} for code, course in store.courses.items() if needle in course["title"].casefold() or needle in code.casefold()]
        return {"matches": matches}
    raise SandboxStateError(f"Unsupported read operation {operation!r}.")
