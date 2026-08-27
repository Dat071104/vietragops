"""Capture old traces by executing the real Gate 07 sandbox."""

from __future__ import annotations

from research.gate07.dataset.models import Gate07Case
from research.gate07.sandbox.api import build_api
from research.gate07.sandbox.store import Gate07SandboxStore
from research.gate07.traces.models import PublicVerifiedTrace


def capture_old_traces(case: Gate07Case) -> tuple[PublicVerifiedTrace, ...]:
    """Run every old operation for a case on a fresh deterministic store."""
    api = build_api(case.old_version, Gate07SandboxStore())
    traces: list[PublicVerifiedTrace] = []
    for sequence, (tool_name, args) in enumerate(zip(case.old_tool_names, case.old_inputs), start=1):
        before = api.store.state_hash()
        output = api.call(tool_name, **args)
        after = api.store.state_hash()
        traces.append(
            PublicVerifiedTrace(
                trace_id=f"TRACE-{case.case_id}-{sequence:02d}",
                tool_name=tool_name,
                version=case.old_version,
                normalized_input=dict(args),
                output=dict(output),
                state_hash_before=before,
                state_hash_after=after,
                sequence=sequence,
                verified=True,
            )
        )
    return tuple(traces)
