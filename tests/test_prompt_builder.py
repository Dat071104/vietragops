from rag.generation.context_builder import ContextBundle
from rag.generation.prompt_builder import PromptBuilder


def test_prompt_builder_includes_rules_and_context():
    builder = PromptBuilder()
    bundle = ContextBundle(
        question="Email sinh viên là gì?",
        chunks=[
            {
                "chunk_id": "c1",
                "doc_id": "doc1",
                "text": "Cấu trúc email: MSSV@student.tdtu.edu.vn",
                "source_url": "https://example.edu",
                "heading_path": ["Email sinh viên"],
                "authority_level": "official",
                "domain": "email_usage",
                "score": 0.5,
                "component_scores": {},
                "metadata": {"title": "Email"},
                "support_score": 0.8,
            }
        ],
        support_score=0.8,
        retrieval_debug={},
    )

    prompt = builder.build("Email sinh viên là gì?", bundle)

    assert "Chỉ được trả lời dựa trên NGỮ CẢNH" in prompt
    assert "Trả lời bằng tiếng Việt" in prompt
    assert "MSSV@student.tdtu.edu.vn" in prompt
