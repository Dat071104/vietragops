import logging

from rag.retrieval.base import RetrievalResult
import rag.retrieval.reranker as reranker_module
from rag.retrieval.reranker import LexicalReranker, build_reranker


def make_candidate(chunk_id: str, text: str, title: str = "Hướng dẫn") -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        doc_id=chunk_id,
        score=0.1,
        rank=1,
        text=text,
        source_url="https://example.edu",
        heading_path=[title],
        authority_level="official",
        domain="course_registration",
        component_scores={"hybrid_score": 0.1},
        metadata={"title": title},
    )


def test_lexical_reranker_prefers_high_overlap_candidate():
    reranker = LexicalReranker()
    candidates = [
        make_candidate("generic", "Quy định về học kỳ và số tín chỉ tối đa trong mỗi học kỳ."),
        make_candidate("specific", "Sinh viên muốn đăng ký vượt số tín chỉ tối đa phải làm đơn tại văn phòng hỗ trợ."),
    ]

    ranked = reranker.rerank("Nếu muốn đăng ký vượt số tín chỉ tối đa thì sinh viên phải làm gì?", candidates)

    assert ranked[0].result.chunk_id == "specific"
    assert ranked[0].score >= ranked[1].score


def test_reranker_backend_unavailable_is_loud_and_reported(monkeypatch, caplog):
    def unavailable(*args, **kwargs):
        raise ModuleNotFoundError("No module named 'FlagEmbedding'")

    monkeypatch.setattr(reranker_module, "BGEReranker", unavailable)

    with caplog.at_level(logging.WARNING, logger="rag.retrieval.reranker"):
        reranker = build_reranker()

    assert isinstance(reranker, LexicalReranker)
    assert reranker.status()["state"] == "degraded"
    assert reranker.status()["degraded"] is True
    assert "FlagEmbedding" in reranker.status()["degradation_reason"]
    assert "FlagEmbedding" in caplog.text
