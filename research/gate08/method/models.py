"""Frozen method interface for the Gate 08 cross-version alignment method.

The interface is deliberately two-sided and symmetric. One signature is
abstracted from the *old* side (contract, verified traces, task description) and
one from each *new* candidate contract, and neither abstraction ever sees the
other side. Correspondence is then computed deterministically over the shared
abstract vocabulary declared here. That is the whole mechanism: no arm in this
package may map an old tool onto a new tool by looking at both at once.

`METHOD_INTERFACE_DIGEST` is recorded in `GATE_08_PROTOCOL.json` before the
headline run. Changing any vocabulary or field name below changes the digest and
therefore invalidates the freeze.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any


INTERFACE_VERSION = "gate08-method-v1"

# A generic operation vocabulary. It describes what a call does to state, not
# what domain it belongs to.
OPERATION_KINDS = (
    "create",
    "read",
    "update",
    "delete",
    "check",
    "record",
    "search",
    "other",
)

# Mirrors research/gate0/contracts EFFECT_KINDS so that an effect abstracted
# from prose can be compared with a declared contract effect.
EFFECT_KINDS = (
    "no_mutation",
    "creates_resource",
    "mutates_field",
    "deletes_resource",
)

VALUE_SHAPES = (
    "opaque_identifier",
    "composite_identifier",
    "free_text",
    "number",
    "boolean",
    "status_token",
    "date",
    "other",
)

PART_POSITIONS = ("prefix", "suffix")

VERDICTS = ("ALIGN", "NO_EQUIVALENT", "ABSTAIN")

# Reasons an alignment may be incomplete. These are recorded, never silently
# repaired, and never converted into a guessed value.
EVIDENCE_GAPS = (
    "unresolved_join_delimiter",
    "unmatched_required_field",
    "unmatched_old_argument",
    "no_candidate_signature",
    "signature_unavailable",
)


@dataclass(frozen=True)
class ArgumentSemantics:
    """One argument abstracted away from its concrete field name."""

    name: str
    concept: str
    value_shape: str
    required: bool = True
    part_of: str | None = None
    part_position: str | None = None
    components: tuple[str, ...] = ()
    stated_literal: Any = None
    observed_value: Any = None
    observed_delimiter: str | None = None

    def to_record(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "concept": self.concept,
            "value_shape": self.value_shape,
            "required": self.required,
            "part_of": self.part_of,
            "part_position": self.part_position,
            "components": list(self.components),
            "stated_literal": self.stated_literal,
            "observed_value": self.observed_value,
            "observed_delimiter": self.observed_delimiter,
        }


@dataclass(frozen=True)
class IntentSignature:
    """The abstraction produced for exactly one side of one tool."""

    side: str
    tool_name: str
    operation: str
    primary_entity: str
    target_entity: str | None
    precondition_targets: tuple[str, ...]
    effects: tuple[tuple[str, str], ...]
    arguments: tuple[ArgumentSemantics, ...]
    output_semantics: tuple[str, ...]

    def to_record(self) -> dict[str, Any]:
        return {
            "side": self.side,
            "tool_name": self.tool_name,
            "operation": self.operation,
            "primary_entity": self.primary_entity,
            "target_entity": self.target_entity,
            "precondition_targets": list(self.precondition_targets),
            "effects": [list(pair) for pair in self.effects],
            "arguments": [argument.to_record() for argument in self.arguments],
            "output_semantics": list(self.output_semantics),
        }

    def without_preconditions_and_effects(self) -> "IntentSignature":
        """The `no preconditions/effects` ablation view."""
        return IntentSignature(
            side=self.side,
            tool_name=self.tool_name,
            operation=self.operation,
            primary_entity=self.primary_entity,
            target_entity=self.target_entity,
            precondition_targets=(),
            effects=(),
            arguments=self.arguments,
            output_semantics=self.output_semantics,
        )


@dataclass(frozen=True)
class CorrespondenceScore:
    """Per-dimension equivalence estimate for one candidate."""

    tool_name: str
    operation: float
    entity: float
    effect: float
    precondition: float
    output: float
    total: float

    def to_record(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "operation": self.operation,
            "entity": self.entity,
            "effect": self.effect,
            "precondition": self.precondition,
            "output": self.output,
            "total": self.total,
        }


@dataclass(frozen=True)
class ArgumentAlignment:
    """One old argument mapped onto one new required field."""

    old_tool: str
    old_arg: str
    new_tool: str
    new_arg: str
    value_transform: dict[str, Any]
    constructed_value: Any = None
    value_resolved: bool = False

    def to_record(self) -> dict[str, Any]:
        return {
            "old_tool": self.old_tool,
            "old_arg": self.old_arg,
            "new_tool": self.new_tool,
            "new_arg": self.new_arg,
            "value_transform": dict(self.value_transform),
            "constructed_value": self.constructed_value,
            "value_resolved": self.value_resolved,
        }


@dataclass(frozen=True)
class AlignmentDecision:
    """The complete pre-execution decision for one case."""

    case_id: str
    verdict: str
    selected_tool_names: tuple[str, ...]
    ranked: tuple[CorrespondenceScore, ...]
    alignments: tuple[ArgumentAlignment, ...]
    unmatched_new_required: tuple[str, ...]
    unmatched_old_arguments: tuple[str, ...]
    confidence: float
    evidence_gaps: tuple[str, ...] = ()
    notes: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "verdict": self.verdict,
            "selected_tool_names": list(self.selected_tool_names),
            "ranked": [score.to_record() for score in self.ranked],
            "alignments": [alignment.to_record() for alignment in self.alignments],
            "unmatched_new_required": list(self.unmatched_new_required),
            "unmatched_old_arguments": list(self.unmatched_old_arguments),
            "confidence": self.confidence,
            "evidence_gaps": list(self.evidence_gaps),
            "notes": dict(self.notes),
        }


INTERFACE_SPEC = {
    "interface_version": INTERFACE_VERSION,
    "operation_kinds": list(OPERATION_KINDS),
    "effect_kinds": list(EFFECT_KINDS),
    "value_shapes": list(VALUE_SHAPES),
    "part_positions": list(PART_POSITIONS),
    "verdicts": list(VERDICTS),
    "evidence_gaps": list(EVIDENCE_GAPS),
    "argument_semantics_fields": [
        "name",
        "concept",
        "value_shape",
        "required",
        "part_of",
        "part_position",
        "components",
        "stated_literal",
        "observed_value",
        "observed_delimiter",
    ],
    "intent_signature_fields": [
        "side",
        "tool_name",
        "operation",
        "primary_entity",
        "target_entity",
        "precondition_targets",
        "effects",
        "arguments",
        "output_semantics",
    ],
    "correspondence_dimensions": ["operation", "entity", "effect", "precondition", "output"],
    "decision_fields": [
        "case_id",
        "verdict",
        "selected_tool_names",
        "ranked",
        "alignments",
        "unmatched_new_required",
        "unmatched_old_arguments",
        "confidence",
        "evidence_gaps",
    ],
}


def method_interface_digest() -> str:
    canonical = json.dumps(INTERFACE_SPEC, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


METHOD_INTERFACE_DIGEST = method_interface_digest()


__all__ = [
    "ArgumentAlignment",
    "ArgumentSemantics",
    "AlignmentDecision",
    "CorrespondenceScore",
    "EFFECT_KINDS",
    "EVIDENCE_GAPS",
    "INTERFACE_SPEC",
    "INTERFACE_VERSION",
    "IntentSignature",
    "METHOD_INTERFACE_DIGEST",
    "OPERATION_KINDS",
    "PART_POSITIONS",
    "VALUE_SHAPES",
    "VERDICTS",
    "method_interface_digest",
]
