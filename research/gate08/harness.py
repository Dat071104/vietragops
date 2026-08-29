"""The frozen Gate 08 evaluation surface.

Both splits are drawn from `build_v4_cases()` -- the same seeded candidate
permutation Gate 07 V4.1 ran on -- so a Gate 08 task and the frozen Gate 07 row
for the same case id describe the identical candidate list. Nothing here
re-generates a case.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.gate07.dataset.generator import build_v4_cases
from research.gate07.harness.serialization import task_record

# Frozen before any Gate 08 number exists. `argument_split` and
# `tool_replacement` are the two regions Gate 07 granted; `no_equivalent` is a
# safety control for abstention and false alignment and never carries a claim.
CLAIM_FAMILIES = ("argument_split", "tool_replacement")
CONTROL_FAMILIES = ("no_equivalent",)
EVAL_FAMILIES = CLAIM_FAMILIES + CONTROL_FAMILIES


def eval_cases() -> tuple:
    return tuple(
        case
        for case in build_v4_cases()
        if not case.held_out and case.family in EVAL_FAMILIES
    )


def calibration_cases() -> tuple:
    """Every held-out case. Gate 07 scored none of them."""
    return tuple(case for case in build_v4_cases() if case.held_out)


def write_tasks(cases: tuple, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    records = [task_record(case) for case in cases]
    target.write_text(
        json.dumps(records, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return target


def load_tasks(path: str | Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


__all__ = [
    "CLAIM_FAMILIES",
    "CONTROL_FAMILIES",
    "EVAL_FAMILIES",
    "calibration_cases",
    "eval_cases",
    "load_tasks",
    "write_tasks",
]
