"""Byte-stable v3 dataset regeneration checks."""

from __future__ import annotations

import json
from pathlib import Path

from research.gate07.dataset.generator import build_all_cases, write_manifests
from research.gate07.harness.serialization import write_public_tasks


def test_gate07_v3_manifests_and_public_tasks_are_byte_stable(tmp_path: Path):
    first_cases = build_all_cases()
    build_all_cases.cache_clear()
    second_cases = build_all_cases()
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_manifest, first_public = write_manifests(first_cases, first)
    second_manifest, second_public = write_manifests(second_cases, second)
    first_tasks = write_public_tasks(first_cases, first / "public_tasks.json")
    second_tasks = write_public_tasks(second_cases, second / "public_tasks.json")
    assert first_manifest.read_bytes() == second_manifest.read_bytes()
    assert first_public.read_bytes() == second_public.read_bytes()
    assert first_tasks.read_bytes() == second_tasks.read_bytes()
    assert len(first_cases) == len(second_cases) == 216
    assert len(json.loads(first_tasks.read_text(encoding="utf-8"))) == 180
