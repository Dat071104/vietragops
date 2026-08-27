"""Internal and public case records for Gate 07."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


FAMILY_NAMES = (
    "tool_rename",
    "argument_rename",
    "multiple_simultaneous_renames",
    "added_required_field",
    "argument_split",
    "argument_merge",
    "output_restructure",
    "tool_replacement",
    "one_old_to_multiple_new",
    "multiple_old_to_one_new",
    "semantic_near_collision",
    "no_equivalent",
)


@dataclass(frozen=True)
class Gate07Case:
    """A generated case; fields after ``candidate_new_tool_names`` are internal."""

    case_id: str
    family: str
    seed: int
    held_out: bool
    lineage_key: str
    old_version: str
    new_version: str
    old_tool_names: tuple[str, ...]
    candidate_new_tool_names: tuple[str, ...]
    task_description: str
    old_inputs: tuple[dict[str, Any], ...]
    new_tool_names: tuple[str, ...]
    new_inputs: tuple[dict[str, Any], ...]
    argument_pairs: tuple[tuple[str, str, str, str], ...]
    new_only_required_fields: tuple[str, ...]
    expected_effect_kinds: tuple[str, ...]
    output_field_mapping: tuple[tuple[str, str], ...]
    execution_receipts: tuple[dict[str, Any], ...]

    def public_record(self) -> dict[str, Any]:
        """Return the complete method-facing case without evaluator fields."""
        return {
            "case_id": self.case_id,
            "old_version": self.old_version,
            "new_version": self.new_version,
            "old_tool_names": list(self.old_tool_names),
            "candidate_new_tool_names": list(self.candidate_new_tool_names),
            "task_description": self.task_description,
        }

    def manifest_record(self) -> dict[str, Any]:
        """Return reproducibility metadata; ground truth lives separately."""
        return {
            "case_id": self.case_id,
            "family": self.family,
            "seed": self.seed,
            "held_out": self.held_out,
            "lineage_key": self.lineage_key,
            "old_version": self.old_version,
            "new_version": self.new_version,
            "old_tool_names": list(self.old_tool_names),
            "candidate_new_tool_names": list(self.candidate_new_tool_names),
            "task_description": self.task_description,
            "old_inputs": list(self.old_inputs),
            "execution_receipts": list(self.execution_receipts),
        }

    def signature(self) -> tuple[Any, ...]:
        """A deterministic duplicate check over task and executed pair shape."""
        return (
            self.family,
            self.old_tool_names,
            self.candidate_new_tool_names,
            self.task_description,
            tuple(tuple(sorted(value.items())) for value in self.old_inputs),
        )
