"""Adapter for the MCPEvol-Bench evolution register.

This module only translates an external record into the input shape already
accepted by ``research.gate19.auditor``.  It deliberately does not import the
auditor or reproduce any classification rule.  A record is refused when the
external release does not supply the target-bearing expected call and the
method-visible contract surface needed to form an auditor item.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


PARAMETER_META_KEYS = {
    "parameter_additions",
    "parameter_changes",
    "parameter_removals",
}


class AdapterRefusal(ValueError):
    """Raised when a register record cannot be expressed as an auditor item."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class EvolutionRecord:
    """One tool-level record flattened from a stage file."""

    stage: int
    source_path: str
    server: str
    tool: str
    mutation_type: str
    task_idx: int | None
    record: Any

    @property
    def item_id(self) -> str:
        return f"stage{self.stage}:{self.server}:{self.tool}"


def iter_evolution_records(source_paths: Sequence[str | Path]) -> Iterable[EvolutionRecord]:
    """Yield one flattened record for each tool key in the supplied files."""

    for stage, source_path in enumerate(source_paths, start=1):
        path = Path(source_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{path} top-level value is not an object")
        for server, server_value in data.items():
            if not isinstance(server_value, dict):
                raise ValueError(f"{path}:{server} server value is not an object")
            mutation_type = server_value.get("mutation_type")
            task_idx = server_value.get("task_idx")
            for tool, record in server_value.items():
                if tool in {"mutation_type", "task_idx"}:
                    continue
                yield EvolutionRecord(
                    stage=stage,
                    source_path=path.as_posix(),
                    server=str(server),
                    tool=str(tool),
                    mutation_type=str(mutation_type),
                    task_idx=task_idx if isinstance(task_idx, int) else None,
                    record=record,
                )


def _parameter_specs(record: Any) -> list[dict[str, Any]]:
    """Extract explicitly named additions/renames; never infer from code."""

    if not isinstance(record, dict):
        return []

    specs: list[dict[str, Any]] = []
    for addition in record.get("parameter_additions", []):
        if not isinstance(addition, dict) or not isinstance(addition.get("name"), str):
            continue
        specs.append(
            {
                "kind": "add",
                "old_arg": None,
                "new_arg": addition["name"],
                "required": addition.get("required"),
            }
        )

    for change in record.get("parameter_changes", []):
        if not isinstance(change, dict):
            continue
        action = change.get("action") or change.get("change_type")
        if action == "add" and isinstance(change.get("name"), str):
            specs.append(
                {
                    "kind": "add",
                    "old_arg": None,
                    "new_arg": change["name"],
                    "required": change.get("required"),
                }
            )
        elif action == "rename":
            old_arg = change.get("old_name") or change.get("old")
            new_arg = change.get("new_name") or change.get("new")
            if isinstance(old_arg, str) and isinstance(new_arg, str):
                specs.append(
                    {
                        "kind": "rename",
                        "old_arg": old_arg,
                        "new_arg": new_arg,
                        "required": change.get("required"),
                    }
                )

    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None, str]] = set()
    for spec in specs:
        key = (spec["kind"], spec["old_arg"], spec["new_arg"])
        if key not in seen:
            seen.add(key)
            unique.append(spec)
    return unique


def _task_case_by_idx(task_cases: Any, task_idx: int | None) -> dict[str, Any] | None:
    if task_cases is None or task_idx is None:
        return None
    if isinstance(task_cases, Mapping):
        candidate = task_cases.get(task_idx, task_cases.get(str(task_idx)))
        return candidate if isinstance(candidate, dict) else None
    if isinstance(task_cases, Sequence) and not isinstance(task_cases, (str, bytes)):
        for candidate in task_cases:
            if isinstance(candidate, dict) and candidate.get("idx") == task_idx:
                return candidate
    return None


def _tool_name(call: Any) -> str | None:
    if not isinstance(call, dict):
        return None
    for key in ("tool_name", "name", "tool"):
        value = call.get(key)
        if isinstance(value, str):
            return value
    function = call.get("function")
    if isinstance(function, dict) and isinstance(function.get("name"), str):
        return function["name"]
    return None


def _call_arguments(call: Any) -> dict[str, Any] | None:
    if not isinstance(call, dict):
        return None
    for key in ("arguments", "args", "parameters", "input"):
        value = call.get(key)
        if isinstance(value, dict):
            return value
    function = call.get("function")
    if isinstance(function, dict):
        value = function.get("arguments")
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return None
            return parsed if isinstance(parsed, dict) else None
        if isinstance(value, dict):
            return value
    return None


def _visible_list(task_case: dict[str, Any], key: str) -> list[Any]:
    value = task_case.get(key, [])
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _new_fields(task_case: dict[str, Any], tool: str, new_arg: str) -> dict[str, list[str]]:
    declared = task_case.get("new_contract_fields")
    if isinstance(declared, dict):
        normalized: dict[str, list[str]] = {}
        for name, fields in declared.items():
            if isinstance(fields, list):
                normalized[str(name)] = [field for field in fields if isinstance(field, str)]
            elif isinstance(fields, str):
                normalized[str(name)] = [fields]
        if tool in normalized:
            return normalized
    # The parameter name itself is explicitly declared by the register item;
    # no other field is inferred here.
    return {tool: [new_arg]}


def _structural_refusal(record: EvolutionRecord) -> tuple[str, str]:
    if record.mutation_type != "PARAM":
        return (
            "MUTATION_TYPE_OUTSIDE_ARGUMENT_TARGET_SCHEMA",
            "DESC and TOOL records are not argument-target items for the frozen auditor.",
        )
    raw = record.record if isinstance(record.record, dict) else {}
    keys = set(raw)
    if "parameter_additions" in keys:
        additions = raw.get("parameter_additions")
        if isinstance(additions, list) and additions and all(
            isinstance(item, dict) and item.get("required") is False for item in additions
        ):
            return (
                "PARAM_OPTIONAL_ADDITION_HAS_NO_TARGET_CALL",
                "The explicit additions are optional and the register supplies no expected call containing a target value.",
            )
        return (
            "PARAM_ADDITION_HAS_NO_TARGET_CALL",
            "The register names the parameter but supplies no expected call containing its target value.",
        )
    if "parameter_removals" in keys:
        return (
            "PARAM_REMOVAL_HAS_NO_NEW_TARGET_FIELD",
            "A removal does not create a new argument target for the frozen auditor.",
        )
    if "parameter_changes" in keys:
        if "tool_description_change" in keys:
            return (
                "PARAM_COMPOSITE_CHANGE_HAS_NO_TARGET_CALL",
                "The composite parameter record has no expected call containing a target value.",
            )
        return (
            "PARAM_CHANGE_HAS_NO_TARGET_CALL",
            "The named parameter change has no expected call containing a target value.",
        )
    return (
        "PARAM_NO_ARGUMENT_TARGET",
        "The PARAM record has no explicit addition or rename that can form an auditor target.",
    )


def adapt_record(
    evolution: EvolutionRecord,
    task_cases: Any = None,
) -> list[dict[str, Any]]:
    """Convert one record to auditor items, or refuse it atomically."""

    if evolution.mutation_type != "PARAM":
        code, message = _structural_refusal(evolution)
        raise AdapterRefusal(code, message)

    specs = _parameter_specs(evolution.record)
    if not specs:
        code, message = _structural_refusal(evolution)
        raise AdapterRefusal(code, message)

    task_case = _task_case_by_idx(task_cases, evolution.task_idx)
    if task_case is None:
        raise AdapterRefusal(
            "TASK_IDX_JOIN_UNAVAILABLE",
            "No declared task_idx-to-test_cases lookup supplied; target values are not inferred from old_code/new_code.",
        )

    calls = task_case.get("tool_calls")
    if not isinstance(calls, list):
        raise AdapterRefusal(
            "EXPECTED_TOOL_CALLS_MISSING",
            "The joined test case has no list-valued tool_calls surface.",
        )

    items: list[dict[str, Any]] = []
    for spec_index, spec in enumerate(specs):
        matched = False
        for call_index, call in enumerate(calls):
            if _tool_name(call) != evolution.tool:
                continue
            arguments = _call_arguments(call)
            if arguments is None or spec["new_arg"] not in arguments:
                continue
            matched = True
            fields = _new_fields(task_case, evolution.tool, spec["new_arg"])
            if spec["new_arg"] not in fields.get(evolution.tool, []):
                raise AdapterRefusal(
                    "NEW_CONTRACT_FIELD_NOT_DECLARED",
                    "The supplied new contract field map does not declare the explicitly named new argument.",
                )
            items.append(
                {
                    "item_id": f"{evolution.item_id}:parameter_{spec_index:02d}:call_{call_index:02d}",
                    "case_id": task_case.get("case_id", task_case.get("idx")),
                    "family": task_case.get("family", "mcpevol_param"),
                    "old_tool": evolution.tool,
                    "old_arg": spec["old_arg"],
                    "new_tool": evolution.tool,
                    "new_arg": spec["new_arg"],
                    "target_value": arguments[spec["new_arg"]],
                    "source_values": list(task_case.get("visible_source_values", []))
                    if isinstance(task_case.get("visible_source_values", []), list)
                    else [],
                    "visible_source_values": list(task_case.get("visible_source_values", []))
                    if isinstance(task_case.get("visible_source_values", []), list)
                    else [],
                    "visible_text": _visible_list(task_case, "visible_text"),
                    "new_contract_fields": fields,
                    "external_record": {
                        "stage": evolution.stage,
                        "source_path": evolution.source_path,
                        "server": evolution.server,
                        "tool": evolution.tool,
                        "mutation_type": evolution.mutation_type,
                        "task_idx": evolution.task_idx,
                    },
                }
            )
        if not matched:
            raise AdapterRefusal(
                "EXPECTED_CALL_HAS_NO_NEW_ARGUMENT",
                f"No expected call for tool {evolution.tool!r} contains new argument {spec['new_arg']!r}.",
            )
    return items


def adapt_register(
    source_paths: Sequence[str | Path],
    task_cases: Any = None,
) -> dict[str, Any]:
    """Adapt all supplied records and retain a complete refusal ledger."""

    items: list[dict[str, Any]] = []
    refused: list[dict[str, Any]] = []
    input_record_count = 0
    for evolution in iter_evolution_records(source_paths):
        input_record_count += 1
        try:
            items.extend(adapt_record(evolution, task_cases=task_cases))
        except AdapterRefusal as exc:
            code, detail = _structural_refusal(evolution)
            if exc.code != "TASK_IDX_JOIN_UNAVAILABLE":
                code = exc.code
            refused.append(
                {
                    "record_id": evolution.item_id,
                    "stage": evolution.stage,
                    "source_path": evolution.source_path,
                    "server": evolution.server,
                    "tool": evolution.tool,
                    "mutation_type": evolution.mutation_type,
                    "task_idx": evolution.task_idx,
                    "record_keys": sorted(evolution.record.keys())
                    if isinstance(evolution.record, dict)
                    else [],
                    "reason_code": code,
                    "reason": str(exc),
                    "structural_detail": detail,
                }
            )
    return {
        "schema": "gate21.mcpevol_adapter_output.v1",
        "input_record_count": input_record_count,
        "converted_item_count": len(items),
        "refused_record_count": len(refused),
        "items": items,
        "refused_records": refused,
    }


def _default_source_paths(source_root: Path) -> list[Path]:
    return [
        source_root / "src/custom/data/mutation/HYBRID/evolution.json",
        source_root / "src/custom/data/mutation/HYBRID/HYBRID/evolution.json",
        source_root / "src/custom/data/mutation/HYBRID/HYBRID/HYBRID/evolution.json",
        source_root / "src/custom/data/mutation/HYBRID/HYBRID/HYBRID/HYBRID/evolution.json",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--task-cases", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    task_cases = None
    if args.task_cases:
        task_cases = json.loads(args.task_cases.read_text(encoding="utf-8"))
    result = adapt_register(_default_source_paths(args.source_root), task_cases=task_cases)
    args.output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "input_record_count": result["input_record_count"],
                "converted_item_count": result["converted_item_count"],
                "refused_record_count": result["refused_record_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
