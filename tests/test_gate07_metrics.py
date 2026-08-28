"""Hand-computed Gate 07 metric fixtures."""

from __future__ import annotations

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.dataset import build_all_cases
from research.gate07.harness.serialization import task_record
from research.gate07.metrics import aggregate_predictions, evaluate_first_attempt, score_prediction
from research.gate07.metrics.report import summarize_values
from research.gate07.oracle import Gate07GroundTruth


def test_gate07_exact_argument_precision_recall_fixture():
    truth = Gate07GroundTruth(
        case_id="fixture",
        family="argument_split",
        old_tool_names=("old",),
        correct_new_tool_names=("new",),
        argument_pairs=(("old", "module", "new", "subject"), ("old", "module", "new", "number")),
        new_only_required_fields=(),
        expected_effect_kinds=("no_mutation",),
        output_field_mapping=(),
        rationale="fixture",
    )
    row = score_prediction({"case_id": "fixture", "selected_tool_names": ["new"], "ranked_tool_names": ["new"], "argument_pairs": [["old", "module", "new", "subject"], ["old", "extra", "new", "number"]]}, truth)
    assert row.tool_alignment_at_1 == 1.0
    assert row.argument_precision == 0.5
    assert row.argument_recall == 0.5
    assert row.argument_f1 == 0.5


def test_gate07_no_equivalent_and_many_to_many_fixture():
    no_equivalent = Gate07GroundTruth("none", "no_equivalent", ("old",), (), (), (), (), (), "fixture")
    assert score_prediction({"case_id": "none", "abstain": True, "ranked_tool_names": []}, no_equivalent).no_equivalent_accuracy == 1.0
    d9 = Gate07GroundTruth("d9", "one_old_to_multiple_new", ("old",), ("a", "b"), (), (), (), (), "fixture")
    row = score_prediction({"case_id": "d9", "selected_tool_names": ["a"], "ranked_tool_names": ["a", "b"]}, d9)
    assert row.tool_alignment_at_1 == 0.0
    assert row.abstention_rate == 0.0


def test_gate07_aggregate_has_deterministic_uncertainty_shape():
    case = build_all_cases()[0]
    predictions = [{"case_id": case.case_id, "selected_tool_names": [case.candidate_new_tool_names[0]], "ranked_tool_names": list(case.candidate_new_tool_names)}]
    result = aggregate_predictions(predictions, EvaluatorCapability(), bootstrap_samples=50)
    assert result["case_count"] == 1
    assert result["overall"]["tool_alignment_at_1"]["mean"] in {0.0, 1.0}


def test_gate07_first_attempt_executes_a_correct_adaptation_in_a_fresh_sandbox():
    case = build_all_cases()[0]
    prediction = {"case_id": case.case_id, "selected_tool_names": [case.new_tool_names[0]], "argument_pairs": [list(pair) for pair in case.argument_pairs], "abstain": False}
    result = evaluate_first_attempt(case, task_record(case), prediction, EvaluatorCapability())
    assert result.outcome == "succeeded"


def test_gate07_first_attempt_treats_no_equivalent_abstention_as_safe_success():
    case = next(case for case in build_all_cases() if case.family == "no_equivalent")
    result = evaluate_first_attempt(case, task_record(case), {"case_id": case.case_id, "selected_tool_names": [], "abstain": True}, EvaluatorCapability())
    assert result.outcome == "succeeded"


def test_gate07_bootstrap_summary_is_deterministic_and_reports_n():
    first = summarize_values([0.0, 1.0, 1.0], seed=123, bootstrap_samples=50)
    second = summarize_values([0.0, 1.0, 1.0], seed=123, bootstrap_samples=50)
    assert first == second
    assert first["n"] == 3
