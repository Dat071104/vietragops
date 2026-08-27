"""Internal tool-definition model for the Gate 07 sandbox."""

from __future__ import annotations

from dataclasses import dataclass

from research.gate0.contracts import Effect, Precondition, ToolContract


@dataclass(frozen=True)
class ToolDefinition:
    """A callable sandbox operation plus its observable contract."""

    tool_id: str
    version: str
    name: str
    description: str
    input_schema: dict
    output_schema: dict
    preconditions: tuple[Precondition, ...]
    effects: tuple[Effect, ...]
    operation: str
    lineage_key: str

    def contract(self) -> ToolContract:
        return ToolContract(
            tool_id=self.tool_id,
            version=self.version,
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            preconditions=self.preconditions,
            effects=self.effects,
        )
