"""Source authority and recency scoring helpers."""

from __future__ import annotations

import csv
from datetime import datetime
import re
from pathlib import Path
from typing import Any


SOURCE_PRIORITY_MAP = {
    "official": 1.00,
    "faculty": 0.90,
    "student_guide": 0.85,
    "announcement": 0.70,
    "derived": 0.40,
    "manual_review": 0.40,
}


def load_manifest_rows(path: str | Path) -> dict[str, dict[str, str]]:
    manifest_path = Path(path)
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row["doc_id"]: row for row in rows}


def source_authority_score(chunk: Any) -> float:
    domain = getattr(chunk, "domain", "")
    authority_level = getattr(chunk, "authority_level", "")
    if domain in SOURCE_PRIORITY_MAP:
        return SOURCE_PRIORITY_MAP[domain]
    return SOURCE_PRIORITY_MAP.get(authority_level, 0.40)


def recency_score(chunk: Any, manifest_row: dict[str, str] | None) -> float:
    if manifest_row is None:
        year = infer_year_from_text(f"{getattr(chunk, 'doc_id', '')} {getattr(chunk, 'title', '')}")
        return year_to_score(year)

    year = None
    for key in ("published_at", "crawled_at"):
        if manifest_row.get(key):
            year = parse_year(manifest_row[key])
            if year is not None:
                break
    if year is None:
        year = infer_year_from_text(
            " ".join(
                [
                    manifest_row.get("doc_id", ""),
                    manifest_row.get("title", ""),
                    getattr(chunk, "doc_id", ""),
                    getattr(chunk, "title", ""),
                ]
            )
        )
    return year_to_score(year)


def parse_year(raw_value: str) -> int | None:
    try:
        return datetime.fromisoformat(raw_value).year
    except ValueError:
        return infer_year_from_text(raw_value)


def infer_year_from_text(raw_value: str) -> int | None:
    match = re.search(r"(20\d{2})", raw_value or "")
    if not match:
        return None
    return int(match.group(1))


def year_to_score(year: int | None) -> float:
    if year is None:
        return 0.5
    if year >= 2025:
        return 1.0
    if year >= 2023:
        return 0.9
    if year >= 2021:
        return 0.8
    if year >= 2019:
        return 0.7
    if year >= 2017:
        return 0.6
    return 0.5
