"""Serialize the method-facing task for offline and live runners."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from research.gate07.dataset.models import Gate07Case
from research.gate07.harness.method_facing import build_method_facing_task


def task_record(case: Gate07Case) -> dict:
    return asdict(build_method_facing_task(case))


def write_public_tasks(cases: tuple[Gate07Case, ...], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    records = [task_record(case) for case in cases if not case.held_out]
    target.write_text(json.dumps(records, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return target


def load_public_tasks(path: str | Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
