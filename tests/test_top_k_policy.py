from app.schemas.query import AskRequest
from rag.generation.answer_generator import AnswerGeneratorConfig


def test_product_ask_default_top_k_is_pinned_to_ten():
    assert AskRequest(question="Câu hỏi kiểm thử").top_k == 10
    assert AnswerGeneratorConfig().top_k == 10
