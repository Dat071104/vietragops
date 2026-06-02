from evals.experiments.run_generation_eval import GenerationEvalConfig


def test_generation_eval_config_defaults():
    config = GenerationEvalConfig(chunks_path="chunks.jsonl", qa_path="qa.jsonl")
    assert config.retriever == "hybrid"
    assert config.top_k == 5
