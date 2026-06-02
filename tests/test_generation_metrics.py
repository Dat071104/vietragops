from evals.metrics.generation_metrics import aggregate_generation_metrics, token_f1


def test_token_f1_positive_overlap():
    assert token_f1("Cấu trúc email MSSV@student.tdtu.edu.vn", "email MSSV@student.tdtu.edu.vn") > 0.5


def test_aggregate_generation_metrics():
    metrics = aggregate_generation_metrics(
        [
            {
                "expected_answer": "abc def",
                "answer": "abc def",
                "citations_valid": True,
                "is_answerable": True,
            }
        ]
    )
    assert metrics["exact_match"] == 1.0
    assert metrics["citation_support_rate"] == 1.0
