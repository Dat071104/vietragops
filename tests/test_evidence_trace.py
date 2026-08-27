"""Gate 04 Phase 4.3: structural tests for the evidence trace exposed through
the existing `/ask` and `/agent/ask` contracts -- query, retrieval, ranking,
selected chunks with source/index version, generation/provider/model,
citations with a separate verification verdict, and latency.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from rag.generation.context_builder import ContextBuilder
from rag.retrieval import ChunkIndexStore
from rag.retrieval.version_resolver import VersionResolver


client = TestClient(app)


def test_ask_endpoint_trace_has_query_ranking_versions_generation_and_citation_state():
    response = client.post(
        "/ask",
        json={
            "question": "Ngành Khoa học máy tính cần bao nhiêu tín chỉ để tốt nghiệp?",
            "top_k": 5,
            "return_debug": True,
        },
    )
    assert response.status_code == 200
    data = response.json()

    debug = data["retrieval_debug"]
    assert debug["query"] == "Ngành Khoa học máy tính cần bao nhiêu tín chỉ để tốt nghiệp?"
    assert "retriever" in debug and "backend" in debug
    assert "chunk_ids" in debug and "scores" in debug  # ranking + selected chunks
    assert "chunk_versions" in debug
    for chunk_id in debug["chunk_ids"]:
        version = debug["chunk_versions"][chunk_id]
        assert set(version) == {
            "source_id",
            "source_version",
            "index_version",
            "authority_state",
            "freshness_state",
            "conflict_key",
        }

    # citation verification stays a distinct verdict from evidence_state / answer correctness
    assert "citation_verification" in data and "is_valid" in data["citation_verification"]
    assert "evidence_state" in data and data["evidence_state"]["state"] in {
        "supported",
        "insufficient_evidence",
        "stale_source",
        "source_conflict",
    }

    if not data["refusal"]:
        assert data["generation"] is not None
        # Gate 04's original fields, still present unchanged; Gate 05 added
        # `failure_kind`/`mode`/`primary_attempt` additively (see GATE_05.md).
        assert {"provider", "model", "fallback_used", "error", "latency_ms"} <= set(data["generation"])
        assert data["generation"]["latency_ms"] >= 0


def test_ask_endpoint_trace_chunk_ids_and_scores_are_in_the_same_deterministic_order():
    response = client.post(
        "/ask",
        json={"question": "Cấu trúc email sinh viên là gì?", "top_k": 5, "return_debug": True},
    )
    assert response.status_code == 200
    debug = response.json()["retrieval_debug"]

    assert [item["chunk_id"] for item in debug["scores"]] == debug["chunk_ids"]
    support_scores = [item["support_score"] for item in debug["scores"]]
    assert support_scores == sorted(support_scores, reverse=True)


def test_ask_endpoint_privacy_refusal_yields_insufficient_evidence_with_no_generation_trace():
    response = client.post(
        "/ask",
        json={"question": "Số điện thoại cá nhân của một sinh viên cụ thể là gì?", "return_debug": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["refusal"] is True
    assert data["evidence_state"]["state"] == "insufficient_evidence"
    assert data["citation_verification"]["is_valid"] is True
    assert data["generation"] is None  # guardrail refused before any provider call


def test_agent_ask_endpoint_debug_trace_carries_generation_and_provider_status():
    response = client.post(
        "/agent/ask",
        json={"question": "Cấu trúc email sinh viên là gì?", "top_k": 5, "return_debug": True},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["latency_ms"] >= 0
    assert data["provider"]
    assert data["model"]
    assert "citation_verification" in data
    assert "evidence_state" in data
    assert "retrieval_debug" in data["debug"]
    assert "provider_status" in data["debug"]
    assert "generation" in data["debug"]


def test_context_builder_retrieval_debug_query_matches_the_question_directly():
    store = ChunkIndexStore.from_records(
        [
            {
                "chunk_id": "c1",
                "doc_id": "doc1",
                "title": "Doc 1",
                "source_url": "https://example.edu/doc1",
                "source_type": "html",
                "domain": "student_guide",
                "authority_level": "official",
                "heading_path": ["Doc 1"],
                "page_start": None,
                "page_end": None,
                "section_id": "doc1_s001",
                "chunk_index": 1,
                "text": "Nội dung doc 1 liên quan đến câu hỏi kiểm thử.",
            }
        ]
    )
    resolver = VersionResolver({"doc1": {"checksum": "abc123", "status": "active"}}, index_version=store.index_version)
    builder = ContextBuilder(store, version_resolver=resolver)

    bundle = builder.build("câu hỏi kiểm thử", top_k=1)

    assert bundle.retrieval_debug["query"] == "câu hỏi kiểm thử"
    assert bundle.retrieval_debug["chunk_versions"][bundle.chunks[0]["chunk_id"]]["index_version"] == store.index_version
