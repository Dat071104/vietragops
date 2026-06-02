from types import SimpleNamespace

from rag.retrieval.source_priority import recency_score, source_authority_score


def test_source_authority_scores_follow_priority_map():
    official_chunk = SimpleNamespace(domain="training_regulation", authority_level="official")
    faculty_chunk = SimpleNamespace(domain="curriculum", authority_level="faculty")
    guide_chunk = SimpleNamespace(domain="student_guide", authority_level="official")

    assert source_authority_score(official_chunk) == 1.0
    assert source_authority_score(faculty_chunk) == 0.9
    assert source_authority_score(guide_chunk) == 0.85


def test_recency_score_prefers_newer_manifest_rows():
    chunk = SimpleNamespace(doc_id="doc_2025", title="Tài liệu 2025")
    old_score = recency_score(chunk, {"published_at": "2021-01-01T00:00:00+07:00", "crawled_at": ""})
    new_score = recency_score(chunk, {"published_at": "2025-01-01T00:00:00+07:00", "crawled_at": ""})

    assert new_score > old_score
