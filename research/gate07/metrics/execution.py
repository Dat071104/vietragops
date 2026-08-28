"""First-attempt execution scoring from supplied V4 values and transforms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.dataset.models import Gate07Case
from research.gate07.oracle.ground_truth import get_ground_truth
from research.gate07.sandbox.api import build_api
from research.gate07.sandbox.store import Gate07SandboxStore, SandboxStateError


@dataclass(frozen=True)
class FirstAttemptResult:
    case_id: str
    outcome: str
    attempted_tool_names: tuple[str, ...]
    attempted_inputs: tuple[dict[str, Any], ...]
    error: str | None = None


def _trace_value(task: dict[str, Any], old_tool: str, old_arg: str) -> Any:
    for trace in task.get("verified_old_traces", []):
        if trace.get("tool_name") == old_tool:
            return trace.get("normalized_input", {}).get(old_arg)
    return None


def _mapping_entries(prediction: dict[str, Any]) -> list[dict[str, Any]]:
    raw_mapping = prediction.get("argument_mapping")
    if isinstance(raw_mapping, list):
        entries: list[dict[str, Any]] = []
        for item in raw_mapping:
            if not isinstance(item, dict):
                continue
            if not all(isinstance(item.get(key), str) for key in ("old_tool", "old_arg", "new_tool", "new_arg")):
                continue
            transform = item.get("value_transform")
            entries.append({**item, "value_transform": transform if isinstance(transform, dict) else {"kind": "identity"}})
        return entries
    entries = []
    for pair in prediction.get("argument_pairs", []):
        if isinstance(pair, (list, tuple)) and len(pair) == 4 and all(isinstance(value, str) for value in pair):
            entries.append(
                {
                    "old_tool": pair[0],
                    "old_arg": pair[1],
                    "new_tool": pair[2],
                    "new_arg": pair[3],
                    "value_transform": {"kind": "identity"},
                }
            )
    return entries


def _constructed_values(prediction: dict[str, Any], tool_name: str) -> dict[str, Any]:
    values = prediction.get("constructed_argument_values", [])
    if isinstance(values, dict):
        candidate = values.get(tool_name)
        return dict(candidate) if isinstance(candidate, dict) else {}
    if not isinstance(values, list):
        return {}
    for item in values:
        if isinstance(item, dict) and item.get("new_tool") == tool_name and isinstance(item.get("arguments"), dict):
            return dict(item["arguments"])
    return {}


def _apply_transform(value: Any, transform: dict[str, Any]) -> tuple[bool, Any, str | None]:
    kind = transform.get("kind")
    if kind == "identity":
        return value is not None, value, None if value is not None else "source value is unavailable"
    if kind == "literal":
        return "value" in transform, transform.get("value"), None if "value" in transform else "literal transform has no value"
    if kind == "split":
        delimiter = transform.get("delimiter")
        part = transform.get("part")
        if value is None:
            return False, None, "source value is unavailable"
        if not isinstance(delimiter, str) or not delimiter or part not in {"prefix", "suffix"}:
            return False, None, "split transform is malformed"
        pieces = str(value).split(delimiter, 1)
        if len(pieces) != 2:
            return False, None, "split delimiter is absent from source value"
        return True, pieces[0] if part == "prefix" else pieces[1], None
    if kind == "join":
        return value is not None, value, None if value is not None else "source value is unavailable"
    return False, None, "unsupported value transform"


def _adapt_input(task: dict[str, Any], tool_name: str, prediction: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any] | None:
    """Build exactly the arguments supplied by the prediction.

    No split or merge is inferred here. A prediction must provide an explicit
    transform or a literal value for every required field.
    """
    entries = [entry for entry in _mapping_entries(prediction) if entry["new_tool"] == tool_name]
    constructed = _constructed_values(prediction, tool_name)
    result: dict[str, Any] = {}
    required_fields = contract.get("input_schema", {}).get("required", [])
    for field in required_fields:
        field_entries = [entry for entry in entries if entry["new_arg"] == field]
        if field_entries:
            kinds = {entry["value_transform"].get("kind") for entry in field_entries}
            if kinds == {"join"}:
                ordered = sorted(field_entries, key=lambda entry: entry["value_transform"].get("order", -1))
                orders = [entry["value_transform"].get("order") for entry in ordered]
                delimiter = ordered[0]["value_transform"].get("delimiter")
                if orders != list(range(len(orders))) or any(entry["value_transform"].get("delimiter") != delimiter for entry in ordered):
                    return None
                values: list[str] = []
                for entry in ordered:
                    source = _trace_value(task, entry["old_tool"], entry["old_arg"])
                    ok, value, _error = _apply_transform(source, entry["value_transform"])
                    if not ok:
                        return None
                    values.append(str(value))
                result[field] = str(delimiter).join(values)
                continue
            if len(field_entries) != 1:
                return None
            entry = field_entries[0]
            source = _trace_value(task, entry["old_tool"], entry["old_arg"])
            ok, value, _error = _apply_transform(source, entry["value_transform"])
            if not ok:
                return None
            result[field] = value
        elif field in constructed:
            result[field] = constructed[field]
        else:
            return None
    return result


def _selected_tools(prediction: dict[str, Any]) -> tuple[str, ...]:
    if "best_candidate_tool_names" in prediction:
        return tuple(prediction.get("best_candidate_tool_names", []))
    return tuple(prediction.get("selected_tool_names", [])) if not prediction.get("abstain", False) else ()


def evaluate_first_attempt(case: Gate07Case, task: dict[str, Any], prediction: dict[str, Any], capability: EvaluatorCapability) -> FirstAttemptResult:
    if not isinstance(capability, EvaluatorCapability):
        raise PermissionError("evaluate_first_attempt requires a real EvaluatorCapability instance.")
    truth = get_ground_truth(case.case_id, capability)
    selected = _selected_tools(prediction)
    if not truth.correct_new_tool_names and not selected:
        return FirstAttemptResult(case.case_id, "succeeded", (), ())
    if not selected:
        return FirstAttemptResult(case.case_id, "malformed_call", (), (), "no selected tool for an equivalent task")
    contracts = {contract["name"]: contract for contract in task.get("new_contracts", [])}
    api = build_api(case.new_version, Gate07SandboxStore())
    expected_inputs = dict(zip(truth.correct_new_tool_names, case.new_inputs))
    attempted_inputs: list[dict[str, Any]] = []
    for tool_name in selected:
        contract = contracts.get(tool_name)
        if contract is None:
            return FirstAttemptResult(case.case_id, "wrong_tool", selected, tuple(attempted_inputs), f"{tool_name!r} is not a public candidate")
        args = _adapt_input(task, tool_name, prediction, contract)
        if args is None:
            return FirstAttemptResult(case.case_id, "malformed_call", selected, tuple(attempted_inputs), f"could not fill required arguments for {tool_name!r} from supplied values/transforms")
        attempted_inputs.append(args)
        try:
            api.call(tool_name, **args)
        except SandboxStateError as exc:
            return FirstAttemptResult(case.case_id, "precondition_failed", selected, tuple(attempted_inputs), str(exc))
        except TypeError as exc:
            return FirstAttemptResult(case.case_id, "malformed_call", selected, tuple(attempted_inputs), str(exc))
        if tool_name not in expected_inputs:
            return FirstAttemptResult(case.case_id, "wrong_tool", selected, tuple(attempted_inputs), f"{tool_name!r} is not an expected tool")
        if args != expected_inputs[tool_name]:
            return FirstAttemptResult(case.case_id, "wrong_arguments", selected, tuple(attempted_inputs), f"supplied arguments for {tool_name!r} differ from the frozen expected values")
    outcome = "succeeded" if set(selected) == set(truth.correct_new_tool_names) else "wrong_tool"
    return FirstAttemptResult(case.case_id, outcome, selected, tuple(attempted_inputs))
