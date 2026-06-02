"""Validation checks for the Phase 1 document manifest."""

from __future__ import annotations

import csv
import hashlib
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = {
    "doc_id",
    "title",
    "source_url",
    "source_type",
    "domain",
    "authority_level",
    "language",
    "published_at",
    "crawled_at",
    "file_path",
    "checksum",
    "status",
    "notes",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python scripts/verify_manifest.py data/manifests/documents_manifest.csv")
        return 2

    manifest_path = (ROOT / argv[1]).resolve()
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            print(f"Missing columns: {sorted(missing)}", file=sys.stderr)
            return 1
        rows = list(reader)

    if len(rows) < 30:
        print(f"Expected at least 30 rows, found {len(rows)}", file=sys.stderr)
        return 1

    checksum_counter = Counter()
    problems = []

    for row in rows:
        for column in ("doc_id", "title", "source_url", "file_path", "checksum", "authority_level", "status"):
            if not row.get(column):
                problems.append(f"{row.get('doc_id', '<missing doc_id>')}: empty {column}")

        source_url = row["source_url"]
        if not source_url.startswith("http"):
            problems.append(f"{row['doc_id']}: invalid source_url {source_url}")
        if "login" in source_url.lower():
            problems.append(f"{row['doc_id']}: source URL appears login-gated")

        file_path = (ROOT / row["file_path"]).resolve()
        if not file_path.exists():
            problems.append(f"{row['doc_id']}: file missing {file_path}")
            continue

        actual_checksum = sha256_file(file_path)
        checksum_counter[actual_checksum] += 1
        if actual_checksum != row["checksum"]:
            problems.append(f"{row['doc_id']}: checksum mismatch")

    duplicate_groups = sum(1 for count in checksum_counter.values() if count > 1)
    print(f"rows={len(rows)}")
    print(f"duplicate_checksum_groups={duplicate_groups}")

    if problems:
        print("Manifest validation failed:", file=sys.stderr)
        for problem in problems:
            print(f" - {problem}", file=sys.stderr)
        return 1

    print("Manifest validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
