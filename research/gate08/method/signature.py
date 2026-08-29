"""Phase 8.1 -- render, parse, and validate one intent signature.

The model supplies the abstraction only. Concrete values observed in verified
old traces are attached here, deterministically, so that no observed value ever
depends on the model transcribing it correctly.
"""

from __future__ import annotations

import json
import re
from typing import Any

from research.gate08.method.models import (
    EFFECT_KINDS,
    OPERATION_KINDS,
    PART_POSITIONS,
    VALUE_SHAPES,
    ArgumentSemantics,
    IntentSignature,
)
from research.gate08.method.prompts import NEW_SIDE_PROMPT, OLD_SIDE_PROMPTS


class SignatureParseError(ValueError):
    """Raised when a model response is not a usable signature."""


# One separator run between two non-empty parts. Used to expose a composite
# value shape without deciding, here, whether a split is warranted.
_COMPOSITE = re.compile(r"^(?P<prefix>[A-Za-z0-9]+)(?P<delimiter>[^A-Za-z0-9]+)(?P<suffix>.+)$")

_CONCEPT_SUFFIXES = ("_id", "_ref", "_code", "_key", "_number", "_name")


def _encode(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


def render_old_signature_prompt(variant: str, task: dict[str, Any]) -> tuple[str, str]:
    template = OLD_SIDE_PROMPTS[variant]
    text = template["text"].format(
        task_description=task.get("task_description", ""),
        old_contracts=_encode(task.get("old_contracts", [])),
        verified_old_traces=_encode(task.get("verified_old_traces", [])),
    )
    return template["prompt_id"], text


def render_new_signature_prompt(contract: dict[str, Any]) -> tuple[str, str]:
    return NEW_SIDE_PROMPT["prompt_id"], NEW_SIDE_PROMPT["text"].format(new_contract=_encode(contract))


def normalize_concept(value: str) -> str:
    """Reduce a field name or model concept to a bare lowercase noun."""
    text = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    for suffix in _CONCEPT_SUFFIXES:
        if text.endswith(suffix) and len(text) > len(suffix):
            text = text[: -len(suffix)]
            break
    return text.strip("_") or "unknown"


def split_composite(value: Any) -> tuple[str, str, str] | None:
    """Return (prefix, delimiter, suffix) when a value is separator-composite."""
    if not isinstance(value, str):
        return None
    match = _COMPOSITE.match(value)
    if match is None:
        return None
    return match.group("prefix"), match.group("delimiter"), match.group("suffix")


def _require_str(payload: dict[str, Any], key: str, *, allow_none: bool = False) -> str | None:
    value = payload.get(key)
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value.strip():
        raise SignatureParseError(f"{key} must be a non-empty string")
    return value.strip()


def _parse_effects(value: Any) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, list):
        raise SignatureParseError("effects must be a list")
    effects: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            raise SignatureParseError("effect entry must be an object")
        kind = item.get("kind")
        target = item.get("target_concept")
        if kind not in EFFECT_KINDS:
            raise SignatureParseError(f"unknown effect kind: {kind!r}")
        if not isinstance(target, str) or not target.strip():
            raise SignatureParseError("effect target_concept must be a non-empty string")
        effects.append((kind, normalize_concept(target)))
    return tuple(effects)


def _parse_arguments(value: Any, *, allowed_fields: frozenset[str] | None) -> tuple[ArgumentSemantics, ...]:
    if not isinstance(value, list):
        raise SignatureParseError("arguments must be a list")
    seen: set[str] = set()
    arguments: list[ArgumentSemantics] = []
    for item in value:
        if not isinstance(item, dict):
            raise SignatureParseError("argument entry must be an object")
        name = _require_str(item, "name")
        assert name is not None
        if allowed_fields is not None and name not in allowed_fields:
            raise SignatureParseError(f"argument {name!r} is not a field of the supplied schema")
        if name in seen:
            raise SignatureParseError(f"duplicate argument {name!r}")
        seen.add(name)
        concept = normalize_concept(_require_str(item, "concept") or name)
        shape = item.get("value_shape")
        if shape not in VALUE_SHAPES:
            raise SignatureParseError(f"unknown value_shape: {shape!r}")
        required = item.get("required", True)
        if not isinstance(required, bool):
            raise SignatureParseError("argument required must be boolean")
        part_of = item.get("part_of")
        if part_of is not None and (not isinstance(part_of, str) or not part_of.strip()):
            raise SignatureParseError("part_of must be a non-empty string or null")
        position = item.get("part_position")
        if position is not None and position not in PART_POSITIONS:
            raise SignatureParseError(f"unknown part_position: {position!r}")
        components = item.get("components", [])
        if not isinstance(components, list) or any(not isinstance(entry, str) or not entry.strip() for entry in components):
            raise SignatureParseError("components must be a list of non-empty strings")
        arguments.append(
            ArgumentSemantics(
                name=name,
                concept=concept,
                value_shape=shape,
                required=required,
                part_of=normalize_concept(part_of) if part_of else None,
                part_position=position,
                components=tuple(normalize_concept(entry) for entry in components),
                stated_literal=item.get("stated_literal"),
            )
        )
    return tuple(arguments)


def parse_signature(
    payload: Any,
    *,
    side: str,
    tool_name: str,
    precondition_targets: tuple[str, ...],
    allowed_fields: frozenset[str] | None,
) -> IntentSignature:
    if not isinstance(payload, dict):
        raise SignatureParseError("response is not a JSON object")
    operation = payload.get("operation")
    if operation not in OPERATION_KINDS:
        raise SignatureParseError(f"unknown operation: {operation!r}")
    primary = _require_str(payload, "primary_entity")
    assert primary is not None
    target = _require_str(payload, "target_entity", allow_none=True)
    outputs = payload.get("output_semantics", [])
    if not isinstance(outputs, list) or any(not isinstance(entry, str) or not entry.strip() for entry in outputs):
        raise SignatureParseError("output_semantics must be a list of non-empty strings")
    return IntentSignature(
        side=side,
        tool_name=tool_name,
        operation=operation,
        primary_entity=normalize_concept(primary),
        target_entity=normalize_concept(target) if target else None,
        precondition_targets=precondition_targets,
        effects=_parse_effects(payload.get("effects", [])),
        arguments=_parse_arguments(payload.get("arguments", []), allowed_fields=allowed_fields),
        output_semantics=tuple(normalize_concept(entry) for entry in outputs),
    )


def attach_observed_values(signature: IntentSignature, traces: list[dict[str, Any]]) -> IntentSignature:
    """Attach the exact trace value and any separator for each old argument."""
    observed: dict[str, Any] = {}
    for trace in traces:
        if trace.get("tool_name") != signature.tool_name:
            continue
        for key, value in (trace.get("normalized_input") or {}).items():
            observed.setdefault(key, value)
    arguments = []
    for argument in signature.arguments:
        value = observed.get(argument.name)
        parts = split_composite(value)
        arguments.append(
            ArgumentSemantics(
                name=argument.name,
                concept=argument.concept,
                value_shape=argument.value_shape,
                required=argument.required,
                part_of=argument.part_of,
                part_position=argument.part_position,
                components=argument.components,
                stated_literal=argument.stated_literal,
                observed_value=value,
                observed_delimiter=parts[1] if parts else None,
            )
        )
    return IntentSignature(
        side=signature.side,
        tool_name=signature.tool_name,
        operation=signature.operation,
        primary_entity=signature.primary_entity,
        target_entity=signature.target_entity,
        precondition_targets=signature.precondition_targets,
        effects=signature.effects,
        arguments=tuple(arguments),
        output_semantics=signature.output_semantics,
    )


def literal_signature(contract: dict[str, Any], *, side: str) -> IntentSignature:
    """The `no intent abstraction` ablation: field names used as their own concepts.

    Nothing here is abstracted. It exists so the rest of the pipeline can be run
    with the abstraction stage removed rather than with a different pipeline.
    """
    schema = contract.get("input_schema", {}) or {}
    properties = schema.get("properties", {}) or {}
    required = set(schema.get("required", []) or [])
    arguments = tuple(
        ArgumentSemantics(
            name=name,
            concept=str(name).strip().lower(),
            value_shape="other",
            required=name in required,
        )
        for name in sorted(properties)
    )
    effects = tuple(
        (effect.get("kind"), str(effect.get("target", "")).strip().lower())
        for effect in contract.get("effects", []) or []
        if effect.get("kind") in EFFECT_KINDS
    )
    return IntentSignature(
        side=side,
        tool_name=contract.get("name", ""),
        operation="other",
        primary_entity=str(contract.get("name", "")).strip().lower(),
        target_entity=None,
        precondition_targets=tuple(
            str(pre.get("target", "")) for pre in contract.get("preconditions", []) or []
        ),
        effects=effects,
        arguments=arguments,
        output_semantics=tuple(sorted((contract.get("output_schema", {}) or {}).get("properties", {}) or {})),
    )


def precondition_targets(contract: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(pre.get("target", "")) for pre in contract.get("preconditions", []) or [])


def schema_fields(contract: dict[str, Any]) -> frozenset[str]:
    return frozenset((contract.get("input_schema", {}) or {}).get("properties", {}) or {})


def required_fields(contract: dict[str, Any]) -> tuple[str, ...]:
    return tuple((contract.get("input_schema", {}) or {}).get("required", []) or [])


__all__ = [
    "SignatureParseError",
    "attach_observed_values",
    "literal_signature",
    "normalize_concept",
    "parse_signature",
    "precondition_targets",
    "render_new_signature_prompt",
    "render_old_signature_prompt",
    "required_fields",
    "schema_fields",
    "split_composite",
]
