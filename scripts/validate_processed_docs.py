"""Validate processed Phase 2 JSONL output."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REQUIRED_DOC_KEYS = {"doc_id", "title", "source_url", "source_type", "sections", "parse_status", "warnings"}
REQUIRED_SECTION_KEYS = {"section_id", "heading_path", "page", "text"}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python scripts/validate_processed_docs.py data/processed/processed_docs.jsonl")
        return 2

    path = (ROOT / argv[1]).resolve()
    if not path.exists():
        print(f"Missing processed docs file: {path}", file=sys.stderr)
        return 1

    total = 0
    success = 0
    failures: list[str] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            total += 1
            data = json.loads(raw_line)
            missing = REQUIRED_DOC_KEYS - set(data)
            if missing:
                failures.append(f"line {line_number}: missing doc keys {sorted(missing)}")
                continue
            if data["parse_status"] == "ok":
                success += 1
            for section in data["sections"]:
                missing_section = REQUIRED_SECTION_KEYS - set(section)
                if missing_section:
                    failures.append(
                        f"line {line_number}: missing section keys {sorted(missing_section)}"
                    )
                if not section["text"].strip():
                    failures.append(f"line {line_number}: empty section text")

    success_rate = (success / total) if total else 0.0
    print(f"total_docs={total}")
    print(f"success_docs={success}")
    print(f"success_rate={success_rate:.3f}")

    if success_rate < 0.9:
        failures.append("parse success rate below 0.9")

    if failures:
        print("Validation failed:", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1

    print("Processed docs validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
