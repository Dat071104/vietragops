"""Verified old successful traces (Phase 6.5).

Traces are captured by actually executing sandbox tools against a real,
freshly-reset store -- never hand-authored. Replaying a trace's
`normalized_input` against the same tool at the same point in a fresh
sequence must reproduce the same output and `state_hash_after`
(`tests/test_gate06_traces.py` proves this).
"""

from __future__ import annotations

from research.gate0.sandbox import EducationSandboxStore, SandboxStateError, build_api
from research.gate0.traces.models import VerifiedTrace

_V1_SEQUENCE: tuple[tuple[str, dict], ...] = (
    ("search_course", {"course_code": "CRS-101"}),
    ("check_prerequisite", {"student_program": "PROG-CS", "course_code": "CRS-201"}),
    ("create_enrollment", {"student_id": "STU-0002", "course_code": "CRS-301", "semester": "TERM-2026A"}),
    ("get_timetable", {"course_code": "CRS-201", "semester": "TERM-2026A"}),
)

_V2_SEQUENCE: tuple[tuple[str, dict], ...] = (
    ("find_module", {"course_code": "CRS-101"}),
    ("check_prerequisite", {"program_code": "PROG-CS", "module_code": "CRS-201"}),
    (
        "create_enrollment",
        {"student_id": "STU-0002", "course_code": "CRS-301", "semester": "TERM-2026A", "consent_ack": True},
    ),
    ("get_timetable", {"course_code": "CRS-201", "semester": "TERM-2026A"}),
)

_SEQUENCES: dict[str, tuple[tuple[str, dict], ...]] = {"v1": _V1_SEQUENCE, "v2": _V2_SEQUENCE}

_FAILING_CALL: dict[str, tuple[str, dict]] = {
    "v1": ("create_enrollment", {"student_id": "STU-0001", "course_code": "CRS-201", "semester": "TERM-2026A"}),
    "v2": (
        "create_enrollment",
        {"student_id": "STU-0001", "course_code": "CRS-201", "semester": "TERM-2026A", "consent_ack": True},
    ),
}


def _contract_for(api, tool_name: str):
    return next(c for c in api.contracts() if c.name == tool_name)


def build_verified_traces_for_version(version: str) -> tuple[VerifiedTrace, ...]:
    """Run the fixed, real call sequence for `version` on one fresh store."""
    store = EducationSandboxStore()
    api = build_api(version, store)
    traces: list[VerifiedTrace] = []
    for sequence, (tool_name, kwargs) in enumerate(_SEQUENCES[version], start=1):
        contract = _contract_for(api, tool_name)
        state_hash_before = store.state_hash()
        output = getattr(api, tool_name)(**kwargs)
        state_hash_after = store.state_hash()
        traces.append(
            VerifiedTrace(
                trace_id=f"TRACE-{version}-{sequence:06d}",
                tool_id=contract.tool_id,
                tool_name=tool_name,
                version=version,
                schema_hash=contract.schema_hash,
                normalized_input=dict(kwargs),
                precondition_outcome="satisfied",
                output=output,
                state_hash_before=state_hash_before,
                state_hash_after=state_hash_after,
                sequence=sequence,
                verified=True,
                error=None,
            )
        )
    return tuple(traces)


def build_failed_trace_for_version(version: str) -> VerifiedTrace:
    """One deliberately-failing call (precondition violated), captured honestly as `verified=False`."""
    store = EducationSandboxStore()
    api = build_api(version, store)
    tool_name, kwargs = _FAILING_CALL[version]
    contract = _contract_for(api, tool_name)
    state_hash_before = store.state_hash()
    try:
        getattr(api, tool_name)(**kwargs)
    except SandboxStateError as exc:
        return VerifiedTrace(
            trace_id=f"TRACE-{version}-FAILED",
            tool_id=contract.tool_id,
            tool_name=tool_name,
            version=version,
            schema_hash=contract.schema_hash,
            normalized_input=dict(kwargs),
            precondition_outcome="violated",
            output=None,
            state_hash_before=state_hash_before,
            state_hash_after=store.state_hash(),
            sequence=0,
            verified=False,
            error=str(exc),
        )
    raise AssertionError(f"Expected {tool_name} to fail its precondition for the fixed failing-trace call.")


def replay_trace(version: str, trace: VerifiedTrace, store: EducationSandboxStore) -> dict:
    """Re-execute exactly what a trace recorded, against the given (already-positioned) store."""
    api = build_api(version, store)
    return getattr(api, trace.tool_name)(**trace.normalized_input)
