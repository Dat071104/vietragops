"""Atomic live-state swap: replace one document's rows in the live manifest
CSV and its chunks in the live chunks JSONL, or remove them entirely.

Both files are fully rebuilt in memory and written with
`storage.write_bytes_atomic`, so each individual file transitions from fully
old to fully new in one `os.replace`. A reader in flight during a swap always
sees one complete generation of each file, never a mix.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from rag.chunking.metadata_builder import json_dumps
from rag.lifecycle.storage import write_bytes_atomic


MANIFEST_FIELDNAMES = [
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
]


def read_manifest_rows(manifest_path: Path) -> list[dict]:
    if not manifest_path.exists():
        return []
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _render_manifest(rows: list[dict]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=MANIFEST_FIELDNAMES)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in MANIFEST_FIELDNAMES})
    return buffer.getvalue().encode("utf-8")


def read_chunk_lines(chunks_path: Path) -> list[str]:
    if not chunks_path.exists():
        return []
    return [line for line in chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _render_chunks(lines: list[str]) -> bytes:
    text = "".join(line + "\n" for line in lines)
    return text.encode("utf-8")


def apply_live_state(
    *,
    manifest_path: Path,
    chunks_path: Path,
    document_id: str,
    manifest_row: dict | None,
    chunk_records: list[dict],
) -> None:
    """Replace `document_id`'s live rows/chunks, or remove them if manifest_row is None.

    Writes the manifest first, then the chunks. Each write is independently
    atomic; a crash between the two leaves the manifest referencing a doc_id
    whose chunk count is momentarily stale (0 or the old count) rather than
    ever exposing a half-written file. The next successful publish/retire/
    rollback call always rebuilds both from registry state, so this is safe
    to retry.
    """
    rows = [row for row in read_manifest_rows(manifest_path) if row.get("doc_id") != document_id]
    if manifest_row is not None:
        rows.append(manifest_row)
    write_bytes_atomic(manifest_path, _render_manifest(rows))

    lines = [line for line in read_chunk_lines(chunks_path) if json.loads(line).get("doc_id") != document_id]
    lines.extend(json_dumps(chunk) for chunk in chunk_records)
    write_bytes_atomic(chunks_path, _render_chunks(lines))
