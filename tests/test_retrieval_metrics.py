from evals.metrics.retrieval_metrics import aggregate_retrieval_metrics, precision_at_k, recall_at_k, reciprocal_rank


def test_basic_retrieval_metrics():
    assert recall_at_k(["c1", "c2"], ["c2", "c5"], 1) == 0.5
    assert precision_at_k(["c1", "c2"], ["c2", "c5"], 2) == 0.5
    assert reciprocal_rank(["c3"], ["c1", "c3", "c4"]) == 0.5


def test_aggregate_metrics_only_score_answerable_queries():
    qa_items = [
        {
            "question_id": "q1",
            "relevant_chunk_ids": ["c1"],
            "is_answerable": True,
        },
        {
            "question_id": "q2",
            "relevant_chunk_ids": [],
            "is_answerable": False,
        },
    ]
    predictions = [
        {"question_id": "q1", "predicted_chunk_ids": ["c1", "c2"], "latency_ms": 12.3},
        {"question_id": "q2", "predicted_chunk_ids": ["c5"], "latency_ms": 11.1},
    ]

    aggregated = aggregate_retrieval_metrics(qa_items, predictions)

    assert aggregated["metrics"]["recall_at_3"] == 1.0
    assert aggregated["metrics"]["mrr"] == 1.0
    assert aggregated["metrics"]["answerable_query_count"] == 1
    assert aggregated["metrics"]["total_query_count"] == 2
