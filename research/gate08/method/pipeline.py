"""The Gate 08 method, end to end, for one case.

Given one old-side signature and one signature per candidate, this produces the
pre-execution decision and a prediction payload in the Gate 07 V4 shape so that
the frozen Gate 07 scoring and execution code can consume it unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from research.gate08.method.alignment import align
from research.gate08.method.calibration import Thresholds, confidence, verdict
from research.gate08.method.correspondence import rank_candidates
from research.gate08.method.models import AlignmentDecision, IntentSignature

SELECTION_CONTRACT = "gate08_method_v1"


@dataclass(frozen=True)
class MethodConfig:
    """One arm of the Gate 08 evaluation."""

    arm_id: str
    old_variant: str = "full"
    use_intent_abstraction: bool = True
    include_preconditions_effects: bool = True
    calibration_enabled: bool = True

    def to_record(self) -> dict[str, Any]:
        return {
            "arm_id": self.arm_id,
            "old_variant": self.old_variant,
            "use_intent_abstraction": self.use_intent_abstraction,
            "include_preconditions_effects": self.include_preconditions_effects,
            "calibration_enabled": self.calibration_enabled,
        }


def _required_fields(task: dict[str, Any], tool_name: str) -> tuple[str, ...]:
    for contract in task.get("new_contracts", []):
        if contract.get("name") == tool_name:
            return tuple((contract.get("input_schema", {}) or {}).get("required", []) or [])
    return ()


def _payload(
    decision: AlignmentDecision,
    constructed: dict[str, Any],
    mapped_fields: frozenset[str],
) -> dict[str, Any]:
    if decision.verdict == "NO_EQUIVALENT":
        return {
            "best_candidate_tool_names": [],
            "selected_tool_names": [],
            "argument_mapping": [],
            "argument_pairs": [],
            "constructed_argument_values": [],
            "equivalence_verdict": "not_equivalent",
            "confidence": decision.confidence,
            "abstain": False,
            "selection_contract": SELECTION_CONTRACT,
        }
    tool_name = decision.selected_tool_names[0]
    mapping = [
        {
            "old_tool": alignment.old_tool,
            "old_arg": alignment.old_arg,
            "new_tool": alignment.new_tool,
            "new_arg": alignment.new_arg,
            "value_transform": dict(alignment.value_transform),
        }
        for alignment in decision.alignments
    ]
    literals = {name: value for name, value in constructed.items() if name not in mapped_fields}
    stated = bool(literals) or any(
        str(alignment.value_transform.get("kind")).endswith("_unresolved")
        for alignment in decision.alignments
    )
    return {
        "best_candidate_tool_names": [tool_name],
        "selected_tool_names": [tool_name],
        "argument_mapping": mapping,
        "argument_pairs": [
            [entry["old_tool"], entry["old_arg"], entry["new_tool"], entry["new_arg"]] for entry in mapping
        ],
        "constructed_argument_values": [{"new_tool": tool_name, "arguments": literals}] if literals else [],
        "equivalence_verdict": "equivalent_under_stated_convention" if stated else "equivalent",
        "confidence": decision.confidence,
        "abstain": decision.verdict == "ABSTAIN",
        "selection_contract": SELECTION_CONTRACT,
    }


def run_case(
    task: dict[str, Any],
    old_signature: IntentSignature,
    candidate_signatures: dict[str, IntentSignature],
    thresholds: Thresholds,
    config: MethodConfig,
) -> tuple[AlignmentDecision, dict[str, Any]]:
    gaps: list[str] = []
    old = old_signature if config.include_preconditions_effects else old_signature.without_preconditions_and_effects()
    candidates = {
        name: (signature if config.include_preconditions_effects else signature.without_preconditions_and_effects())
        for name, signature in candidate_signatures.items()
        if name in task.get("candidate_new_tool_names", [])
    }
    missing = [name for name in task.get("candidate_new_tool_names", []) if name not in candidates]
    if missing:
        gaps.append("no_candidate_signature")

    ranked = rank_candidates(old, candidates) if candidates else ()
    provisional = verdict(ranked, 1.0, thresholds, calibration_enabled=config.calibration_enabled)
    if provisional == "NO_EQUIVALENT" or not ranked:
        decision = AlignmentDecision(
            case_id=task["case_id"],
            verdict="NO_EQUIVALENT",
            selected_tool_names=(),
            ranked=ranked,
            alignments=(),
            unmatched_new_required=(),
            unmatched_old_arguments=tuple(argument.name for argument in old.arguments),
            confidence=confidence(ranked, required_field_count=0, resolved_field_count=0),
            evidence_gaps=tuple(gaps),
            notes={"missing_candidate_signatures": missing, "config": config.to_record()},
        )
        return decision, _payload(decision, {}, frozenset())

    selected = ranked[0].tool_name
    required = _required_fields(task, selected)
    alignments, constructed, unmatched_new, unmatched_old = align(old, candidates[selected], required)
    mapped_fields = frozenset(alignment.new_arg for alignment in alignments)
    # Coverage, not value resolution: an arm without trace rights still gets
    # its values from the executor, so completeness must not double-penalise it.
    covered = len([name for name in required if name in mapped_fields or name in constructed])
    score = confidence(ranked, required_field_count=len(required), resolved_field_count=covered)
    if unmatched_new:
        gaps.append("unmatched_required_field")
    if unmatched_old:
        gaps.append("unmatched_old_argument")
    if any(alignment.value_transform.get("kind").endswith("_unresolved") for alignment in alignments):
        gaps.append("unresolved_join_delimiter")

    final = verdict(ranked, score, thresholds, calibration_enabled=config.calibration_enabled)
    decision = AlignmentDecision(
        case_id=task["case_id"],
        verdict=final,
        selected_tool_names=() if final == "NO_EQUIVALENT" else (selected,),
        ranked=ranked,
        alignments=() if final == "NO_EQUIVALENT" else alignments,
        unmatched_new_required=unmatched_new,
        unmatched_old_arguments=unmatched_old,
        confidence=score,
        evidence_gaps=tuple(dict.fromkeys(gaps)),
        notes={"missing_candidate_signatures": missing, "config": config.to_record()},
    )
    return decision, _payload(decision, constructed, mapped_fields)


__all__ = ["MethodConfig", "SELECTION_CONTRACT", "run_case"]
