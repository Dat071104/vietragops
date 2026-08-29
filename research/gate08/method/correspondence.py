"""Phases 8.2 and 8.3 -- candidate retrieval and correspondence scoring.

Both stages are fully deterministic functions of two signatures that were
produced independently of one another. Nothing here reads a raw contract, a
trace, a family label, or a case id, so a score cannot encode a correspondence
that the abstraction stage did not already expose.
"""

from __future__ import annotations

from research.gate08.method.models import CorrespondenceScore, IntentSignature
from research.gate08.method.signature import normalize_concept


# Frozen before the headline run. Recorded in GATE_08_PROTOCOL.json.
DIMENSION_WEIGHTS = {
    "operation": 0.25,
    "entity": 0.25,
    "effect": 0.25,
    "precondition": 0.10,
    "output": 0.15,
}

_MUTATING = frozenset({"creates_resource", "mutates_field", "deletes_resource"})
_MUTATING_OPERATIONS = frozenset({"create", "update", "delete", "record"})


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _concepts(signature: IntentSignature) -> frozenset[str]:
    values = {argument.concept for argument in signature.arguments}
    values |= {component for argument in signature.arguments for component in argument.components}
    values |= {argument.part_of for argument in signature.arguments if argument.part_of}
    return frozenset(values)


def _entity_terms(signature: IntentSignature) -> frozenset[str]:
    terms = {signature.primary_entity}
    if signature.target_entity:
        terms.add(signature.target_entity)
    return frozenset(terms)


def score_operation(old: IntentSignature, new: IntentSignature) -> float:
    if old.operation == new.operation:
        return 1.0
    old_mutating = old.operation in _MUTATING_OPERATIONS
    new_mutating = new.operation in _MUTATING_OPERATIONS
    return 0.5 if old_mutating == new_mutating else 0.0


def score_entity(old: IntentSignature, new: IntentSignature) -> float:
    old_terms = _entity_terms(old)
    new_terms = _entity_terms(new)
    if old_terms & new_terms:
        return 1.0
    if (old_terms & _concepts(new)) or (new_terms & _concepts(old)):
        return 0.6
    return _jaccard(_concepts(old), _concepts(new))


def score_effect(old: IntentSignature, new: IntentSignature) -> float:
    old_kinds = frozenset(kind for kind, _ in old.effects)
    new_kinds = frozenset(kind for kind, _ in new.effects)
    if not old_kinds and not new_kinds:
        return 0.5
    if bool(old_kinds & _MUTATING) != bool(new_kinds & _MUTATING):
        return 0.0
    if old_kinds != new_kinds:
        return 0.4
    old_targets = frozenset(target for _, target in old.effects)
    new_targets = frozenset(target for _, target in new.effects)
    return 1.0 if old_targets & new_targets else 0.6


def score_precondition(old: IntentSignature, new: IntentSignature) -> float:
    old_targets = frozenset(normalize_concept(target) for target in old.precondition_targets)
    new_targets = frozenset(normalize_concept(target) for target in new.precondition_targets)
    return _jaccard(old_targets, new_targets)


def score_output(old: IntentSignature, new: IntentSignature) -> float:
    return _jaccard(frozenset(old.output_semantics), frozenset(new.output_semantics))


def score_candidate(old: IntentSignature, new: IntentSignature) -> CorrespondenceScore:
    operation = score_operation(old, new)
    entity = score_entity(old, new)
    effect = score_effect(old, new)
    precondition = score_precondition(old, new)
    output = score_output(old, new)
    total = (
        DIMENSION_WEIGHTS["operation"] * operation
        + DIMENSION_WEIGHTS["entity"] * entity
        + DIMENSION_WEIGHTS["effect"] * effect
        + DIMENSION_WEIGHTS["precondition"] * precondition
        + DIMENSION_WEIGHTS["output"] * output
    )
    return CorrespondenceScore(
        tool_name=new.tool_name,
        operation=operation,
        entity=entity,
        effect=effect,
        precondition=precondition,
        output=output,
        total=round(total, 10),
    )


def rank_candidates(
    old: IntentSignature,
    candidates: dict[str, IntentSignature],
) -> tuple[CorrespondenceScore, ...]:
    """Rank every candidate. Order is by score, then name -- never by position."""
    scores = [score_candidate(old, candidates[name]) for name in sorted(candidates)]
    return tuple(sorted(scores, key=lambda score: (-score.total, score.tool_name)))


def retrieve(
    old: IntentSignature,
    candidates: dict[str, IntentSignature],
    *,
    floor: float,
) -> tuple[tuple[CorrespondenceScore, ...], tuple[str, ...]]:
    """Return the full ranking and the names that clear the retrieval floor.

    The retained set may be empty. Retrieval never promotes a best-of-a-bad-set
    candidate simply because it ranked first.
    """
    ranked = rank_candidates(old, candidates)
    retained = tuple(score.tool_name for score in ranked if score.total >= floor)
    return ranked, retained


__all__ = [
    "DIMENSION_WEIGHTS",
    "rank_candidates",
    "retrieve",
    "score_candidate",
    "score_effect",
    "score_entity",
    "score_operation",
    "score_output",
    "score_precondition",
]
