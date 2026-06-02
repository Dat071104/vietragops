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
