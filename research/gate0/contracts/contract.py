"""Versioned tool contract model (Gate 06, Phase 6.1).

A `ToolContract` is the full, internal representation of one callable's
shape at one version: stable identity, version, name/description, input/
output schema, structured preconditions/effects, and a deterministic
schema hash. `tool_id` is the one field that is never exposed to an
evaluated method (see `research/gate0/harness/method_facing.py`) --
leaking it would hand out the exact cross-version correspondence the
sandbox exists to hide. `to_public()` returns the redacted view that is
safe to show a method.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any

TOOL_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

PRECONDITION_KINDS = frozenset(
    {
        "field_type",
        "field_pattern",
        "enum_member",
        "resource_exists",
        "resource_absent",
        "state_flag",
    }
)

EFFECT_KINDS = frozenset(
    {
        "no_mutation",
        "creates_resource",
        "mutates_field",
        "deletes_resource",
    }
)

_MUTATING_EFFECT_KINDS = frozenset({"creates_resource", "mutates_field", "deletes_resource"})


class ContractValidationError(ValueError):
    """Raised when a `ToolContract` is malformed or internally ambiguous."""


@dataclass(frozen=True)
class Precondition:
    kind: str
    target: str
    expected: Any = None


@dataclass(frozen=True)
class Effect:
    kind: str
    target: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PublicToolContract:
    """The method-facing view of a contract. Deliberately has no `tool_id`."""

    version: str
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    preconditions: tuple[Precondition, ...]
    effects: tuple[Effect, ...]
    schema_hash: str


@dataclass(frozen=True)
class ToolContract:
    tool_id: str
    version: str
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    preconditions: tuple[Precondition, ...] = ()
    effects: tuple[Effect, ...] = ()
    schema_hash: str = field(init=False)

    def __post_init__(self) -> None:
        validate_contract(self)
        object.__setattr__(self, "schema_hash", compute_schema_hash(self))

    def to_public(self) -> PublicToolContract:
        return PublicToolContract(
            version=self.version,
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            preconditions=self.preconditions,
            effects=self.effects,
            schema_hash=self.schema_hash,
        )


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError) as exc:
        raise ContractValidationError(f"Value is not JSON-serializable: {value!r}") from exc


def compute_schema_hash(contract: ToolContract) -> str:
    """Deterministic sha256 over the observable contract surface.

    Excludes `description` (prose, not schema) and `tool_id` (identity,
    not shape) -- a rename alone changes this hash (the surface a caller
    sees changed) while the tool's stable identity does not.
    """
    payload = {
        "version": contract.version,
        "name": contract.name,
        "input_schema": contract.input_schema,
        "output_schema": contract.output_schema,
        "preconditions": [
            {"kind": p.kind, "target": p.target, "expected": p.expected} for p in contract.preconditions
        ],
        "effects": [{"kind": e.kind, "target": e.target, "detail": e.detail} for e in contract.effects],
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _validate_schema_shape(schema: dict[str, Any], *, label: str) -> None:
    if not isinstance(schema, dict):
        raise ContractValidationError(f"{label} must be a dict.")
    if schema.get("type") != "object":
        raise ContractValidationError(f"{label}.type must be 'object'.")
    properties = schema.get("properties")
    if not isinstance(properties, dict) or not properties:
        raise ContractValidationError(f"{label}.properties must be a non-empty dict.")
    for prop_name, prop_schema in properties.items():
        if not isinstance(prop_name, str) or not prop_name:
            raise ContractValidationError(f"{label}.properties has a malformed key: {prop_name!r}.")
        if not isinstance(prop_schema, dict) or "type" not in prop_schema:
            raise ContractValidationError(f"{label}.properties.{prop_name} must declare a 'type'.")
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise ContractValidationError(f"{label}.required must be a list.")
    for req_name in required:
        if req_name not in properties:
            raise ContractValidationError(f"{label}.required references unknown field {req_name!r}.")


def validate_contract(contract: ToolContract) -> None:
    if not TOOL_ID_PATTERN.match(contract.tool_id or ""):
        raise ContractValidationError(f"tool_id {contract.tool_id!r} must match {TOOL_ID_PATTERN.pattern}.")
    if not contract.version or not isinstance(contract.version, str):
        raise ContractValidationError("version must be a non-empty string.")
    if not NAME_PATTERN.match(contract.name or ""):
        raise ContractValidationError(f"name {contract.name!r} must match {NAME_PATTERN.pattern}.")
    if not contract.description or not isinstance(contract.description, str):
        raise ContractValidationError("description must be a non-empty string.")

    _validate_schema_shape(contract.input_schema, label="input_schema")
    _validate_schema_shape(contract.output_schema, label="output_schema")

    input_fields = set(contract.input_schema["properties"])

    if not isinstance(contract.preconditions, tuple):
        raise ContractValidationError("preconditions must be a tuple of Precondition.")
    for pre in contract.preconditions:
        if not isinstance(pre, Precondition):
            raise ContractValidationError(f"preconditions must contain Precondition instances, got {pre!r}.")
        if pre.kind not in PRECONDITION_KINDS:
            raise ContractValidationError(f"Unknown precondition kind {pre.kind!r}.")
        if not pre.target:
            raise ContractValidationError("Precondition.target must be non-empty.")
        if not pre.target.startswith("state:") and pre.target not in input_fields:
            raise ContractValidationError(
                f"Precondition target {pre.target!r} is neither an input field nor a 'state:'-prefixed sandbox check."
            )
        _canonical_json(pre.expected)

    if not isinstance(contract.effects, tuple):
        raise ContractValidationError("effects must be a tuple of Effect.")
    mutation_targets: dict[str, set[str]] = {}
    for eff in contract.effects:
        if not isinstance(eff, Effect):
            raise ContractValidationError(f"effects must contain Effect instances, got {eff!r}.")
        if eff.kind not in EFFECT_KINDS:
            raise ContractValidationError(f"Unknown effect kind {eff.kind!r}.")
        if not eff.target:
            raise ContractValidationError("Effect.target must be non-empty.")
        _canonical_json(eff.detail)
        mutation_targets.setdefault(eff.target, set()).add(eff.kind)

    for target, kinds in mutation_targets.items():
        if "no_mutation" in kinds and kinds & _MUTATING_EFFECT_KINDS:
            raise ContractValidationError(
                f"Effect target {target!r} declares both 'no_mutation' and a mutating effect -- ambiguous."
            )
