from rag.retrieval.base import RetrievalResult
from rag.retrieval.reranker import LexicalReranker


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
