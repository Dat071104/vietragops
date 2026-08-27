"""Integration coverage for Gate 04 Phase 4.2: the deterministic evidence
state and the real citation-verification result flow end to end through
`AnswerGenerator`, wired to a real `ContextBuilder` + `VersionResolver`, and
the two stay independent of each other.
"""

from __future__ import annotations

from rag.generation.answer_generator import AnswerGenerator
from rag.generation.context_builder import ContextBuilder
from rag.generation.groq_client import GroqClient
from rag.retrieval import ChunkIndexStore
from rag.retrieval.version_resolver import VersionResolver


class StubGroqClient(GroqClient):
    def __init__(self) -> None:
        pass

    def available(self) -> bool:
        return False


def _chunk(chunk_id: str, doc_id: str, text: str) -> dict:
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


def _generator(records: list[dict], manifest_rows: dict[str, dict[str, str]], *, as_of=None) -> AnswerGenerator:
    store = ChunkIndexStore.from_records(records)
    resolver = VersionResolver(manifest_rows, index_version=store.index_version, as_of=as_of)
    return AnswerGenerator(
        context_builder=ContextBuilder(store, version_resolver=resolver),
        groq_client=StubGroqClient(),
    )


def test_normal_educational_qa_is_supported_and_citations_are_verified():
    generator = _generator(
        [_chunk("email_chunk", "email_doc", "Cấu trúc email sinh viên: MSSV@student.tdtu.edu.vn.")],
        {"email_doc": {"checksum": "abc123", "status": "active"}},
    )

    response = generator.answer("Cấu trúc email sinh viên là gì?")

    assert response["refusal"] is False
    assert response["evidence_state"]["state"] == "supported"
    assert response["citation_verification"]["is_valid"] is True


def test_stale_cited_source_yields_stale_source_state_with_valid_citations():
    """A grounded, correctly-quoted citation from a stale source must still
    surface stale_source -- citation grounding and evidence state are
    independent axes."""
    from datetime import datetime, timezone

    as_of = datetime(2026, 6, 1, tzinfo=timezone.utc)
    generator = _generator(
        [_chunk("fee_chunk", "fee_doc", "Học phí kỳ này là 15 triệu đồng theo quy định cũ.")],
        {"fee_doc": {"checksum": "abc123", "status": "active", "stale_after": "2026-01-01T00:00:00+00:00"}},
        as_of=as_of,
    )

    response = generator.answer("Học phí kỳ này là bao nhiêu?")

    assert response["refusal"] is False
    assert response["citation_verification"]["is_valid"] is True  # quote is genuinely grounded
    assert response["evidence_state"]["state"] == "stale_source"  # but the source itself is stale
    assert response["evidence_state"]["reasons"] == ["stale:fee_doc"]


def test_two_conflicting_active_official_sources_yield_source_conflict():
    generator = _generator(
        [
            _chunk("fee_chunk_a", "fee_doc_a", "Học phí kỳ này là 15 triệu đồng theo thông báo A."),
            _chunk("fee_chunk_b", "fee_doc_b", "Học phí kỳ này là 18 triệu đồng theo thông báo B."),
        ],
        {
            "fee_doc_a": {"checksum": "aaa111", "status": "active", "conflict_key": "tuition_2026"},
            "fee_doc_b": {"checksum": "bbb222", "status": "active", "conflict_key": "tuition_2026"},
        },
    )

    response = generator.answer("Học phí kỳ này là bao nhiêu?", top_k=2)

    assert response["refusal"] is False
    assert len(response["citations"]) >= 2
    assert response["evidence_state"]["state"] == "source_conflict"


def test_refusal_is_insufficient_evidence_and_citation_verification_trivially_valid():
    generator = _generator(
        [_chunk("email_chunk", "email_doc", "Cấu trúc email sinh viên: MSSV@student.tdtu.edu.vn.")],
        {"email_doc": {"checksum": "abc123", "status": "active"}},
    )

    response = generator.answer("Số điện thoại của một sinh viên cụ thể là gì?")

    assert response["refusal"] is True
    assert response["evidence_state"]["state"] == "insufficient_evidence"
    assert response["citation_verification"]["is_valid"] is True
