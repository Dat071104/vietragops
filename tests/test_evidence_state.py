from __future__ import annotations

from rag.generation.evidence_state import (
    INSUFFICIENT_EVIDENCE,
    SOURCE_CONFLICT,
    STALE_SOURCE,
    SUPPORTED,
    resolve_evidence_state,
)


def _version(
    source_id: str,
    source_version: str,
    *,
    authority_state: str = "active",
    freshness_state: str = "unknown",
    conflict_key: str | None = None,
) -> dict:
    return {
        "source_id": source_id,
        "source_version": source_version,
        "index_version": "sha256:deadbeef",
        "authority_state": authority_state,
        "freshness_state": freshness_state,
        "conflict_key": conflict_key,
    }


def _chunk(chunk_id: str, version: dict | None) -> dict:
    chunk = {"chunk_id": chunk_id, "text": "text"}
    if version is not None:
        chunk["version"] = version
    return chunk


def test_refusal_is_insufficient_evidence():
    result = resolve_evidence_state(refusal=True, citations=[], chunks=[])
    assert result.state == INSUFFICIENT_EVIDENCE
    assert result.reasons == ["refusal"]


def test_no_citations_is_insufficient_evidence():
    result = resolve_evidence_state(refusal=False, citations=[], chunks=[_chunk("c1", _version("doc1", "v1"))])
    assert result.state == INSUFFICIENT_EVIDENCE


def test_citation_with_unresolved_version_is_insufficient_evidence():
    chunks = [_chunk("c1", None)]
    citations = [{"chunk_id": "c1"}]
    result = resolve_evidence_state(refusal=False, citations=citations, chunks=chunks)
    assert result.state == INSUFFICIENT_EVIDENCE
    assert result.reasons == ["no_resolved_version_for_citations"]


def test_citation_pointing_at_unknown_chunk_id_is_insufficient_evidence():
    chunks = [_chunk("c1", _version("doc1", "v1"))]
    citations = [{"chunk_id": "does_not_exist"}]
    result = resolve_evidence_state(refusal=False, citations=citations, chunks=chunks)
    assert result.state == INSUFFICIENT_EVIDENCE


def test_normal_educational_qa_is_supported():
    chunks = [_chunk("c1", _version("doc1", "legacy:abc123", freshness_state="current"))]
    citations = [{"chunk_id": "c1"}]
    result = resolve_evidence_state(refusal=False, citations=citations, chunks=chunks)
    assert result.state == SUPPORTED
    assert result.reasons == []


def test_normal_educational_qa_with_unknown_freshness_is_supported():
    """The real 37-doc corpus never sets stale_after, so freshness stays
    'unknown' for every legacy chunk -- this must never be treated as stale."""
    chunks = [_chunk("c1", _version("doc1", "legacy:abc123", freshness_state="unknown"))]
    citations = [{"chunk_id": "c1"}]
    result = resolve_evidence_state(refusal=False, citations=citations, chunks=chunks)
    assert result.state == SUPPORTED


def test_stale_cited_source_yields_stale_source():
    chunks = [_chunk("c1", _version("doc1", "legacy:abc123", freshness_state="stale"))]
    citations = [{"chunk_id": "c1"}]
    result = resolve_evidence_state(refusal=False, citations=citations, chunks=chunks)
    assert result.state == STALE_SOURCE
    assert result.reasons == ["stale:doc1"]


def test_two_active_conflicting_official_sources_yield_source_conflict():
    chunks = [
        _chunk("c1", _version("doc_a", "legacy:aaa", conflict_key="tuition_2026")),
        _chunk("c2", _version("doc_b", "legacy:bbb", conflict_key="tuition_2026")),
    ]
    citations = [{"chunk_id": "c1"}, {"chunk_id": "c2"}]
    result = resolve_evidence_state(refusal=False, citations=citations, chunks=chunks)
    assert result.state == SOURCE_CONFLICT
    assert result.reasons == ["conflict_key=tuition_2026"]


def test_conflict_key_shared_by_same_version_is_not_a_conflict():
    """Two chunks from the SAME source version sharing a conflict_key (e.g.
    two chunks of one document) must not be misreported as a conflict."""
    chunks = [
        _chunk("c1", _version("doc_a", "legacy:aaa", conflict_key="tuition_2026")),
        _chunk("c2", _version("doc_a", "legacy:aaa", conflict_key="tuition_2026")),
    ]
    citations = [{"chunk_id": "c1"}, {"chunk_id": "c2"}]
    result = resolve_evidence_state(refusal=False, citations=citations, chunks=chunks)
    assert result.state == SUPPORTED


def test_conflict_requires_both_sources_to_be_active():
    """A retired source sharing a conflict_key with an active one must not
    trigger source_conflict -- the retired one is not a live disagreement."""
    chunks = [
        _chunk("c1", _version("doc_a", "legacy:aaa", authority_state="active", conflict_key="tuition_2026")),
        _chunk("c2", _version("doc_b", "legacy:bbb", authority_state="retired", conflict_key="tuition_2026")),
    ]
    citations = [{"chunk_id": "c1"}, {"chunk_id": "c2"}]
    result = resolve_evidence_state(refusal=False, citations=citations, chunks=chunks)
    assert result.state == SUPPORTED


def test_conflict_takes_precedence_over_stale():
    chunks = [
        _chunk(
            "c1",
            _version("doc_a", "legacy:aaa", conflict_key="tuition_2026", freshness_state="stale"),
        ),
        _chunk(
            "c2",
            _version("doc_b", "legacy:bbb", conflict_key="tuition_2026", freshness_state="current"),
        ),
    ]
    citations = [{"chunk_id": "c1"}, {"chunk_id": "c2"}]
    result = resolve_evidence_state(refusal=False, citations=citations, chunks=chunks)
    assert result.state == SOURCE_CONFLICT
