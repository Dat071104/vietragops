from evals.metrics.abstention_metrics import aggregate_abstention_metrics


def test_abstention_metrics():
    metrics = aggregate_abstention_metrics(
        [
            {"is_answerable": False, "refusal": True},
            {"is_answerable": True, "refusal": False},
        ]
    )
    assert metrics["refusal_accuracy"] == 1.0
    assert metrics["unsupported_answer_rate"] == 0.0
