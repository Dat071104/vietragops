"""Deterministic controls for candidate-order and random-choice priors."""

from __future__ import annotations

import hashlib
from typing import Any


CONTROL_ARM_IDS = ("positional_prior", "random_choice")


def _prediction(selected: list[str]) -> dict[str, Any]:
    return {
        "best_candidate_tool_names": selected,
        "selected_tool_names": selected,
        "argument_mapping": [],
        "argument_pairs": [],
        "value_transforms": [],
        "constructed_argument_values": [],
        "equivalence_verdict": "equivalent",
        "confidence": 0.0,
        "abstain": False,
        "selection_contract": "v4_control",
    }


def predict_positional_prior(task: dict[str, Any]) -> dict[str, Any]:
    candidates = task.get("candidate_new_tool_names", [])
    return _prediction(list(candidates[:1]))


def predict_random_choice(task: dict[str, Any]) -> dict[str, Any]:
    candidates = list(task.get("candidate_new_tool_names", []))
    if not candidates:
        return _prediction([])
    digest = hashlib.sha256(f"gate07-v4-random-choice:{task.get('case_id', '')}".encode("utf-8")).digest()
    return _prediction([candidates[int.from_bytes(digest[:8], "big") % len(candidates)]])


__all__ = ["CONTROL_ARM_IDS", "predict_positional_prior", "predict_random_choice"]
