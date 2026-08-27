"""Gate 07 raw artifact retention tests."""

from __future__ import annotations

import json
from pathlib import Path

from research.gate07.baselines.models import RawOutputRecord
from research.gate07.runner import RawArtifactWriter


def test_gate07_raw_writer_is_append_only(tmp_path: Path):
    path = tmp_path / "raw.jsonl"
    writer = RawArtifactWriter(path)
    first = RawOutputRecord("arm", "model", "case-1", "prompt-1", "rendered", "raw-1", "mock", 1.0)
    second = RawOutputRecord("arm", "model", "case-2", "prompt-1", "rendered", "raw-2", "mock", 2.0)
    writer.append(first)
    writer.append(second)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["case_id"] for row in rows] == ["case-1", "case-2"]
    assert rows[0]["raw_response"] == "raw-1"


def test_gate07_raw_artifacts_are_ignored_but_gitignore_is_trackable():
    path = Path(__file__).parents[1] / "gates" / "artifacts" / ".gitignore"
    assert path.exists()
    assert "*" in path.read_text(encoding="utf-8")
