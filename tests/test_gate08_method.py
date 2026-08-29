"""Gate 08 method-interface and alignment behaviour."""

from __future__ import annotations

import json

import pytest

from research.gate07.baselines.llm import parse_v4_llm_payload
from research.gate07.harness.serialization import task_record
from research.gate08.ablations import ABLATIONS, ALL_CONFIGS, METHOD_ARM, REUSED_ABLATION, config_by_id
from research.gate08.harness import eval_cases
from research.gate08.method.alignment import TRANSFORM_KINDS, align
from research.gate08.method.calibration import Thresholds, confidence, verdict
from research.gate08.method.correspondence import DIMENSION_WEIGHTS, rank_candidates, score_candidate
from research.gate08.method.models import (
    METHOD_INTERFACE_DIGEST,
    ArgumentSemantics,
    CorrespondenceScore,
    IntentSignature,
    method_interface_digest,
)
from research.gate08.method.pipeline import run_case
from research.gate08.method.signature import (
    SignatureParseError,
    attach_observed_values,
    normalize_concept,
    parse_signature,
    split_composite,
)
from research.gate08.runner.store import literal_candidate_signatures, literal_old_signature


def _signature(side, tool, arguments, *, operation="read", entity="course", effects=()):
    return IntentSignature(
        side=side,
        tool_name=tool,
        operation=operation,
        primary_entity=entity,
        target_entity=None,
        precondition_targets=(),
        effects=effects,
        arguments=tuple(arguments),
        output_semantics=("record",),
    )


def _json_task(case):
    """Tasks reach a runner as JSON, so lists -- not tuples -- are the real shape."""
    return json.loads(json.dumps(task_record(case), default=str))


def _argument(name, concept, **kwargs):
    kwargs.setdefault("value_shape", "opaque_identifier")
    return ArgumentSemantics(name=name, concept=concept, **kwargs)


def test_interface_digest_is_stable_and_recomputable():
    assert METHOD_INTERFACE_DIGEST == method_interface_digest()
    assert METHOD_INTERFACE_DIGEST.startswith("sha256:")


def test_dimension_weights_sum_to_one():
    assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9


def test_normalize_concept_strips_system_suffixes():
    assert normalize_concept("student_id") == "student"
    assert normalize_concept("course_code") == "course"
    assert normalize_concept("Section-Ref") == "section"
    assert normalize_concept("") == "unknown"


def test_split_composite_detects_separator_only_for_strings():
    assert split_composite("CRS-011") == ("CRS", "-", "011")
    assert split_composite("CRS-021::TERM-01") == ("CRS", "-", "021::TERM-01")
    assert split_composite("plain") is None
    assert split_composite(7) is None


def test_parse_signature_rejects_unknown_vocabulary():
    payload = {
        "operation": "teleport",
        "primary_entity": "course",
        "target_entity": None,
        "effects": [],
        "arguments": [],
        "output_semantics": [],
    }
    with pytest.raises(SignatureParseError):
        parse_signature(payload, side="old", tool_name="t", precondition_targets=(), allowed_fields=None)


def test_parse_signature_rejects_fields_outside_the_supplied_schema():
    payload = {
        "operation": "read",
        "primary_entity": "course",
        "target_entity": None,
        "effects": [],
        "arguments": [{"name": "invented", "concept": "course", "value_shape": "opaque_identifier"}],
        "output_semantics": [],
    }
    with pytest.raises(SignatureParseError):
        parse_signature(payload, side="new", tool_name="t", precondition_targets=(), allowed_fields=frozenset({"course_code"}))


def test_attach_observed_values_is_deterministic_not_model_supplied():
    signature = _signature("old", "get_course_contact", [_argument("course_code", "course")])
    attached = attach_observed_values(
        signature,
        [{"tool_name": "get_course_contact", "normalized_input": {"course_code": "CRS-023"}}],
    )
    assert attached.arguments[0].observed_value == "CRS-023"
    assert attached.arguments[0].observed_delimiter == "-"


def test_alignment_pass_one_matches_by_concept():
    old = _signature("old", "old_tool", [_argument("student_id", "student", observed_value="STU-1")])
    new = _signature("new", "new_tool", [_argument("learner_ref", "student")])
    alignments, constructed, unmatched_new, unmatched_old = align(old, new, ("learner_ref",))
    assert [entry.value_transform["kind"] for entry in alignments] == ["identity"]
    assert constructed == {"learner_ref": "STU-1"}
    assert not unmatched_new and not unmatched_old


def test_residual_split_recovers_an_unannounced_split():
    old = _signature("old", "old_tool", [_argument("course_code", "course", observed_value="CRS-011")])
    new = _signature("new", "new_tool", [_argument("subject_area", "subject"), _argument("catalog_number", "catalog")])
    alignments, constructed, unmatched_new, unmatched_old = align(old, new, ("subject_area", "catalog_number"))
    assert [entry.value_transform["part"] for entry in alignments] == ["prefix", "suffix"]
    assert constructed == {"subject_area": "CRS", "catalog_number": "011"}
    assert not unmatched_new and not unmatched_old


def test_residual_merge_is_reported_but_never_given_an_invented_separator():
    old = _signature(
        "old",
        "old_tool",
        [_argument("course_code", "course", observed_value="CRS-021"), _argument("term_id", "term", observed_value="TERM-01")],
    )
    new = _signature("new", "new_tool", [_argument("section_ref", "section")])
    alignments, constructed, unmatched_new, unmatched_old = align(old, new, ("section_ref",))
    assert {entry.value_transform["kind"] for entry in alignments} == {"join_unresolved"}
    assert constructed == {}
    assert not unmatched_new and not unmatched_old
    assert all(kind in TRANSFORM_KINDS for kind in (entry.value_transform["kind"] for entry in alignments))


def test_literal_pass_uses_only_values_the_new_contract_states():
    old = _signature("old", "old_tool", [_argument("student_id", "student", observed_value="STU-1")])
    new = _signature(
        "new",
        "new_tool",
        [
            _argument("learner_ref", "student"),
            _argument("payment_status", "payment", value_shape="status_token", stated_literal="paid"),
            _argument("consent_ack", "consent", value_shape="boolean"),
        ],
    )
    _alignments, constructed, unmatched_new, _unmatched_old = align(
        old, new, ("learner_ref", "payment_status", "consent_ack")
    )
    assert constructed["payment_status"] == "paid"
    assert constructed["consent_ack"] is True
    assert not unmatched_new


def test_correspondence_rejects_a_mutation_mismatch():
    old = _signature("old", "a", [], operation="create", effects=(("creates_resource", "request"),))
    new = _signature("new", "b", [], operation="read", effects=(("no_mutation", "records"),))
    assert score_candidate(old, new).effect == 0.0


def test_ranking_is_by_score_then_name_not_by_candidate_order():
    old = _signature("old", "a", [_argument("course_code", "course")])
    candidates = {
        "zeta": _signature("new", "zeta", [_argument("course_code", "course")]),
        "alpha": _signature("new", "alpha", [_argument("course_code", "course")]),
    }
    ranked = rank_candidates(old, candidates)
    assert [score.tool_name for score in ranked] == ["alpha", "zeta"]


def test_all_three_verdicts_are_reachable():
    ranked = (CorrespondenceScore("t", 1.0, 1.0, 1.0, 1.0, 1.0, 0.9),)
    thresholds = Thresholds(retrieval_floor=0.5, abstain_floor=0.5)
    assert verdict(ranked, 0.9, thresholds) == "ALIGN"
    assert verdict(ranked, 0.1, thresholds) == "ABSTAIN"
    assert verdict((CorrespondenceScore("t", 0.0, 0.0, 0.0, 0.0, 0.0, 0.1),), 0.9, thresholds) == "NO_EQUIVALENT"


def test_disabling_calibration_removes_every_decline():
    thresholds = Thresholds(retrieval_floor=0.9, abstain_floor=0.9)
    ranked = (CorrespondenceScore("t", 0.0, 0.0, 0.0, 0.0, 0.0, 0.01),)
    assert verdict(ranked, 0.0, thresholds, calibration_enabled=False) == "ALIGN"


def test_confidence_is_bounded():
    ranked = (CorrespondenceScore("t", 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),)
    assert 0.0 <= confidence(ranked, required_field_count=2, resolved_field_count=2) <= 1.0
    assert confidence((), required_field_count=0, resolved_field_count=0) == 0.0


def test_six_required_ablations_are_declared():
    assert len(ABLATIONS) == 5
    assert REUSED_ABLATION["ablation_id"] == "ablate_direct_frontier_llm_mapper"
    assert REUSED_ABLATION["re_collected"] is False
    assert {config.arm_id for config in ALL_CONFIGS} == {
        "gate08_method",
        "ablate_no_history",
        "ablate_schema_only",
        "ablate_no_intent_abstraction",
        "ablate_no_preconditions_effects",
        "ablate_no_calibration",
    }
    assert config_by_id("gate08_method") == METHOD_ARM


def test_resolved_payload_satisfies_the_gate07_v4_prediction_contract():
    case = next(case for case in eval_cases() if case.family == "argument_split")
    task = _json_task(case)
    decision, payload = run_case(
        task,
        literal_old_signature(task, with_traces=True),
        literal_candidate_signatures(task),
        Thresholds(0.0, 0.0),
        config_by_id("ablate_no_intent_abstraction"),
    )
    assert decision.verdict in {"ALIGN", "ABSTAIN", "NO_EQUIVALENT"}
    if all(not str(entry["value_transform"]["kind"]).endswith("_unresolved") for entry in payload["argument_mapping"]):
        parsed = parse_v4_llm_payload(payload, task)
        assert parsed["best_candidate_tool_names"] == payload["best_candidate_tool_names"]


def test_unresolved_transform_is_rejected_by_the_gate07_v4_contract():
    """The boundary is deliberate: an unconstructible value is never a V4 call."""
    case = next(case for case in eval_cases() if case.family == "tool_replacement")
    task = _json_task(case)
    _decision, payload = run_case(
        task,
        literal_old_signature(task, with_traces=True),
        literal_candidate_signatures(task),
        Thresholds(0.0, 0.0),
        config_by_id("ablate_no_intent_abstraction"),
    )
    if any(str(entry["value_transform"]["kind"]).endswith("_unresolved") for entry in payload["argument_mapping"]):
        with pytest.raises(ValueError):
            parse_v4_llm_payload(payload, task)
