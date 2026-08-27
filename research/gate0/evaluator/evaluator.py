"""Deterministic task evaluator (Phase 6.6). For later Gate-0 use only --
this module runs no model and makes no scientific claim.

Every outcome here is computed by pure set arithmetic and real sandbox
execution against the hidden ground truth -- never an LLM call, never a
heuristic confidence score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from research.gate0.drift import build_case_manifest
from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate0.oracle import get_ground_truth
from research.gate0.sandbox import EducationSandboxStore, SandboxStateError, build_api

NO_EQUIVALENT = "NO_EQUIVALENT"


@dataclass(frozen=True)
class ProposedMapping:
    case_id: str
    predicted_new_tool_name: str | None
    predicted_argument_mapping: dict[str, str | tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class MappingEvaluationResult:
    case_id: str
    family: str
    no_equivalent_expected: bool
    no_equivalent_predicted: bool
    no_equivalent_correct: bool
    tool_selection_correct: bool
    argument_pairs_expected: frozenset[tuple[str, str]]
    argument_pairs_predicted: frozenset[tuple[str, str]]
    argument_pairs_correct: frozenset[tuple[str, str]]
    argument_pairs_missed: frozenset[tuple[str, str]]
    argument_pairs_spurious: frozenset[tuple[str, str]]
    argument_precision: float
    argument_recall: float
    effect_kind_expected: str | None
    effect_kind_matches_new_contract: bool | None
    overall_correct: bool
    failure_reasons: tuple[str, ...]


@dataclass(frozen=True)
class AdaptedCallResult:
    case_id: str
    attempted_tool_name: str
    outcome: str  # "succeeded" | "precondition_failed" | "malformed_call" | "wrong_tool"
    output: dict[str, Any] | None
    output_expectation_met: bool | None
    error: str | None


def _case_by_id(case_id: str):
    for case in build_case_manifest():
        if case.case_id == case_id:
            return case
    raise KeyError(f"No manifest case {case_id!r}.")


def _is_no_equivalent_marker(value: str | None) -> bool:
    return value is None or value == NO_EQUIVALENT


def _expand_pairs(mapping: dict[str, str | tuple[str, ...]]) -> frozenset[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for old_arg, new_args in mapping.items():
        if isinstance(new_args, str):
            new_args = (new_args,)
        for new_arg in new_args:
            pairs.add((old_arg, new_arg))
    return frozenset(pairs)


def _resolve_real_contract(version: str, tool_name: str):
    for contract in build_api(version, EducationSandboxStore()).contracts():
        if contract.name == tool_name:
            return contract
    return None


def evaluate_mapping(proposed: ProposedMapping, capability: EvaluatorCapability) -> MappingEvaluationResult:
    if not isinstance(capability, EvaluatorCapability):
        raise PermissionError("evaluate_mapping requires a real EvaluatorCapability instance.")

    case = _case_by_id(proposed.case_id)
    gt = get_ground_truth(proposed.case_id, capability)

    # Internal consistency guard: the ground truth must agree with the real,
    # currently-defined sandbox contracts -- never a hand-drifted string.
    if gt.correct_new_tool_id is not None:
        real = _resolve_real_contract(case.new_version, gt.correct_new_tool_name or "")
        assert real is not None and real.tool_id == gt.correct_new_tool_id, (
            f"{proposed.case_id}: ground truth disagrees with the live sandbox contract."
        )

    no_equivalent_expected = gt.correct_new_tool_name is None
    no_equivalent_predicted = _is_no_equivalent_marker(proposed.predicted_new_tool_name)
    no_equivalent_correct = no_equivalent_expected == no_equivalent_predicted

    if no_equivalent_expected:
        tool_selection_correct = no_equivalent_predicted
    else:
        tool_selection_correct = (not no_equivalent_predicted) and proposed.predicted_new_tool_name == gt.correct_new_tool_name

    expected_pairs = _expand_pairs(gt.argument_mapping)
    predicted_pairs = _expand_pairs(proposed.predicted_argument_mapping) if not no_equivalent_expected else frozenset()
    correct_pairs = expected_pairs & predicted_pairs
    missed_pairs = expected_pairs - predicted_pairs
    spurious_pairs = predicted_pairs - expected_pairs

    precision = (len(correct_pairs) / len(predicted_pairs)) if predicted_pairs else (1.0 if not expected_pairs else 0.0)
    recall = (len(correct_pairs) / len(expected_pairs)) if expected_pairs else 1.0

    effect_matches: bool | None = None
    if tool_selection_correct and not no_equivalent_expected and gt.expected_effect_kind is not None:
        real_contract = _resolve_real_contract(case.new_version, gt.correct_new_tool_name)
        effect_matches = real_contract is not None and gt.expected_effect_kind in {e.kind for e in real_contract.effects}

    failure_reasons: list[str] = []
    if not no_equivalent_correct:
        failure_reasons.append("false_no_equivalent" if no_equivalent_predicted else "missed_no_equivalent")
    elif not tool_selection_correct:
        failure_reasons.append("wrong_tool_selected")
    for old_arg, new_arg in sorted(missed_pairs):
        failure_reasons.append(f"argument_pair_missed:{old_arg}->{new_arg}")
    for old_arg, new_arg in sorted(spurious_pairs):
        failure_reasons.append(f"argument_pair_spurious:{old_arg}->{new_arg}")
    if effect_matches is False:
        failure_reasons.append("effect_kind_mismatch")

    overall_correct = (
        no_equivalent_correct
        and tool_selection_correct
        and not missed_pairs
        and not spurious_pairs
        and effect_matches is not False
    )

    return MappingEvaluationResult(
        case_id=proposed.case_id,
        family=case.family,
        no_equivalent_expected=no_equivalent_expected,
        no_equivalent_predicted=no_equivalent_predicted,
        no_equivalent_correct=no_equivalent_correct,
        tool_selection_correct=tool_selection_correct,
        argument_pairs_expected=expected_pairs,
        argument_pairs_predicted=predicted_pairs,
        argument_pairs_correct=correct_pairs,
        argument_pairs_missed=missed_pairs,
        argument_pairs_spurious=spurious_pairs,
        argument_precision=precision,
        argument_recall=recall,
        effect_kind_expected=gt.expected_effect_kind,
        effect_kind_matches_new_contract=effect_matches,
        overall_correct=overall_correct,
        failure_reasons=tuple(failure_reasons),
    )


def evaluate_adapted_call(
    case_id: str,
    attempted_tool_name: str,
    attempted_kwargs: dict[str, Any],
    capability: EvaluatorCapability,
) -> AdaptedCallResult:
    """Actually attempt the predicted call against a fresh sandbox and score it."""
    if not isinstance(capability, EvaluatorCapability):
        raise PermissionError("evaluate_adapted_call requires a real EvaluatorCapability instance.")

    case = _case_by_id(case_id)
    gt = get_ground_truth(case_id, capability)

    if gt.correct_new_tool_name is None:
        # No-equivalent case: the only "correct" adapted call is none at all.
        return AdaptedCallResult(
            case_id=case_id,
            attempted_tool_name=attempted_tool_name,
            outcome="wrong_tool",
            output=None,
            output_expectation_met=False,
            error="This case has no valid new-version tool; any attempted call is incorrect.",
        )

    store = EducationSandboxStore()
    api = build_api(case.new_version, store)
    real_contract = _resolve_real_contract(case.new_version, attempted_tool_name)
    if real_contract is None:
        return AdaptedCallResult(
            case_id=case_id,
            attempted_tool_name=attempted_tool_name,
            outcome="wrong_tool",
            output=None,
            output_expectation_met=None,
            error=f"{attempted_tool_name!r} is not a real {case.new_version} tool.",
        )

    try:
        output = getattr(api, attempted_tool_name)(**attempted_kwargs)
    except SandboxStateError as exc:
        return AdaptedCallResult(
            case_id=case_id,
            attempted_tool_name=attempted_tool_name,
            outcome="precondition_failed",
            output=None,
            output_expectation_met=None,
            error=str(exc),
        )
    except TypeError as exc:
        return AdaptedCallResult(
            case_id=case_id,
            attempted_tool_name=attempted_tool_name,
            outcome="malformed_call",
            output=None,
            output_expectation_met=None,
            error=str(exc),
        )

    required_output_fields = set(real_contract.output_schema.get("required", []))
    output_expectation_met = required_output_fields <= set(output.keys())
    outcome = "succeeded" if attempted_tool_name == gt.correct_new_tool_name else "wrong_tool"
    return AdaptedCallResult(
        case_id=case_id,
        attempted_tool_name=attempted_tool_name,
        outcome=outcome,
        output=output,
        output_expectation_met=output_expectation_met,
        error=None,
    )
