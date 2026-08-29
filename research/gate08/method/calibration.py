"""Phase 8.5 -- confidence and the three-way verdict.

This module only *applies* thresholds. Fitting them is an evaluator-lane job and
lives in `research/gate08/runner/calibrate.py`, so nothing under `method/` ever
needs the oracle.
"""

from __future__ import annotations

from dataclasses import dataclass

from research.gate08.method.models import CorrespondenceScore


# Frozen confidence weights. Recorded in GATE_08_PROTOCOL.json.
CONFIDENCE_WEIGHTS = {"top": 0.5, "margin": 0.3, "completeness": 0.2}

# The grids the fitter is allowed to search. Fixed before any fitting run.
RETRIEVAL_FLOOR_GRID = tuple(round(0.30 + 0.05 * step, 2) for step in range(13))
ABSTAIN_COVERAGE_TARGET = 0.30


@dataclass(frozen=True)
class Thresholds:
    retrieval_floor: float
    abstain_floor: float

    def to_record(self) -> dict[str, float]:
        return {"retrieval_floor": self.retrieval_floor, "abstain_floor": self.abstain_floor}


def confidence(
    ranked: tuple[CorrespondenceScore, ...],
    *,
    required_field_count: int,
    resolved_field_count: int,
) -> float:
    if not ranked:
        return 0.0
    top = ranked[0].total
    second = ranked[1].total if len(ranked) > 1 else 0.0
    margin = max(0.0, min(1.0, top - second))
    completeness = 1.0 if required_field_count == 0 else resolved_field_count / required_field_count
    value = (
        CONFIDENCE_WEIGHTS["top"] * top
        + CONFIDENCE_WEIGHTS["margin"] * margin
        + CONFIDENCE_WEIGHTS["completeness"] * completeness
    )
    return round(max(0.0, min(1.0, value)), 10)


def verdict(
    ranked: tuple[CorrespondenceScore, ...],
    score: float,
    thresholds: Thresholds,
    *,
    calibration_enabled: bool = True,
) -> str:
    """Return ALIGN, NO_EQUIVALENT, or ABSTAIN.

    With calibration disabled -- the `no calibration` ablation -- the method
    always aligns to its top candidate and can never decline.
    """
    if not ranked:
        return "NO_EQUIVALENT" if calibration_enabled else "ALIGN"
    if not calibration_enabled:
        return "ALIGN"
    if ranked[0].total < thresholds.retrieval_floor:
        return "NO_EQUIVALENT"
    if score < thresholds.abstain_floor:
        return "ABSTAIN"
    return "ALIGN"


__all__ = [
    "ABSTAIN_COVERAGE_TARGET",
    "CONFIDENCE_WEIGHTS",
    "RETRIEVAL_FLOOR_GRID",
    "Thresholds",
    "confidence",
    "verdict",
]
