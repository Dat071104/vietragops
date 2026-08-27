"""Versioned generic API over the isolated Gate 07 store."""

from __future__ import annotations

from typing import Any

from research.gate07.sandbox.catalog import build_definitions
from research.gate07.sandbox.models import ToolDefinition
from research.gate07.sandbox.operations import execute_operation
from research.gate07.sandbox.store import Gate07SandboxStore, SandboxStateError


class Gate07EducationApi:
    """A deterministic version surface whose tools execute real operations."""

    def __init__(self, version: str, store: Gate07SandboxStore) -> None:
        self.version = version
        self.store = store
        self._definitions = {definition.name: definition for definition in build_definitions(version)}

    def contracts(self) -> tuple:
        return tuple(definition.contract() for definition in self._definitions.values())

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._definitions.values())

    def call(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        try:
            definition = self._definitions[tool_name]
        except KeyError as exc:
            raise SandboxStateError(f"No such {self.version} tool: {tool_name!r}.") from exc
        return execute_operation(self.store, definition, kwargs)


def build_api(version: str, store: Gate07SandboxStore | None = None) -> Gate07EducationApi:
    return Gate07EducationApi(version, store or Gate07SandboxStore())


__all__ = ["Gate07EducationApi", "Gate07SandboxStore", "SandboxStateError", "build_api"]
