"""Frozen-seed operators that turn real sandbox contract pairs into cases."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any

from research.gate07.dataset.models import Gate07Case
from research.gate07.sandbox.api import Gate07EducationApi, build_api
from research.gate07.sandbox.catalog import Lineage, all_lineages
from research.gate07.sandbox.store import Gate07SandboxStore


GENERATOR_SEED = 20260827
GRADED_PER_FAMILY = 15
HELD_OUT_PER_FAMILY = 3


@dataclass(frozen=True)
class CaseRequest:
    family_index: int
    lineage: Lineage
    variant: int
    seed: int
    held_out: bool
    ordinal: int


def case_requests() -> tuple[CaseRequest, ...]:
    requests: list[CaseRequest] = []
    ordinal = 1
    for family_index, family in enumerate(
        ("tool_rename", "argument_rename", "multiple_simultaneous_renames", "added_required_field", "argument_split", "argument_merge", "output_restructure", "tool_replacement", "one_old_to_multiple_new", "multiple_old_to_one_new", "semantic_near_collision", "no_equivalent")
    ):
        family_lineages = [lineage for lineage in all_lineages() if lineage.family == family]
        for held_out, count in ((False, GRADED_PER_FAMILY), (True, HELD_OUT_PER_FAMILY)):
            for variant in range(count):
                lineage = family_lineages[variant % len(family_lineages)]
                seed = GENERATOR_SEED + family_index * 10000 + (variant + (100 if held_out else 0)) * 101 + family_lineages.index(lineage)
                prefix = "H" if held_out else "G"
                requests.append(CaseRequest(family_index, lineage, variant, seed, held_out, ordinal))
                ordinal += 1
    return tuple(requests)


def _resource_index(seed: int, modulus: int, offset: int = 0) -> int:
    return ((seed * 17 + offset) % modulus) + 1


def _field_value(name: str, seed: int) -> Any:
    course_number = _resource_index(seed, 30)
    student_number = _resource_index(seed, 20, 3)
    assessment_number = _resource_index(seed, 20, 5)
    invoice_number = _resource_index(seed, 20, 7)
    room_number = _resource_index(seed, 15, 11)
    if name in {"course_code", "module_code", "module_ref", "course_ref"}:
        return f"CRS-{course_number:03d}"
    if name in {"subject_area", "department_code"}:
        return "CRS"
    if name in {"catalog_number", "course_number"}:
        return f"{course_number:03d}"
    if name in {"student_id", "learner_ref", "student_ref", "learner_id"}:
        return f"STU-{student_number:04d}"
    if name in {"assessment_id", "assessment_ref", "evaluation_id"}:
        return f"ASM-{assessment_number:03d}"
    if name in {"invoice_id", "billing_ref", "invoice_ref"}:
        return f"INV-{invoice_number:03d}"
    if name in {"room_code", "facility_ref", "room_ref"}:
        return f"ROOM-{room_number:03d}"
    if name in {"term_id", "semester", "period_id", "term_ref", "period_ref"}:
        return f"TERM-{(course_number % 3) + 1:02d}"
    if name in {"section_ref", "section_code", "class_ref"}:
        return f"CRS-{course_number:03d}::TERM-{(course_number % 3) + 1:02d}"
    if name in {"session_date", "meeting_day"}:
        return f"2026-09-{(seed % 20) + 1:02d}"
    if name in {"response_text", "answer"}:
        return "synthetic response"
    if name in {"reason", "audit_reason", "review_note"}:
        return "routine review"
    if name == "source_institution":
        return "SYNTH-EXT"
    if name == "query_text":
        return "Synthetic Module"
    if name == "amount":
        return 1000 + invoice_number * 25
    if name in {"consent_ack", "honor_code", "payment_ack"}:
        return True
    if name in {"payment_status"}:
        return "paid"
    if name in {"approval_status"}:
        return "approved"
    return f"synthetic-{name}-{seed}"


def _args_for_fields(fields: tuple[tuple[str, str], ...], seed: int) -> dict[str, Any]:
    return {name: _field_value(name, seed) for name, _ in fields}


def _args_for_definition(definition: Any, seed: int) -> dict[str, Any]:
    return {name: _field_value(name, seed) for name in definition.input_schema["required"]}


def _transform_args(lineage: Lineage, old_args: tuple[dict[str, Any], ...], seed: int) -> tuple[dict[str, Any], ...]:
    if not lineage.new_names:
        return ()
    source = old_args[0]
    new_args: dict[str, Any] = {}
    for name, _ in lineage.new_fields:
        if name in source:
            new_args[name] = source[name]
    old_course = _field_value("course_code", seed)
    old_term = _field_value("term_id", seed)
    for name, _ in lineage.new_fields:
        if name in {"learner_ref", "student_ref", "learner_id"}:
            new_args[name] = source.get("student_id", _field_value(name, seed))
        elif name in {"module_ref", "course_ref"}:
            new_args[name] = source.get("course_code", old_course)
        elif name in {"subject_area", "department_code"}:
            new_args[name] = str(source.get("course_code", old_course)).split("-", 1)[0]
        elif name in {"catalog_number", "course_number"}:
            new_args[name] = str(source.get("course_code", old_course)).split("-", 1)[-1]
        elif name in {"period_ref", "term_ref"}:
            new_args[name] = source.get("term_id", old_term)
        elif name in {"section_ref", "section_code", "class_ref"}:
            new_args[name] = f"{source.get('course_code', old_course)}::{source.get('term_id', old_term)}"
        elif name == "evaluation_id":
            new_args[name] = source.get("assessment_id", _field_value(name, seed))
        elif name == "billing_ref":
            new_args[name] = source.get("invoice_id", _field_value(name, seed))
        elif name == "facility_ref":
            new_args[name] = source.get("room_code", _field_value(name, seed))
        elif name == "meeting_day":
            new_args[name] = source.get("session_date", _field_value(name, seed))
        elif name in {"consent_ack", "honor_code", "payment_ack"}:
            new_args[name] = True
        elif name == "payment_status":
            new_args[name] = "paid"
        elif name == "approval_status":
            new_args[name] = "approved"
        elif name == "review_note":
            new_args[name] = source.get("audit_reason", _field_value(name, seed))
    return tuple(dict(new_args) for _ in lineage.new_names)


def _argument_pairs(lineage: Lineage) -> tuple[tuple[str, str, str, str], ...]:
    if not lineage.new_names:
        return ()
    pairs: list[tuple[str, str, str, str]] = []
    if lineage.family == "one_old_to_multiple_new":
        for old_field, _ in lineage.old_fields:
            for new_name in lineage.new_names:
                pairs.append((lineage.old_names[0], old_field, new_name, new_field_for(old_field, lineage, new_name)))
        return tuple(pairs)
    if lineage.family == "multiple_old_to_one_new":
        for old_name in lineage.old_names:
            for old_field, _ in lineage.old_fields:
                pairs.append((old_name, old_field, lineage.new_names[0], lineage.new_fields[0][0]))
        return tuple(pairs)
    for index, (old_field, _) in enumerate(lineage.old_fields):
        if lineage.family == "argument_split" and old_field == "course_code":
            pairs.extend(((lineage.old_names[0], old_field, lineage.new_names[0], "subject_area"), (lineage.old_names[0], old_field, lineage.new_names[0], "catalog_number")))
            continue
        if lineage.family == "argument_merge":
            pairs.append((lineage.old_names[0], old_field, lineage.new_names[0], "section_ref"))
            continue
        if lineage.family == "tool_replacement":
            target = {"student_id": "learner_ref", "course_code": "section_ref", "term_id": "section_ref", "room_code": "facility_ref"}.get(old_field, old_field)
        else:
            target = lineage.new_fields[index][0] if index < len(lineage.new_fields) else old_field
        pairs.append((lineage.old_names[0], old_field, lineage.new_names[0], target))
    return tuple(pairs)


def new_field_for(old_field: str, lineage: Lineage, new_name: str) -> str:
    if lineage.key == "profile_parts":
        return "student_id"
    if lineage.key == "course_parts":
        return "course_code"
    if lineage.key == "assessment_parts":
        return "assessment_id"
    return lineage.new_fields[0][0]


def _candidate_names(lineage: Lineage, seed: int, new_api: Gate07EducationApi) -> tuple[str, ...]:
    correct = list(lineage.new_names)
    if lineage.family == "no_equivalent":
        correct = []
    pool = [definition.name for definition in new_api.definitions() if definition.name not in correct]
    if lineage.family == "semantic_near_collision":
        decoys = {"browse_course_catalog", "search_room_options", "search_learner_records"}
        prioritized = [name for name in pool if name in decoys]
        pool = prioritized + [name for name in pool if name not in decoys]
    rng = random.Random(seed)
    rng.shuffle(pool)
    return tuple(correct + pool[: max(3, 5 - len(correct))])


def _task_description(lineage: Lineage, old_args: tuple[dict[str, Any], ...], seed: int) -> str:
    if len(lineage.old_names) > 1:
        return f"The legacy interface exposes {', '.join(lineage.old_names)}. Preserve the learner-facing task represented by these operations for the synthetic record {seed}."
        return f"For the supplied synthetic record, {lineage.old_description} Choose the new interface operation or operations that preserve this task."


def _run(api: Gate07EducationApi, tool_name: str, args: dict[str, Any], role: str) -> dict[str, Any]:
    before = api.store.state_hash()
    output = api.call(tool_name, **args)
    after = api.store.state_hash()
    required = next(definition for definition in api.definitions() if definition.name == tool_name).output_schema["required"]
    if not set(required) <= set(output):
        raise AssertionError(f"{tool_name}: output misses required fields {required!r}")
    return {"role": role, "version": api.version, "tool_name": tool_name, "input": dict(args), "output": output, "state_hash_before": before, "state_hash_after": after, "succeeded": True}


def build_case(request: CaseRequest) -> Gate07Case:
    lineage = request.lineage
    old_api = build_api("v1", Gate07SandboxStore())
    new_api = build_api("v3", Gate07SandboxStore())
    old_args = tuple(_args_for_fields(lineage.old_fields, request.seed) for _ in lineage.old_names)
    new_args = _transform_args(lineage, old_args, request.seed)
    candidates = _candidate_names(lineage, request.seed, new_api)
    receipts: list[dict[str, Any]] = []
    old_probe_api = build_api("v1", Gate07SandboxStore())
    for tool_name, args in zip(lineage.old_names, old_args):
        receipts.append(_run(old_probe_api, tool_name, args, "old"))
    if new_args:
        new_probe_api = build_api("v3", Gate07SandboxStore())
        for tool_name, args in zip(lineage.new_names, new_args):
            receipts.append(_run(new_probe_api, tool_name, args, "new_correct"))
    for tool_name in candidates:
        if tool_name in lineage.new_names:
            continue
        definition = next(definition for definition in new_api.definitions() if definition.name == tool_name)
        probe_api = build_api("v3", Gate07SandboxStore())
        receipts.append(_run(probe_api, tool_name, _args_for_definition(definition, request.seed + len(tool_name)), "candidate_probe"))
    mapped_targets = {new_field for _, _, _, new_field in _argument_pairs(lineage)}
    new_required = {name for name, _ in lineage.new_fields}
    output_mapping: tuple[tuple[str, str], ...] = ()
    if lineage.family == "output_restructure":
        outer = lineage.new_outputs[0][0][0]
        output_mapping = tuple((old_name, f"{outer}.{old_name}") for old_name, _ in lineage.old_output)
    correct_definitions = [next(definition for definition in new_api.definitions() if definition.name == name) for name in lineage.new_names]
    effect_kinds = tuple(effect.kind for definition in correct_definitions for effect in definition.effects)
    return Gate07Case(
        case_id=f"G07-{'H' if request.held_out else 'G'}-{request.ordinal:04d}",
        family=lineage.family,
        seed=request.seed,
        held_out=request.held_out,
        lineage_key=lineage.key,
        old_version="v1",
        new_version="v3",
        old_tool_names=lineage.old_names,
        candidate_new_tool_names=candidates,
        task_description=_task_description(lineage, old_args, request.seed),
        old_inputs=old_args,
        new_tool_names=lineage.new_names,
        new_inputs=new_args,
        argument_pairs=_argument_pairs(lineage),
        new_only_required_fields=tuple(sorted(new_required - mapped_targets)),
        expected_effect_kinds=effect_kinds,
        output_field_mapping=output_mapping,
        execution_receipts=tuple(receipts),
    )
