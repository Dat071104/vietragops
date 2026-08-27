import pytest

from research.gate0.drift import build_case_manifest
from research.gate0.evaluator import (
    NO_EQUIVALENT,
    EvaluatorCapability,
    ProposedMapping,
    evaluate_adapted_call,
    evaluate_mapping,
)
from research.gate0.oracle import get_ground_truth

CAP = EvaluatorCapability()


def _correct_proposal(case_id: str) -> ProposedMapping:
    gt = get_ground_truth(case_id, CAP)
    if gt.correct_new_tool_name is None:
        return ProposedMapping(case_id=case_id, predicted_new_tool_name=NO_EQUIVALENT)
    return ProposedMapping(
        case_id=case_id,
        predicted_new_tool_name=gt.correct_new_tool_name,
        predicted_argument_mapping=dict(gt.argument_mapping),
    )


@pytest.mark.parametrize("case", build_case_manifest(), ids=lambda c: c.case_id)
def test_correct_proposal_is_scored_correct_for_every_family(case):
    result = evaluate_mapping(_correct_proposal(case.case_id), CAP)
    assert result.overall_correct is True
    assert result.failure_reasons == ()
    assert result.family == case.family


def test_all_nine_families_are_exercised_by_the_manifest():
    families = {case.family for case in build_case_manifest()}
    assert len(families) == 9
    for case in build_case_manifest():
        result = evaluate_mapping(_correct_proposal(case.case_id), CAP)
        assert result.overall_correct is True


def test_semantic_near_collision_decoy_is_scored_wrong_for_the_right_reason():
    case = next(c for c in build_case_manifest() if c.family == "semantic_near_collision")
    decoy = ProposedMapping(case_id=case.case_id, predicted_new_tool_name="browse_catalog", predicted_argument_mapping={"course_code": "query_text"})
    result = evaluate_mapping(decoy, CAP)
    assert result.overall_correct is False
    assert result.tool_selection_correct is False
    assert "wrong_tool_selected" in result.failure_reasons


def test_no_equivalent_case_rejects_a_forced_nearest_tool_answer():
    case = next(c for c in build_case_manifest() if c.family == "no_equivalent")
    forced = ProposedMapping(case_id=case.case_id, predicted_new_tool_name=case.candidate_new_tool_names[0])
    result = evaluate_mapping(forced, CAP)
    assert result.no_equivalent_expected is True
    assert result.no_equivalent_predicted is False
    assert result.no_equivalent_correct is False
    assert result.overall_correct is False
    assert "missed_no_equivalent" in result.failure_reasons


def test_false_no_equivalent_on_a_real_correspondence_is_scored_wrong():
    case = next(c for c in build_case_manifest() if c.family == "tool_rename")
    over_cautious = ProposedMapping(case_id=case.case_id, predicted_new_tool_name=NO_EQUIVALENT)
    result = evaluate_mapping(over_cautious, CAP)
    assert result.no_equivalent_correct is False
    assert "false_no_equivalent" in result.failure_reasons


def test_partial_argument_mapping_is_penalized_by_recall_not_hidden():
    case = next(c for c in build_case_manifest() if c.family == "argument_split")
    gt = get_ground_truth(case.case_id, CAP)
    partial = ProposedMapping(
        case_id=case.case_id,
        predicted_new_tool_name=gt.correct_new_tool_name,
        predicted_argument_mapping={"program_code": "program_code", "module_code": "subject_area"},  # missing catalog_number
    )
    result = evaluate_mapping(partial, CAP)
    assert result.overall_correct is False
    assert ("module_code", "catalog_number") in result.argument_pairs_missed
    assert result.argument_recall < 1.0


def test_spurious_argument_mapping_on_a_dropped_field_is_penalized():
    case = next(c for c in build_case_manifest() if c.family == "tool_replacement")
    gt = get_ground_truth(case.case_id, CAP)
    over_mapped = dict(gt.argument_mapping)
    over_mapped["consent_ack"] = "payment_status"  # consent_ack has no real successor
    proposal = ProposedMapping(case_id=case.case_id, predicted_new_tool_name=gt.correct_new_tool_name, predicted_argument_mapping=over_mapped)
    result = evaluate_mapping(proposal, CAP)
    assert result.overall_correct is False
    assert ("consent_ack", "payment_status") in result.argument_pairs_spurious


def test_evaluation_is_repeatable_across_separate_process_invocations():
    import subprocess
    import sys

    script = (
        "from research.gate0.drift import build_case_manifest\n"
        "from research.gate0.evaluator import EvaluatorCapability, ProposedMapping, evaluate_mapping\n"
        "from research.gate0.oracle import get_ground_truth\n"
        "cap = EvaluatorCapability()\n"
        "case = build_case_manifest()[0]\n"
        "gt = get_ground_truth(case.case_id, cap)\n"
        "proposal = ProposedMapping(case_id=case.case_id, predicted_new_tool_name=gt.correct_new_tool_name, predicted_argument_mapping=dict(gt.argument_mapping))\n"
        "result = evaluate_mapping(proposal, cap)\n"
        "print(result.overall_correct, result.failure_reasons)\n"
    )
    outputs = []
    for _ in range(2):
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        outputs.append(completed.stdout.strip())
    assert outputs[0] == outputs[1]
    assert outputs[0] == "True ()"


@pytest.mark.parametrize("case", build_case_manifest(), ids=lambda c: c.case_id)
def test_evaluation_is_repeatable_across_multiple_resets(case):
    results = [evaluate_mapping(_correct_proposal(case.case_id), CAP) for _ in range(5)]
    assert all(r == results[0] for r in results)


def test_evaluate_mapping_rejects_non_capability_caller():
    case_id = build_case_manifest()[0].case_id
    with pytest.raises(PermissionError):
        evaluate_mapping(_correct_proposal(case_id), capability="nope")  # type: ignore[arg-type]


def test_adapted_call_succeeds_for_the_correct_tool_and_real_arguments():
    case = next(c for c in build_case_manifest() if c.family == "tool_rename")
    result = evaluate_adapted_call(case.case_id, "find_module", {"course_code": "CRS-101"}, CAP)
    assert result.outcome == "succeeded"
    assert result.output_expectation_met is True


def test_adapted_call_reports_precondition_failure_not_a_crash():
    case = next(c for c in build_case_manifest() if c.family == "tool_replacement")
    result = evaluate_adapted_call(
        case.case_id,
        "finalize_registration",
        {"learner_ref": "STU-0001", "section_code": "CRS-101::TERM-2026A", "payment_status": "unpaid"},
        CAP,
    )
    assert result.outcome == "precondition_failed"
    assert result.error is not None


def test_adapted_call_on_no_equivalent_case_is_always_wrong():
    case = next(c for c in build_case_manifest() if c.family == "no_equivalent")
    result = evaluate_adapted_call(case.case_id, case.candidate_new_tool_names[0], {}, CAP)
    assert result.outcome == "wrong_tool"


def test_adapted_call_never_leaves_isolated_sandbox_state():
    import hashlib
    import json

    from research.gate0.sandbox import EducationSandboxStore

    baseline = EducationSandboxStore().state_hash()
    case = next(c for c in build_case_manifest() if c.family == "tool_rename")
    evaluate_adapted_call(case.case_id, "find_module", {"course_code": "CRS-101"}, CAP)
    # A brand-new store must still hash identically -- nothing escaped the evaluator's own temporary store.
    assert EducationSandboxStore().state_hash() == baseline
    assert isinstance(hashlib.sha256(json.dumps({}).encode()).hexdigest(), str)  # sanity: hashing itself is deterministic


def test_no_llm_or_model_dependency_anywhere_in_the_evaluator():
    import research.gate0.evaluator.evaluator as ev_module

    source = open(ev_module.__file__, encoding="utf-8").read()
    for banned in ("groq", "ollama", "openai", "anthropic", "requests.", "httpx.", "generate_json"):
        assert banned.lower() not in source.lower()
