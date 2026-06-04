from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.main import app
from rag.generation.answer_generator import AnswerGenerator
from rag.generation.provider_router import ProviderInvocation


client = TestClient(app)


@dataclass(frozen=True)
class StubContextBundle:
    question: str
    support_score: float
    retrieval_debug: dict
    chunks: list[dict]


class StubContextBuilder:
    def __init__(self, bundle: StubContextBundle) -> None:
        self.bundle = bundle

    def build(self, question: str, top_k: int = 5):
        return StubContextBundle(
            question=question,
            support_score=self.bundle.support_score,
            retrieval_debug={"top_k": top_k, **self.bundle.retrieval_debug},
            chunks=list(self.bundle.chunks),
        )


class StubAnswerGenerator:
    def answer_with_agent_fallback_from_context(self, question, context_bundle, debug=False):
        return (
            {
                "answer": "Theo ngữ cảnh đã truy xuất, ngành Khoa học máy tính cần 136 tín chỉ để tốt nghiệp.",
                "citations": [
                    {
                        "doc_id": "doc-1",
                        "chunk_id": "c1",
                        "source_url": "https://example.edu/cs",
                        "heading_path": ["Chương trình đào tạo"],
                        "quoted_evidence": "Ngành Khoa học máy tính cần tích lũy 136 tín chỉ để tốt nghiệp.",
                    }
                ],
                "confidence": 0.9,
                "refusal": False,
                "refusal_reason": None,
                "retrieval_debug": {"top_k": 5},
            },
            {"provider": "ollama", "model": "qwen2.5:3b", "fallback_used": False, "error": None},
        )


class StubProviderRouterWithTools:
    def status(self):
        return {
            "provider": "ollama",
            "model": "qwen2.5:3b",
            "ollama": {"available": True, "model_available": True, "base_url": "http://localhost:11434"},
        }

    def chat_with_tools(self, messages, tools):
        return type(
            "Invocation",
            (),
            {
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {"name": "retrieve_policy_context", "arguments": {"question": messages[-1]["content"]}},
                    }
                ],
                "content": "",
                "fallback_used": False,
                "error": None,
            },
        )()

    def chat(self, messages):
        return type("Invocation", (), {"content": "done", "fallback_used": False})()


class StubProviderRouterFallback(StubProviderRouterWithTools):
    def chat_with_tools(self, messages, tools):
        return type("Invocation", (), {"tool_calls": [], "content": "", "fallback_used": True, "error": "offline"})()


class StubProviderRouterInvalidCitation:
    def __init__(self) -> None:
        self.provider = "ollama"
        self.model = "qwen2.5:3b"

    def current_provider(self) -> str:
        return self.provider

    def generate_json(self, prompt: str) -> ProviderInvocation:
        return ProviderInvocation(
            provider=self.provider,
            model=self.model,
            payload={
                "answer": "Cấu trúc email sinh viên TDTU là MSSV@student.tdtu.edu.vn.",
                "citations": [
                    {
                        "doc_id": "hallucinated-doc",
                        "chunk_id": "2. Điểm H",
                        "source_url": "https://invalid.example",
                        "heading_path": ["Sai"],
                        "quoted_evidence": "MSSV@student.tdtu.edu.vn",
                    }
                ],
                "confidence": 0.8,
                "refusal": False,
                "refusal_reason": None,
            },
        )


def make_cs_bundle() -> StubContextBundle:
    return StubContextBundle(
        question="Ngành Khoa học máy tính cần bao nhiêu tín chỉ để tốt nghiệp?",
        support_score=0.8,
        retrieval_debug={"chunk_ids": ["c1"]},
        chunks=[
            {
                "chunk_id": "c1",
                "doc_id": "doc-1",
                "text": "Ngành Khoa học máy tính cần tích lũy 136 tín chỉ để tốt nghiệp.",
                "source_url": "https://example.edu/cs",
                "heading_path": ["Chương trình đào tạo"],
                "authority_level": "official",
                "domain": "curriculum",
                "score": 0.95,
                "component_scores": {"hybrid_score": 0.95},
                "support_score": 0.9,
                "lexical_score": 0.9,
                "bigram_overlap": 0.4,
            }
        ],
    )


def make_email_bundle() -> StubContextBundle:
    return StubContextBundle(
        question="Cấu trúc email sinh viên TDTU là gì?",
        support_score=0.92,
        retrieval_debug={"chunk_ids": ["ug_student_email_guide_s001_c001"]},
        chunks=[
            {
                "chunk_id": "ug_student_email_guide_s001_c001",
                "doc_id": "ug_student_email_guide",
                "text": (
                    "Email sinh viên TDTU > Email sinh viên TDTU\n"
                    "Mỗi sinh viên được cấp 1 tài khoản email để trao đổi thông tin phục vụ việc học tại Trường.\n"
                    "Cấu trúc email: MSSV@student.tdtu.edu.vn\n"
                    "Địa chỉ đăng nhập: mail.student.tdtu.edu.vn"
                ),
                "source_url": "https://undergrad.tdtu.edu.vn/huong-dan/email-sinh-vien-tdtu",
                "heading_path": ["Email sinh viên TDTU", "Email sinh viên TDTU"],
                "authority_level": "official",
                "domain": "email_usage",
                "score": 0.99,
                "component_scores": {"hybrid_score": 0.99},
                "support_score": 0.95,
                "lexical_score": 0.95,
                "bigram_overlap": 0.6,
            }
        ],
    )


def make_tuition_bundle() -> StubContextBundle:
    return StubContextBundle(
        question="Học phí kỳ này của tôi là bao nhiêu?",
        support_score=0.2,
        retrieval_debug={"chunk_ids": ["c-fee"]},
        chunks=[
            {
                "chunk_id": "c-fee",
                "doc_id": "doc-fee",
                "text": "Phòng Tài chính hỗ trợ giải đáp các thắc mắc liên quan đến học phí cho sinh viên.",
                "source_url": "https://example.edu/fees",
                "heading_path": ["Hỗ trợ học phí"],
                "authority_level": "official",
                "domain": "student_support",
                "score": 0.4,
                "component_scores": {"hybrid_score": 0.4},
                "support_score": 0.2,
                "lexical_score": 0.2,
                "bigram_overlap": 0.0,
            }
        ],
    )


def test_agent_ask_endpoint_returns_tool_trace(monkeypatch):
    monkeypatch.setattr("app.api.routes_agent.get_context_builder", lambda: StubContextBuilder(make_cs_bundle()))
    monkeypatch.setattr("app.api.routes_agent.get_agent_answer_generator", lambda: StubAnswerGenerator())
    monkeypatch.setattr("app.api.routes_agent.get_agent_provider_router", lambda: StubProviderRouterWithTools())

    response = client.post(
        "/agent/ask",
        json={"question": "Ngành Khoa học máy tính cần bao nhiêu tín chỉ để tốt nghiệp?", "top_k": 5, "return_debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "ollama"
    assert data["model"] == "qwen2.5:3b"
    assert data["provider_status"]["ollama"]["available"] is True
    assert data["generation_mode"] == "Ollama direct"
    assert data["tool_calls"][0]["name"] == "retrieve_policy_context"
    assert data["fallback_used"] is False
    assert data["citations"][0]["chunk_id"] == "c1"
    assert "136" in data["answer"]
    assert data["confidence"] == 0.9


def test_agent_ask_endpoint_email_rebuilds_citations_from_verified_chunks(monkeypatch):
    answer_generator = AnswerGenerator(
        context_builder=StubContextBuilder(make_email_bundle()),
        provider_router=StubProviderRouterInvalidCitation(),
    )
    monkeypatch.setattr("app.api.routes_agent.get_context_builder", lambda: StubContextBuilder(make_email_bundle()))
    monkeypatch.setattr("app.api.routes_agent.get_agent_answer_generator", lambda: answer_generator)
    monkeypatch.setattr("app.api.routes_agent.get_agent_provider_router", lambda: StubProviderRouterFallback())

    response = client.post(
        "/agent/ask",
        json={"question": "Cấu trúc email sinh viên TDTU là gì?", "top_k": 5, "return_debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["refusal"] is False
    assert data["citations"]
    retrieved_chunk_ids = {item["chunk_id"] for item in data["retrieved_chunks"]}
    assert retrieved_chunk_ids == {"ug_student_email_guide_s001_c001"}
    assert all(citation["chunk_id"] in retrieved_chunk_ids for citation in data["citations"])
    assert all(citation["chunk_id"] != "2. Điểm H" for citation in data["citations"])
    assert "MSSV@student.tdtu.edu.vn" in data["answer"]
    assert data["provider"] == "ollama"
    assert data["generation_mode"] == "Verified fallback"
    assert data["fallback_used"] is True
    assert "rebuilt the answer from verified retrieved chunks" in data["fallback_reason"]
    assert data["citations_verified"] is True


def test_agent_ask_endpoint_private_question_still_refuses(monkeypatch):
    answer_generator = AnswerGenerator(
        context_builder=StubContextBuilder(make_tuition_bundle()),
        provider_router=StubProviderRouterInvalidCitation(),
    )
    monkeypatch.setattr("app.api.routes_agent.get_context_builder", lambda: StubContextBuilder(make_tuition_bundle()))
    monkeypatch.setattr("app.api.routes_agent.get_agent_answer_generator", lambda: answer_generator)
    monkeypatch.setattr("app.api.routes_agent.get_agent_provider_router", lambda: StubProviderRouterFallback())

    response = client.post(
        "/agent/ask",
        json={"question": "Học phí kỳ này của tôi là bao nhiêu?", "top_k": 5, "return_debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["refusal"] is True
    assert data["citations"] == []
    assert data["refusal_reason"]
    assert data["generation_mode"] == "Deterministic fallback"


def test_agent_ask_endpoint_forces_retrieval_fallback(monkeypatch):
    monkeypatch.setattr("app.api.routes_agent.get_context_builder", lambda: StubContextBuilder(make_cs_bundle()))
    monkeypatch.setattr("app.api.routes_agent.get_agent_answer_generator", lambda: StubAnswerGenerator())
    monkeypatch.setattr("app.api.routes_agent.get_agent_provider_router", lambda: StubProviderRouterFallback())

    response = client.post(
        "/agent/ask",
        json={"question": "Học phí kỳ này của tôi là bao nhiêu?", "top_k": 5, "return_debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tool_calls"] == []
    assert data["fallback_used"] is True
    assert data["answer"]
    assert data["generation_mode"] == "Verified fallback"
    assert data["fallback_reason"]


def test_agent_ask_endpoint_mock_provider_explains_setup_hint(monkeypatch):
    monkeypatch.setattr("app.api.routes_agent.get_context_builder", lambda: StubContextBuilder(make_cs_bundle()))
    monkeypatch.setattr("app.api.routes_agent.get_agent_answer_generator", lambda: StubAnswerGenerator())
    monkeypatch.setattr("app.api.routes_agent.get_agent_provider_router", lambda: StubProviderRouterFallback())

    class MockStatusRouter(StubProviderRouterFallback):
        def status(self):
            return {
                "provider": "mock",
                "model": "deterministic-mock",
                "ollama": {"available": True, "model_available": True, "base_url": "http://localhost:11434"},
            }

    monkeypatch.setattr("app.api.routes_agent.get_agent_provider_router", lambda: MockStatusRouter())
    response = client.post(
        "/agent/ask",
        json={"question": "Ngành Khoa học máy tính cần bao nhiêu tín chỉ để tốt nghiệp?", "top_k": 5, "return_debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert "LLM_PROVIDER=ollama" in data["fallback_reason"]


def test_agent_ask_endpoint_out_of_scope_question_refuses(monkeypatch):
    answer_generator = AnswerGenerator(
        context_builder=StubContextBuilder(make_tuition_bundle()),
        provider_router=StubProviderRouterInvalidCitation(),
    )
    monkeypatch.setattr("app.api.routes_agent.get_context_builder", lambda: StubContextBuilder(make_tuition_bundle()))
    monkeypatch.setattr("app.api.routes_agent.get_agent_answer_generator", lambda: answer_generator)
    monkeypatch.setattr("app.api.routes_agent.get_agent_provider_router", lambda: StubProviderRouterFallback())

    response = client.post(
        "/agent/ask",
        json={"question": "Tôi nên mua laptop nào?", "top_k": 5, "return_debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["refusal"] is True
    assert data["citations"] == []
