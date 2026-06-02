from rag.retrieval.base import RetrievalResult
from rag.retrieval.rrf import reciprocal_rank_fusion


def make_result(chunk_id: str, rank: int, score: float) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        doc_id=chunk_id,
        score=score,
        rank=rank,
        text="",
        source_url="https://example.edu",
        heading_path=["Heading"],
        authority_level="official",
        domain="course_registration",
        component_scores={},
        metadata={"title": "Title"},
    )


def test_rrf_prefers_items_ranked_by_multiple_systems():
    fused = reciprocal_rank_fusion(
        [
            ("bm25_score", [make_result("c1", 1, 9.0), make_result("c2", 2, 8.0)]),
            ("dense_score", [make_result("c2", 1, 0.9), make_result("c1", 2, 0.8)]),
        ],
        rrf_k=10,
    )

    assert fused["c1"]["rrf_score"] > 0
    assert fused["c2"]["rrf_score"] > 0
    assert fused["c2"]["component_scores"]["dense_score"] == 0.9
