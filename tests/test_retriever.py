from rag.retrieval import BM25Retriever, ChunkIndexStore, DenseRetriever, HybridRetriever


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


def test_hybrid_retriever_combines_signals():
    retriever = HybridRetriever(make_store())
    results = retriever.retrieve("làm sao hoàn tất đăng ký môn học", top_k=2)
    assert results
    assert results[0].chunk_id == "course_registration_chunk"
