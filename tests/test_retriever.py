import logging

import pytest

from rag.retrieval import BM25Retriever, ChunkIndexStore, DenseRetriever, HybridRetriever
import rag.retrieval.dense_retriever as dense_retriever_module


def make_store() -> ChunkIndexStore:
    records = [
        {
            "chunk_id": "student_email_chunk",
            "doc_id": "student_email",
            "title": "Email sinh viên",
            "source_url": "https://example.edu/email",
            "source_type": "html",
            "domain": "email_usage",
            "authority_level": "official",
            "heading_path": ["Email sinh viên"],
            "page_start": None,
            "page_end": None,
            "section_id": "student_email_s001",
            "chunk_index": 1,
            "text": "Email sinh viên có cấu trúc MSSV@student.tdtu.edu.vn và dùng để liên hệ với Trường.",
        },
        {
            "chunk_id": "course_registration_chunk",
            "doc_id": "course_registration",
            "title": "Đăng ký môn học",
            "source_url": "https://example.edu/register",
            "source_type": "html",
            "domain": "course_registration",
            "authority_level": "official",
            "heading_path": ["Đăng ký môn học"],
            "page_start": None,
            "page_end": None,
            "section_id": "course_registration_s001",
            "chunk_index": 1,
            "text": "Sinh viên phải xác nhận mật khẩu để hoàn tất đăng ký môn học trong hệ thống.",
        },
        {
            "chunk_id": "graduation_chunk",
            "doc_id": "graduation",
            "title": "Điều kiện tốt nghiệp",
            "source_url": "https://example.edu/graduation",
            "source_type": "html",
            "domain": "graduation_requirement",
            "authority_level": "official",
            "heading_path": ["Điều kiện tốt nghiệp"],
            "page_start": None,
            "page_end": None,
            "section_id": "graduation_s001",
            "chunk_index": 1,
            "text": "Sinh viên phải hoàn tất học phần bắt buộc, học phần tự chọn và chuẩn đầu ra để được xét tốt nghiệp.",
        },
    ]
    return ChunkIndexStore.from_records(records)


def test_bm25_retriever_returns_exact_match():
    retriever = BM25Retriever(make_store())
    results = retriever.retrieve("Cấu trúc email sinh viên là gì?", top_k=2)
    assert results
    assert results[0].chunk_id == "student_email_chunk"


def test_dense_retriever_fallback_returns_semanticish_match():
    retriever = DenseRetriever(make_store())
    results = retriever.retrieve("Đăng nhập email trường bằng tài khoản sinh viên", top_k=2)
    assert results
    assert results[0].chunk_id == "student_email_chunk"


def test_dense_backend_available_is_selected_and_reported(monkeypatch):
    class FakeDenseBackend:
        name = "sentence_transformers:test"

        def __init__(self, store, config):
            self.store = store
            self.config = config

        def search(self, query, top_k):
            return [(0, 1.0)]

    monkeypatch.setattr(dense_retriever_module, "_SentenceTransformerBackend", FakeDenseBackend)

    retriever = DenseRetriever(make_store())

    assert retriever.backend_name == "sentence_transformers:test"
    assert retriever.status() == {
        "name": "dense",
        "backend": "sentence_transformers:test",
        "state": "active",
        "degraded": False,
        "degradation_reason": None,
        "model_name": retriever.config.model_name,
    }


def test_dense_backend_unavailable_is_loud_and_reported(monkeypatch, caplog):
    def unavailable(store, config):
        raise ModuleNotFoundError("No module named 'sentence_transformers'")

    monkeypatch.setattr(dense_retriever_module, "_SentenceTransformerBackend", unavailable)

    with caplog.at_level(logging.WARNING, logger="rag.retrieval.dense_retriever"):
        retriever = DenseRetriever(make_store())

    assert retriever.backend_name == "sparse_semantic_fallback"
    assert retriever.status()["state"] == "degraded"
    assert retriever.status()["degraded"] is True
    assert "ModuleNotFoundError" in retriever.status()["degradation_reason"]
    assert "sentence_transformers" in caplog.text


def test_hybrid_retriever_combines_signals():
    retriever = HybridRetriever(make_store())
    results = retriever.retrieve("làm sao hoàn tất đăng ký môn học", top_k=2)
    assert results
    assert results[0].chunk_id == "course_registration_chunk"
