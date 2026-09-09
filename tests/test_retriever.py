import logging

import pytest

from rag.retrieval import BM25Retriever, ChunkIndexStore, DenseRetriever, HybridRetriever
import rag.retrieval.dense_retriever as dense_retriever_module
from rag.retrieval.dense_retriever import VectorSpaceMismatchError


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
    class FakeOnnxBackend:
        name = "onnx:test:fp32"

        def __init__(self, store, config):
            self.store = store
            self.config = config

        def search(self, query, top_k):
            return [(0, 1.0)]

    monkeypatch.setattr(dense_retriever_module, "_OnnxBackend", FakeOnnxBackend)

    retriever = DenseRetriever(make_store())

    assert retriever.backend_name == "onnx:test:fp32"
    assert retriever.status()["state"] == "active"
    assert retriever.status()["degraded"] is False
    assert retriever.status()["downgrade_reasons"] == []


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


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        ({"model_id": "other/model", "dimension": 2, "normalized": True, "normalization": "l2"}, "model identity"),
        ({"model_id": "expected/model", "dimension": 3, "normalized": True, "normalization": "l2"}, "shape"),
        ({"model_id": "expected/model", "dimension": 2, "normalized": False, "normalization": "none"}, "normalized"),
    ],
)
def test_vector_space_contract_rejects_mismatch(metadata, message):
    class FakeEmbeddings:
        ndim = 2
        shape = (3, 2)

        def __len__(self):
            return self.shape[0]

    with pytest.raises(VectorSpaceMismatchError, match=message):
        dense_retriever_module._validate_vector_space(
            metadata,
            FakeEmbeddings(),
            [chunk.chunk_id for chunk in make_store()],
            make_store(),
            expected_model_name="expected/model",
            expected_model_revision=None,
            session_dimension=2,
        )


def test_hybrid_retriever_combines_signals():
    retriever = HybridRetriever(make_store())
    results = retriever.retrieve("làm sao hoàn tất đăng ký môn học", top_k=2)
    assert results
    assert results[0].chunk_id == "course_registration_chunk"
