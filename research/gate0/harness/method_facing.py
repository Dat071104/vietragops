"""The only interface an evaluated method is ever given (Phase 6.4).

Exposes exactly what the entry contract allows on the public side:
current and historical tool contracts for the case (redacted, no
`tool_id`), sandbox execution, and verified historical traces. This
module has no import of `research.gate0.oracle` anywhere in its source --
`tests/test_gate06_oracle_boundary.py` proves that statically (AST scan)
and proves at runtime that no method exposed here can return oracle
content.
"""

from __future__ import annotations

from dataclasses import dataclass

from research.gate0.contracts import PublicToolContract
from research.gate0.drift import DriftCase
from research.gate0.sandbox import EducationSandboxStore, SandboxStateError, build_api
from research.gate0.traces import VerifiedTrace, build_verified_traces_for_version


@dataclass(frozen=True)
class MethodFacingTask:
    case_id: str
    family: str
    old_version: str
    new_version: str
    old_tool_name: str
    candidate_new_tool_names: tuple[str, ...]
    old_contracts: tuple[PublicToolContract, ...]
    new_contracts: tuple[PublicToolContract, ...]
    verified_old_traces: tuple[VerifiedTrace, ...]


class MethodFacingHarness:
    """One case's worth of public artifacts and a live sandbox to call into."""

    def __init__(self, case: DriftCase) -> None:
        self._case = case
        self._old_store = EducationSandboxStore()
        self._new_store = EducationSandboxStore()
        self._old_api = build_api(case.old_version, self._old_store)
        self._new_api = build_api(case.new_version, self._new_store)

    def task(self) -> MethodFacingTask:
        return MethodFacingTask(
            case_id=self._case.case_id,
            family=self._case.family,
            old_version=self._case.old_version,
            new_version=self._case.new_version,
            old_tool_name=self._case.old_tool_name,
            candidate_new_tool_names=self._case.candidate_new_tool_names,
            old_contracts=tuple(c.to_public() for c in self._old_api.contracts()),
            new_contracts=tuple(c.to_public() for c in self._new_api.contracts()),
            verified_old_traces=build_verified_traces_for_version(self._case.old_version),
        )

    def call_old_tool(self, tool_name: str, **kwargs):
        return self._invoke(self._old_api, self._case.old_version, tool_name, kwargs)

    def call_new_tool(self, tool_name: str, **kwargs):
        return self._invoke(self._new_api, self._case.new_version, tool_name, kwargs)

    @staticmethod
    def _invoke(api, version: str, tool_name: str, kwargs: dict):
        public_names = {c.name for c in api.contracts()}
        if tool_name not in public_names:
            raise SandboxStateError(f"No such {version} tool: {tool_name!r}.")
        return getattr(api, tool_name)(**kwargs)

    def reset(self) -> None:
        self._old_store.reset()
        self._new_store.reset()
