from evals.experiments.compare_retrievers import parse_args as parse_compare_retrievers_args
from evals.experiments.defaults import DEFAULT_CHUNKS_PATH, DEFAULT_GENERATION_QA_PATH, DEFAULT_RETRIEVAL_QA_PATH
from evals.experiments import run_generation_eval as run_generation_eval_module


def test_compare_retrievers_cli_defaults():
    args = parse_compare_retrievers_args([])

    assert args.chunks == DEFAULT_CHUNKS_PATH
    assert args.qa == DEFAULT_RETRIEVAL_QA_PATH
    assert args.top_k == 5


def test_run_generation_eval_cli_defaults():
    args = run_generation_eval_module.parse_args([])

    assert args.chunks == DEFAULT_CHUNKS_PATH
    assert args.qa == DEFAULT_GENERATION_QA_PATH
    assert args.retriever == "hybrid"
    assert args.top_k == 5
    assert args.guardrails is True


def test_run_generation_eval_passes_top_k_to_answer_generator(monkeypatch):
    seen_top_k: list[int | None] = []

    class DummyRetriever:
        backend_name = "dummy"

    class DummyContextBuilder:
        def __init__(self, store, retriever=None):
            self.store = store
            self.retriever = retriever

    class DummyAnswerGenerator:
        def __init__(self, context_builder, guardrails):
            self.context_builder = context_builder
            self.guardrails = guardrails

        def answer(self, question, debug=True, top_k=None):
            seen_top_k.append(top_k)
            return {
                "answer": "stub answer",
                "citations": [{"chunk_id": "chunk-1"}],
                "confidence": 0.8,
                "refusal": False,
                "refusal_reason": None,
                "retrieval_debug": {"chunk_ids": ["chunk-1"]},
            }

    class DummyChunkIndexStore:
        @staticmethod
        def from_jsonl(path):
            return object()

    monkeypatch.setattr(run_generation_eval_module, "AnswerGenerator", DummyAnswerGenerator)
    monkeypatch.setattr(run_generation_eval_module, "ContextBuilder", DummyContextBuilder)
    monkeypatch.setattr(run_generation_eval_module, "ChunkIndexStore", DummyChunkIndexStore)
    monkeypatch.setattr(run_generation_eval_module, "build_retriever", lambda config, store: DummyRetriever())
    monkeypatch.setattr(
        run_generation_eval_module,
        "load_jsonl",
        lambda path: [
            {
                "question_id": "q1",
                "question": "Question?",
                "expected_answer": "Expected answer",
                "is_answerable": True,
                "category": "general",
                "relevant_chunk_ids": ["chunk-1"],
            }
        ],
    )

    payload = run_generation_eval_module.run_generation_eval(
        run_generation_eval_module.GenerationEvalConfig(
            chunks_path="chunks.jsonl",
            qa_path="qa.jsonl",
            top_k=3,
        )
    )

    assert seen_top_k == [3]
    assert payload["config"]["top_k"] == 3
