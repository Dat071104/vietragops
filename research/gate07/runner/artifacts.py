"""Append-only raw-output retention for Gate 07 runs."""

from __future__ import annotations

import json
from pathlib import Path

from research.gate07.baselines.models import RawOutputRecord


class RawArtifactWriter:
    """Append one JSON record per arm call; never rewrites prior records."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: RawOutputRecord) -> None:
        line = json.dumps(record.to_record(), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")
