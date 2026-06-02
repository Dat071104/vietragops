from rag.generation.context_builder import ContextBundle
from rag.generation.guardrails import GuardrailEngine


def make_bundle(score: float) -> ContextBundle:
    return ContextBundle(
        question="Question",
        chunks=[{"chunk_id": "c1", "text": "text"}] if score > 0 else [],
        support_score=score,
        retrieval_debug={},
    )


def test_guardrails_refuse_private_data_question():
    engine = GuardrailEngine()
    decision = engine.evaluate("Số điện thoại của một sinh viên cụ thể là gì?", make_bundle(0.9))
    assert decision.refusal is True


def test_guardrails_refuse_low_support_question():
    engine = GuardrailEngine(min_support_score=0.4)
    decision = engine.evaluate("Câu hỏi ngoài phạm vi", make_bundle(0.1))
    assert decision.refusal is True
