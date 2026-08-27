"""Build and serialize the deterministic Gate 07 dataset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from research.gate07.dataset.models import FAMILY_NAMES, Gate07Case
from research.gate07.dataset.operators import build_case, case_requests


def build_all_cases() -> tuple[Gate07Case, ...]:
    cases = tuple(build_case(request) for request in case_requests())
    _validate_dataset(cases)
    return cases


def build_graded_cases() -> tuple[Gate07Case, ...]:
    return tuple(case for case in build_all_cases() if not case.held_out)


def build_held_out_cases() -> tuple[Gate07Case, ...]:
    return tuple(case for case in build_all_cases() if case.held_out)


def _validate_dataset(cases: Iterable[Gate07Case]) -> None:
    materialized = tuple(cases)
    if len(materialized) != 216:
        raise AssertionError(f"Expected 216 total cases, got {len(materialized)}")
    if len({case.case_id for case in materialized}) != len(materialized):
        raise AssertionError("Case ids are not unique.")
    if len({case.signature() for case in materialized}) != len(materialized):
        raise AssertionError("Generated cases contain duplicate task signatures.")
    for family in FAMILY_NAMES:
        graded = [case for case in materialized if case.family == family and not case.held_out]
        held_out = [case for case in materialized if case.family == family and case.held_out]
        if len(graded) != 15 or len(held_out) != 3:
            raise AssertionError(f"Family {family!r} has {len(graded)} graded and {len(held_out)} held-out cases.")
    if {case.case_id for case in materialized if case.held_out} & {case.case_id for case in materialized if not case.held_out}:
        raise AssertionError("Held-out and graded case ids overlap.")


def write_manifests(cases: tuple[Gate07Case, ...], output_dir: str | Path) -> tuple[Path, Path]:
    """Write reproducibility metadata and a redacted public manifest."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / "frozen_manifest.json"
    public_path = directory / "public_manifest.json"
    manifest_path.write_text(_canonical_json([case.manifest_record() for case in cases]), encoding="utf-8")
    public_path.write_text(_canonical_json([case.public_record() for case in cases if not case.held_out]), encoding="utf-8")
    return manifest_path, public_path


def load_manifest(path: str | Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
