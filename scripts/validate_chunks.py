"""Validate generated chunk JSONL files for VietRAGOps Phase 3."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


REQUIRED_FIELDS = {
    "chunk_id",
    "doc_id",
    "title",
    "source_url",
    "source_type",
    "domain",
    "authority_level",
    "heading_path",
    "page_start",
    "page_end",
    "section_id",
    "chunk_index",
    "text",
    "token_count",
    "char_start",
    "char_end",
    "checksum",
    "chunk_config",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate chunk JSONL outputs.")
    parser.add_argument("--chunks", default=None)
    parser.add_argument("--chunks-dir", default=None)
    return parser.parse_args()


def validate_chunk_file(path: str | Path) -> dict:
    chunk_path = Path(path)
    if not chunk_path.exists():
        raise FileNotFoundError(f"Chunk file not found: {chunk_path}")

    chunk_ids = set()
    rows = []
    critical_errors = []
    abnormal_chunks = []

    with chunk_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                critical_errors.append(f"line {line_number}: invalid JSON ({exc})")
                continue

            missing = REQUIRED_FIELDS - set(row)
            if missing:
                critical_errors.append(f"line {line_number}: missing fields {sorted(missing)}")
                continue

            if row["chunk_id"] in chunk_ids:
                critical_errors.append(f"line {line_number}: duplicate chunk_id {row['chunk_id']}")
            chunk_ids.add(row["chunk_id"])

            if not row["text"].strip():
                critical_errors.append(f"line {line_number}: empty text")
            if not row["doc_id"]:
                critical_errors.append(f"line {line_number}: missing doc_id")
            if not row["source_url"]:
                critical_errors.append(f"line {line_number}: missing source_url")
            if not row["heading_path"]:
                critical_errors.append(f"line {line_number}: missing heading_path")
            if not row["authority_level"]:
                critical_errors.append(f"line {line_number}: missing authority_level")
            if not row["checksum"]:
                critical_errors.append(f"line {line_number}: missing checksum")
            if row["token_count"] <= 0:
                critical_errors.append(f"line {line_number}: non-positive token_count")
            if row["char_end"] < row["char_start"]:
                critical_errors.append(f"line {line_number}: invalid char range")
            if row["source_type"] == "pdf" and row["page_start"] is None and row["page_end"] is None:
                critical_errors.append(f"line {line_number}: missing PDF page metadata")

            config = row.get("chunk_config", {})
            upper_bound = config.get("chunk_size", 0) + max(config.get("overlap", 0), 40)
            if row["token_count"] < 5 or (upper_bound and row["token_count"] > upper_bound):
                abnormal_chunks.append(row["chunk_id"])

            rows.append(row)

    duplicate_rate = 0.0
    if rows:
        unique_texts = len({row["text"] for row in rows})
        duplicate_rate = (len(rows) - unique_texts) / len(rows)

    return {
        "path": str(chunk_path),
        "rows": len(rows),
        "duplicate_rate": duplicate_rate,
        "abnormal_chunks": abnormal_chunks,
        "critical_errors": critical_errors,
    }


def validate_chunk_dir(path: str | Path) -> list[dict]:
    chunk_dir = Path(path)
    if not chunk_dir.exists():
        raise FileNotFoundError(f"Chunk directory not found: {chunk_dir}")
    files = sorted(chunk_dir.glob("chunks_*.jsonl"))
    if not files:
        raise FileNotFoundError(f"No chunk files found in {chunk_dir}")
    return [validate_chunk_file(file_path) for file_path in files]


def main() -> int:
    args = parse_args()
    if not args.chunks and not args.chunks_dir:
        print("Provide either --chunks or --chunks-dir", file=sys.stderr)
        return 2

    results = []
    if args.chunks:
        results.append(validate_chunk_file(args.chunks))
    if args.chunks_dir:
        results.extend(validate_chunk_dir(args.chunks_dir))

    has_critical = False
    for result in results:
        print(
            f"[validate_chunks] {result['path']}: rows={result['rows']} "
            f"duplicate_rate={result['duplicate_rate']:.4f} abnormal={len(result['abnormal_chunks'])}"
        )
        if result["critical_errors"]:
            has_critical = True
            for error in result["critical_errors"]:
                print(f"  - {error}", file=sys.stderr)

    return 1 if has_critical else 0


if __name__ == "__main__":
    raise SystemExit(main())
