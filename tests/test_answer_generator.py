from rag.generation.answer_generator import AnswerGenerator
from rag.generation.context_builder import ContextBuilder
from rag.generation.groq_client import GroqClient
from rag.retrieval import ChunkIndexStore


class StubGroqClient(GroqClient):
    def __init__(self) -> None:
        pass

    def available(self) -> bool:
        return False


def make_store() -> ChunkIndexStore:
    records = [
        {
            "chunk_id": "email_chunk",
            "doc_id": "email_doc",
            "title": "Email sinh viên",
            "source_url": "https://example.edu/email",
            "source_type": "html",
            "domain": "email_usage",
            "authority_level": "official",
            "heading_path": ["Email sinh viên"],
            "page_start": None,
            "page_end": None,
            "section_id": "email_s001",
            "chunk_index": 1,
            "text": "Mỗi sinh viên được cấp 1 tài khoản email. Cấu trúc email: MSSV@student.tdtu.edu.vn.",
        }
    ]
    return ChunkIndexStore.from_records(records)


def test_answer_generator_returns_grounded_answer_without_groq():
    store = make_store()
    generator = AnswerGenerator(
        context_builder=ContextBuilder(store),
        groq_client=StubGroqClient(),
    )

    response = generator.answer("Cấu trúc email sinh viên là gì?")

    assert response["refusal"] is False
    assert response["citations"]
    assert "MSSV@student.tdtu.edu.vn" in response["answer"]


def test_answer_generator_refuses_private_data_request():
    store = make_store()
    generator = AnswerGenerator(
        context_builder=ContextBuilder(store),
        groq_client=StubGroqClient(),
    )

    response = generator.answer("Số điện thoại của một sinh viên cụ thể là gì?")

    assert response["refusal"] is True
    assert response["citations"] == []


def test_answer_generator_email_evidence_trim_keeps_login_phrases():
    generator = AnswerGenerator(
        context_builder=ContextBuilder(make_store()),
        groq_client=StubGroqClient(),
    )
    evidence = [
        {
            "chunk_id": "email_format_chunk",
            "doc_id": "email_doc",
            "source_url": "https://example.edu/email",
            "heading_path": ["Email sinh viên"],
            "text": "Cấu trúc email sinh viên TDTU: MSSV@student.tdtu.edu.vn.",
        },
        {
            "chunk_id": "email_login_chunk",
            "doc_id": "email_doc",
            "source_url": "https://example.edu/email",
            "heading_path": ["Email sinh viên"],
            "text": "Địa chỉ đăng nhập: mail.student.tdtu.edu.vn. Tên đăng nhập là email sinh viên.",
        },
        {
            "chunk_id": "other_chunk",
            "doc_id": "other_doc",
            "source_url": "https://example.edu/other",
            "heading_path": ["Khác"],
            "text": "Nội dung không liên quan đến email sinh viên.",
        },
    ]

    trimmed = generator._trim_evidence("Cấu trúc email và địa chỉ đăng nhập email sinh viên TDTU là gì?", evidence)

    assert [item["chunk_id"] for item in trimmed] == ["email_format_chunk", "email_login_chunk"]
