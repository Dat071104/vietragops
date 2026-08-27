"""The only task surface exposed to a Gate 07 baseline arm."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from research.gate0.contracts import PublicToolContract

from research.gate07.dataset.models import Gate07Case
from research.gate07.sandbox.api import build_api
from research.gate07.sandbox.store import Gate07SandboxStore, SandboxStateError
from research.gate07.traces.capture import capture_old_traces
from research.gate07.traces.models import PublicVerifiedTrace


@dataclass(frozen=True)
class MethodFacingTask:
    case_id: str
    old_version: str
    new_version: str
    old_tool_names: tuple[str, ...]
    candidate_new_tool_names: tuple[str, ...]
    task_description: str
    old_contracts: tuple[PublicToolContract, ...]
    new_contracts: tuple[PublicToolContract, ...]
    verified_old_traces: tuple[PublicVerifiedTrace, ...]


class MethodFacingHarness:
    """Expose redacted contracts, verified old traces, and safe calls."""

    def __init__(self, case: Gate07Case) -> None:
        self._case = case
        self._old_api = build_api(case.old_version, Gate07SandboxStore())
        self._new_api = build_api(case.new_version, Gate07SandboxStore())

    def task(self) -> MethodFacingTask:
        old_contracts = tuple(self._public_contract(name, self._old_api) for name in self._case.old_tool_names)
        new_contracts = tuple(self._public_contract(name, self._new_api) for name in self._case.candidate_new_tool_names)
        return MethodFacingTask(
            case_id=self._case.case_id,
            old_version=self._case.old_version,
            new_version=self._case.new_version,
            old_tool_names=self._case.old_tool_names,
            candidate_new_tool_names=self._case.candidate_new_tool_names,
            task_description=self._case.task_description,
            old_contracts=old_contracts,
            new_contracts=new_contracts,
            verified_old_traces=capture_old_traces(self._case),
        )

    def call_old_tool(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        if tool_name not in self._case.old_tool_names:
            raise SandboxStateError(f"Tool {tool_name!r} is not public for this task.")
        return self._old_api.call(tool_name, **kwargs)

    def call_new_tool(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        if tool_name not in self._case.candidate_new_tool_names:
            raise SandboxStateError(f"Tool {tool_name!r} is not a candidate for this task.")
        return self._new_api.call(tool_name, **kwargs)

    @staticmethod
    def _public_contract(tool_name: str, api) -> PublicToolContract:
        for contract in api.contracts():
            if contract.name == tool_name:
                return contract.to_public() if hasattr(contract, "to_public") else contract
        raise SandboxStateError(f"Unknown public tool {tool_name!r}.")


def build_method_facing_task(case: Gate07Case) -> MethodFacingTask:
    return MethodFacingHarness(case).task()
