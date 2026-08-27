"""Deterministic unit tests for offline Gate 07 scoring."""

from __future__ import annotations

from research.gate07.baselines.offline import predict_lexical


def _task():
    contract = {
        "name": "find_module",
        "description": "Find a module by its exact course code.",
        "input_schema": {"type": "object", "properties": {"course_code": {"type": "string"}}, "required": ["course_code"]},
        "output_schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
        "preconditions": [],
        "effects": [],
    }
    decoy = {**contract, "name": "browse_catalog", "description": "Search many modules by free text."}
    return {"case_id": "fixture", "old_contracts": [contract], "new_contracts": [decoy, contract], "candidate_new_tool_names": ["browse_catalog", "find_module"]}


def test_gate07_lexical_name_arm_is_deterministic_and_ranked():
    first, first_scores = predict_lexical(_task(), names_only=True)
    second, second_scores = predict_lexical(_task(), names_only=True)
    assert first == second
    assert first_scores == second_scores
    assert first["ranked_tool_names"][0] == "find_module"


def test_gate07_lexical_arm_can_produce_argument_quadruples():
    prediction, _ = predict_lexical(_task(), names_only=False)
    assert prediction["argument_pairs"]
    assert all(pair[2] == prediction["selected_tool_names"][0] for pair in prediction["argument_pairs"])
