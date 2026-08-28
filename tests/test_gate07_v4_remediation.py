"""Gate 07 V4 remediation tests for ordering, abstention, intervals, and execution."""

from __future__ import annotations

from collections import Counter

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.baselines.controls import predict_positional_prior, predict_random_choice
from research.gate07.dataset import build_all_cases, build_v4_cases
from research.gate07.harness.serialization import task_record
from research.gate07.metrics.execution import evaluate_first_attempt
from research.gate07.metrics.scoring import _proportion_summary, _summary, score_prediction
from research.gate07.oracle import Gate07GroundTruth
from research.gate07.protocol import build_protocol_v4, candidate_order_digest


def test_gate07_v4_candidate_order_is_shuffled_and_not_positionally_concentrated():
    v3_cases = build_all_cases()
    v4_cases = build_v4_cases()
    assert all(case.candidate_permutation == tuple(range(len(case.candidate_permutation))) for case in v3_cases)
    answerable = [case for case in v4_cases if case.new_tool_names]
    assert len(answerable) == 198
    indices = Counter(case.candidate_new_tool_names.index(case.new_tool_names[0]) for case in answerable)
    assert set(indices) == {0, 1, 2, 3, 4}
    assert max(abs(indices[index] - len(answerable) / 5) for index in range(5)) <= 20
    for family in {case.family for case in answerable}:
        zero_count = sum(case.candidate_new_tool_names.index(case.new_tool_names[0]) == 0 for case in answerable if case.family == family)
        assert zero_count < 9


def test_gate07_v4_public_task_does_not_expose_candidate_permutation():
    task = task_record(next(case for case in build_v4_cases() if not case.held_out))
    assert "candidate_permutation" not in task
    assert "candidate_new_tool_names" in task


def test_gate07_v4_abstention_does_not_remove_best_candidate_from_scores():
    truth = Gate07GroundTruth("fixture", "argument_split", ("old",), ("new",), (), (), (), (), "fixture")
    metric = score_prediction(
        {
            "best_candidate_tool_names": ["new"],
            "argument_mapping": [],
            "equivalence_verdict": "equivalent_under_stated_convention",
            "confidence": 0.2,
            "abstain": True,
        },
        truth,
    )
    assert metric.tool_alignment_at_1 == 1.0
    assert metric.abstention_rate == 1.0


def test_gate07_v4_wilson_and_degenerate_interval_are_distinguished():
    proportion = _proportion_summary([0.0] * 13)
    assert proportion["interval_method"] == "wilson"
    assert proportion["ci95"][1] > 0.0
    continuous = _summary([0.0] * 13, seed=1, bootstrap_samples=50)
    assert continuous["degenerate"] is True
    assert continuous["ci95"] == [0.0, 0.0]


def test_gate07_v4_wrong_split_is_a_first_attempt_failure():
    case = next(case for case in build_v4_cases() if case.case_id == "G07-G-0075")
    mapping = [
        {
            "old_tool": old_tool,
            "old_arg": old_arg,
            "new_tool": new_tool,
            "new_arg": new_arg,
            "value_transform": {"kind": "split", "delimiter": "-", "part": "prefix" if new_arg == "subject_area" else "suffix"},
        }
        for old_tool, old_arg, new_tool, new_arg in case.argument_pairs
    ]
    prediction = {
        "best_candidate_tool_names": list(case.new_tool_names),
        "argument_mapping": mapping,
        "constructed_argument_values": [],
        "equivalence_verdict": "equivalent_under_stated_convention",
        "confidence": 0.8,
        "abstain": False,
    }
    assert evaluate_first_attempt(case, task_record(case), prediction, EvaluatorCapability()).outcome == "succeeded"
    wrong = [dict(entry, value_transform={"kind": "split", "delimiter": "-", "part": "prefix"}) for entry in mapping]
    prediction["argument_mapping"] = wrong
    failed = evaluate_first_attempt(case, task_record(case), prediction, EvaluatorCapability())
    assert failed.outcome != "succeeded"
    assert failed.attempted_inputs[0]["catalog_number"] == "CRS"


def test_gate07_v4_controls_are_deterministic_and_use_public_candidates():
    task = task_record(next(case for case in build_v4_cases() if not case.held_out))
    positional = predict_positional_prior(task)
    random_choice = predict_random_choice(task)
    assert positional["best_candidate_tool_names"] == list(task["candidate_new_tool_names"][:1])
    assert len(random_choice["best_candidate_tool_names"]) == 1
    assert random_choice["best_candidate_tool_names"][0] in task["candidate_new_tool_names"]


def test_gate07_v4_protocol_declares_controls_and_fresh_budget():
    protocol = build_protocol_v4(build_v4_cases(), ("model/strong", "model/mid"), created_at="2026-08-28T00:00:00+00:00")
    assert protocol["schema"] == "gate07.protocol.v4"
    assert protocol["rate_limit_budget"]["base_calls"] == 1800
    assert protocol["dataset"]["candidate_order_oracle_sha256"] == candidate_order_digest(build_v4_cases())
    arm_ids = {arm["arm_id"] for arm in protocol["baseline_arms"]}
    assert {"positional_prior", "random_choice", "llm_old_new_direct_v3_legacy", "llm_old_new_direct"} <= arm_ids
    assert "tool_alignment_at_3" not in protocol["metrics"]
    assert "tool_alignment_at_5" not in protocol["metrics"]
