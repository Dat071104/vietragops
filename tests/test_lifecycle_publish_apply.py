from __future__ import annotations

import json

from rag.lifecycle.publish import apply_live_state, read_chunk_lines, read_manifest_rows


def _manifest_row(doc_id: str) -> dict:
    return {
        "doc_id": doc_id,
        "title": f"Title {doc_id}",
        "source_url": f"https://example.edu/{doc_id}",
        "source_type": "markdown",
        "domain": "student_guide",
        "authority_level": "official",
        "language": "",
        "published_at": "2026-08-26T00:00:00+00:00",
        "crawled_at": "",
        "file_path": f"data/lifecycle/originals/{doc_id}.md",
        "checksum": "a" * 64,
        "status": "active",
        "notes": "",
    }


def _chunk(doc_id: str, index: int) -> dict:
    return {"chunk_id": f"{doc_id}_c{index:03d}", "doc_id": doc_id, "text": f"chunk {index} of {doc_id}"}


def test_apply_live_state_adds_a_new_document(tmp_path):
    manifest_path = tmp_path / "manifest.csv"
    chunks_path = tmp_path / "chunks.jsonl"

    apply_live_state(
        manifest_path=manifest_path,
        chunks_path=chunks_path,
        document_id="doc-a",
        manifest_row=_manifest_row("doc-a"),
        chunk_records=[_chunk("doc-a", 1), _chunk("doc-a", 2)],
    )

    rows = read_manifest_rows(manifest_path)
    assert [row["doc_id"] for row in rows] == ["doc-a"]
    lines = read_chunk_lines(chunks_path)
    assert len(lines) == 2
    assert all(json.loads(line)["doc_id"] == "doc-a" for line in lines)


def test_apply_live_state_replaces_existing_document_without_touching_others(tmp_path):
    manifest_path = tmp_path / "manifest.csv"
    chunks_path = tmp_path / "chunks.jsonl"

    apply_live_state(
        manifest_path=manifest_path,
        chunks_path=chunks_path,
        document_id="doc-a",
        manifest_row=_manifest_row("doc-a"),
        chunk_records=[_chunk("doc-a", 1)],
    )
    apply_live_state(
        manifest_path=manifest_path,
        chunks_path=chunks_path,
        document_id="doc-b",
        manifest_row=_manifest_row("doc-b"),
        chunk_records=[_chunk("doc-b", 1), _chunk("doc-b", 2)],
    )

    # Publish a new version of doc-a: two chunks now, replacing the old one.
    apply_live_state(
        manifest_path=manifest_path,
        chunks_path=chunks_path,
        document_id="doc-a",
        manifest_row=_manifest_row("doc-a"),
        chunk_records=[_chunk("doc-a", 1), _chunk("doc-a", 2), _chunk("doc-a", 3)],
    )

    rows = read_manifest_rows(manifest_path)
    assert {row["doc_id"] for row in rows} == {"doc-a", "doc-b"}
    lines = read_chunk_lines(chunks_path)
    doc_a_chunks = [line for line in lines if json.loads(line)["doc_id"] == "doc-a"]
    doc_b_chunks = [line for line in lines if json.loads(line)["doc_id"] == "doc-b"]
    assert len(doc_a_chunks) == 3
    assert len(doc_b_chunks) == 2  # untouched by doc-a's republish


def test_apply_live_state_removes_a_document_when_manifest_row_is_none(tmp_path):
    manifest_path = tmp_path / "manifest.csv"
    chunks_path = tmp_path / "chunks.jsonl"

    apply_live_state(
        manifest_path=manifest_path,
        chunks_path=chunks_path,
        document_id="doc-a",
        manifest_row=_manifest_row("doc-a"),
        chunk_records=[_chunk("doc-a", 1)],
    )
    apply_live_state(
        manifest_path=manifest_path,
        chunks_path=chunks_path,
        document_id="doc-a",
        manifest_row=None,
        chunk_records=[],
    )

    assert read_manifest_rows(manifest_path) == []
    assert read_chunk_lines(chunks_path) == []


def test_apply_live_state_on_nonexistent_files_starts_from_empty(tmp_path):
    manifest_path = tmp_path / "nested" / "manifest.csv"
    chunks_path = tmp_path / "nested" / "chunks.jsonl"

    apply_live_state(
        manifest_path=manifest_path,
        chunks_path=chunks_path,
        document_id="doc-a",
        manifest_row=_manifest_row("doc-a"),
        chunk_records=[_chunk("doc-a", 1)],
    )

    assert manifest_path.exists()
    assert chunks_path.exists()
    assert len(read_manifest_rows(manifest_path)) == 1
