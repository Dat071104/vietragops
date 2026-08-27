"""First-attempt execution scoring from public traces and a prediction."""

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


def _adapt_input(task: dict[str, Any], tool_name: str, prediction: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any] | None:
    pairs = [tuple(pair) for pair in prediction.get("argument_pairs", []) if len(pair) == 4 and pair[2] == tool_name]
    values: dict[str, list[Any]] = {}
    for old_tool, old_arg, _new_tool, new_arg in pairs:
        value = _trace_value(task, old_tool, old_arg)
        if value is not None:
            values.setdefault(new_arg, []).append(value)
    result: dict[str, Any] = {}
    for field in contract.get("input_schema", {}).get("required", []):
        candidates = values.get(field, [])
        if candidates:
            if field in {"subject_area", "catalog_number"} and "-" in str(candidates[0]):
                pieces = str(candidates[0]).split("-", 1)
                result[field] = pieces[0] if field == "subject_area" else pieces[1]
            elif field in {"section_ref", "section_code", "class_ref"} and len(candidates) >= 2:
                course = next((str(value) for value in candidates if str(value).startswith("CRS-")), str(candidates[0]))
                term = next((str(value) for value in candidates if str(value).startswith("TERM-")), str(candidates[-1]))
                result[field] = f"{course}::{term}"
            else:
                result[field] = candidates[0]
    return result if len(result) == len(contract.get("input_schema", {}).get("required", [])) else None


def evaluate_first_attempt(case: Gate07Case, task: dict[str, Any], prediction: dict[str, Any], capability: EvaluatorCapability) -> FirstAttemptResult:
    if not isinstance(capability, EvaluatorCapability):
        raise PermissionError("evaluate_first_attempt requires a real EvaluatorCapability instance.")
    truth = get_ground_truth(case.case_id, capability)
    selected = tuple(prediction.get("selected_tool_names", [])) if not prediction.get("abstain", False) else ()
    if not truth.correct_new_tool_names and not selected:
        return FirstAttemptResult(case.case_id, "succeeded", (), ())
    if not selected:
        return FirstAttemptResult(case.case_id, "malformed_call", (), (), "no selected tool for an equivalent task")
    contracts = {contract["name"]: contract for contract in task.get("new_contracts", [])}
    api = build_api(case.new_version, Gate07SandboxStore())
    attempted_inputs: list[dict[str, Any]] = []
    for tool_name in selected:
        contract = contracts.get(tool_name)
        if contract is None:
            return FirstAttemptResult(case.case_id, "wrong_tool", selected, tuple(attempted_inputs), f"{tool_name!r} is not a public candidate")
        args = _adapt_input(task, tool_name, prediction, contract)
        if args is None:
            return FirstAttemptResult(case.case_id, "malformed_call", selected, tuple(attempted_inputs), f"could not fill required arguments for {tool_name!r}")
        attempted_inputs.append(args)
        try:
            api.call(tool_name, **args)
        except SandboxStateError as exc:
            return FirstAttemptResult(case.case_id, "precondition_failed", selected, tuple(attempted_inputs), str(exc))
        except TypeError as exc:
            return FirstAttemptResult(case.case_id, "malformed_call", selected, tuple(attempted_inputs), str(exc))
    outcome = "succeeded" if set(selected) == set(truth.correct_new_tool_names) else "wrong_tool"
    return FirstAttemptResult(case.case_id, outcome, selected, tuple(attempted_inputs))
