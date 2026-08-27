"""Gate 04 Phase 4.4: controlled regression fixtures, each in an isolated
tmp_path -- never the real corpus or live SQLite state.

Covers the four required scenarios: active-vs-retired exclusion (through the
real lifecycle publish/retire cycle, at the live-retrieval level, not just
the resolver's diagnostic path), conflicting official sources, a stale
source, and unchanged normal educational QA -- each proven through the real
manifest-CSV-loading code path (`load_manifest_rows`), not just synthetic
in-memory dicts.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from rag.generation.answer_generator import AnswerGenerator
from rag.generation.context_builder import ContextBuilder
from rag.generation.groq_client import GroqClient
from rag.lifecycle.registry import LifecycleRegistry
from rag.lifecycle.service import LifecycleService
from rag.retrieval import BM25Retriever, ChunkIndexStore, HybridRetriever
from rag.retrieval.source_priority import load_manifest_rows
from rag.retrieval.version_resolver import VersionResolver


MANIFEST_FIELDNAMES = [
    "doc_id", "title", "source_url", "source_type", "domain", "authority_level",
    "language", "published_at", "crawled_at", "file_path", "checksum", "status", "notes",
]


class StubGroqClient(GroqClient):
    def __init__(self) -> None:
        pass

    def available(self) -> bool:
        return False


def _make_service(tmp_path: Path) -> tuple[LifecycleService, LifecycleRegistry, Path, Path]:
    manifest_path = tmp_path / "live" / "manifest.csv"
    chunks_path = tmp_path / "live" / "chunks.jsonl"
    registry = LifecycleRegistry(tmp_path / "registry.db")
    service = LifecycleService(
        registry=registry,
        originals_dir=tmp_path / "originals",
        candidates_dir=tmp_path / "candidates",
        live_manifest_path=manifest_path,
        live_chunks_path=chunks_path,
        max_upload_bytes=1_000_000,
    )
    return service, registry, manifest_path, chunks_path


def _upload_review_publish(service: LifecycleService, filename: str, content: str) -> str:
    receiver = service.begin_intake(filename=filename, content_type="text/markdown")
    receiver.feed(content.encode("utf-8"))
    outcome = service.complete_intake(receiver, domain="student_guide", authority_level="official")
    service.review(outcome.version_id)
    service.publish(outcome.version_id)
    return outcome.version_id


def test_retired_version_excluded_from_live_retrieval_by_removal_not_reranking(tmp_path):
    """Proves exclusion is structural (the retired doc's chunks are removed
    from the live index entirely), never a silent down-rank that could
    still surface it under a different query."""
    service, registry, manifest_path, chunks_path = _make_service(tmp_path)
    markdown = "# Quy dinh hoc phi\n\nHoc phi ky nay la 15 trieu dong theo quy dinh hien hanh.\n"
    version_id = _upload_review_publish(service, "hoc-phi.md", markdown)

    store_before = ChunkIndexStore.from_jsonl(chunks_path)
    assert any(chunk.doc_id == "hoc-phi" for chunk in store_before)
    results_before = HybridRetriever(store_before).retrieve("hoc phi ky nay", top_k=5)
    assert any(result.doc_id == "hoc-phi" for result in results_before)

    service.retire(version_id)

    store_after = ChunkIndexStore.from_jsonl(chunks_path)
    assert not any(chunk.doc_id == "hoc-phi" for chunk in store_after)  # removed, not just down-ranked
    results_after = HybridRetriever(store_after).retrieve("hoc phi ky nay", top_k=5)
    assert not any(result.doc_id == "hoc-phi" for result in results_after)
    bm25_after = BM25Retriever(store_after).retrieve("hoc phi ky nay", top_k=5)
    assert not any(result.doc_id == "hoc-phi" for result in bm25_after)

    # Diagnostic path: a resolver with direct registry access still classifies
    # the retired document correctly, even though it is unreachable live.
    manifest_rows = load_manifest_rows(manifest_path) if manifest_path.exists() else {}
    resolver = VersionResolver(manifest_rows, index_version=store_after.index_version, registry=registry)
    info = resolver.resolve("hoc-phi")
    assert info.authority_state == "retired"


def _write_manifest_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = MANIFEST_FIELDNAMES + ["stale_after", "conflict_key"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _chunk_record(chunk_id: str, doc_id: str, text: str) -> dict:
    return {
        "chunk_id": chunk_id,
        "doc_id": doc_id,
        "title": doc_id,
        "source_url": f"https://example.edu/{doc_id}",
        "source_type": "html",
        "domain": "student_guide",
        "authority_level": "official",
        "heading_path": [doc_id],
        "page_start": None,
        "page_end": None,
        "section_id": f"{doc_id}_s001",
        "chunk_index": 1,
        "text": text,
    }


def _write_chunks_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")


def test_conflicting_official_sources_fixture_yields_source_conflict_via_manifest_csv(tmp_path):
    manifest_path = tmp_path / "manifest.csv"
    chunks_path = tmp_path / "chunks.jsonl"
    _write_manifest_csv(
        manifest_path,
        [
            {"doc_id": "tuition_notice_a", "checksum": "aaa111", "status": "active", "conflict_key": "tuition_2026"},
            {"doc_id": "tuition_notice_b", "checksum": "bbb222", "status": "active", "conflict_key": "tuition_2026"},
        ],
    )
    _write_chunks_jsonl(
        chunks_path,
        [
            _chunk_record("c_a", "tuition_notice_a", "Học phí học kỳ này là 15 triệu đồng theo thông báo chính thức A."),
            _chunk_record("c_b", "tuition_notice_b", "Học phí học kỳ này là 18 triệu đồng theo thông báo chính thức B."),
        ],
    )

    store = ChunkIndexStore.from_jsonl(chunks_path)
    manifest_rows = load_manifest_rows(manifest_path)
    resolver = VersionResolver(manifest_rows, index_version=store.index_version)
    generator = AnswerGenerator(
        context_builder=ContextBuilder(store, version_resolver=resolver),
        groq_client=StubGroqClient(),
    )

    response = generator.answer("Học phí học kỳ này là bao nhiêu?", top_k=2)

    assert response["refusal"] is False
    assert response["evidence_state"]["state"] == "source_conflict"
    assert response["citation_verification"]["is_valid"] is True  # quotes are still grounded


def test_stale_source_fixture_yields_stale_source_via_manifest_csv(tmp_path):
    from datetime import datetime, timezone

    manifest_path = tmp_path / "manifest.csv"
    chunks_path = tmp_path / "chunks.jsonl"
    _write_manifest_csv(
        manifest_path,
        [
            {
                "doc_id": "old_fee_notice",
                "checksum": "ccc333",
                "status": "active",
                "stale_after": "2026-01-01T00:00:00+00:00",
            }
        ],
    )
    _write_chunks_jsonl(
        chunks_path,
        [_chunk_record("c_old", "old_fee_notice", "Học phí học kỳ trước là 12 triệu đồng theo quy định cũ.")],
    )

    store = ChunkIndexStore.from_jsonl(chunks_path)
    manifest_rows = load_manifest_rows(manifest_path)
    as_of = datetime(2026, 6, 1, tzinfo=timezone.utc)
    resolver = VersionResolver(manifest_rows, index_version=store.index_version, as_of=as_of)
    generator = AnswerGenerator(
        context_builder=ContextBuilder(store, version_resolver=resolver),
        groq_client=StubGroqClient(),
    )

    response = generator.answer("Học phí học kỳ trước là bao nhiêu?")

    assert response["refusal"] is False
    assert response["evidence_state"]["state"] == "stale_source"
    assert response["citation_verification"]["is_valid"] is True


def test_normal_educational_qa_fixture_remains_supported_and_unchanged(tmp_path):
    """No stale_after/conflict_key anywhere -- mirrors the real 37-doc
    corpus's manifest shape exactly. Confirms Gate 04 wiring is a pure no-op
    for ordinary QA: same refusal/citation behavior as pre-Gate-04, with the
    new evidence_state resolving to 'supported'."""
    manifest_path = tmp_path / "manifest.csv"
    chunks_path = tmp_path / "chunks.jsonl"
    _write_manifest_csv(
        manifest_path,
        [{"doc_id": "email_doc", "checksum": "ddd444", "status": "active"}],
    )
    _write_chunks_jsonl(
        chunks_path,
        [_chunk_record("email_chunk", "email_doc", "Cấu trúc email sinh viên: MSSV@student.tdtu.edu.vn.")],
    )

    store = ChunkIndexStore.from_jsonl(chunks_path)
    manifest_rows = load_manifest_rows(manifest_path)
    resolver = VersionResolver(manifest_rows, index_version=store.index_version)
    generator = AnswerGenerator(
        context_builder=ContextBuilder(store, version_resolver=resolver),
        groq_client=StubGroqClient(),
    )
    baseline_generator = AnswerGenerator(
        context_builder=ContextBuilder(store),  # no version_resolver at all
        groq_client=StubGroqClient(),
    )

    response = generator.answer("Cấu trúc email sinh viên là gì?")
    baseline_response = baseline_generator.answer("Cấu trúc email sinh viên là gì?")

    assert response["refusal"] is False
    assert response["evidence_state"]["state"] == "supported"
    assert response["citation_verification"]["is_valid"] is True
    assert response["answer"] == baseline_response["answer"]
    assert response["citations"] == baseline_response["citations"]
    assert response["confidence"] == baseline_response["confidence"]
