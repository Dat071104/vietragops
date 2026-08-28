"""Gate 07 protocol-freeze structure tests."""

from __future__ import annotations

import json
from pathlib import Path

from research.gate07.dataset import build_all_cases
from research.gate07.protocol import build_protocol


def test_gate07_protocol_freezes_dataset_rights_metrics_and_exclusions():
    protocol = build_protocol(build_all_cases(), ("model/strong", "model/mid"), created_at="2026-08-27T00:00:00+00:00")
    assert protocol["dataset"]["graded_count"] == 180
    assert protocol["dataset"]["held_out_count"] == 36
    assert set(protocol["dataset"]["family_counts"].values()) == {15}
    assert set(protocol["dataset"]["held_out_family_counts"].values()) == {3}
    assert protocol["ground_truth"]["graded_sha256"].startswith("sha256:")
    assert len(protocol["baseline_arms"]) == 9
    allowed = {"old_contract", "new_contracts", "verified_old_traces", "task_description", "candidate_list"}
    assert all(set(arm["information_rights"]) <= allowed for arm in protocol["baseline_arms"])
    assert "many_to_many_scoring" in protocol["metrics"]
    assert "provider_failure" in protocol["exclusions"]
    assert protocol["rate_limit_budget"]["base_calls"] == 1440
    assert protocol["rate_limit_budget"]["max_attempts"] == 4320


def test_gate07_protocol_prompt_templates_are_renderable_and_versioned():
    protocol = build_protocol(build_all_cases(), ("model/strong", "model/mid"), created_at="2026-08-27T00:00:00+00:00")
    templates = protocol["prompt_templates"]
    assert {"llm_new_schema_only", "llm_old_new_direct", "llm_old_new_history", "llm_reasoning"} == set(templates)
    assert all(template["prompt_id"].startswith("gate07-") and template["version"] == "gate07-llm-v1" for template in templates.values())
    assert "selected_tool_names" in templates["llm_new_schema_only"]["text"]


def test_gate07_frozen_protocol_file_contains_no_credentials_and_precedes_headline_run():
    path = Path(__file__).parents[1] / "gates" / "baselines" / "GATE_07_PROTOCOL.json"
    protocol = json.loads(path.read_text(encoding="utf-8"))
    assert protocol["schema"] == "gate07.protocol.v1"
    assert protocol["git_head_at_freeze"] == "44be1410af557a11557dfe339a08fb6d2af3660e"
    assert protocol["rate_limit_budget"]["safety_reserve_fraction"] == 0.2
    serialized = json.dumps(protocol, ensure_ascii=True).casefold()
    assert "api_key" not in serialized
    assert "secret" not in serialized
    assert protocol["models"]["verification"]["http_status"] == 403


def test_gate07_protocol_v2_records_pre_headline_seed_leakage_amendment():
    path = Path(__file__).parents[1] / "gates" / "baselines" / "GATE_07_PROTOCOL_V2.json"
    protocol = json.loads(path.read_text(encoding="utf-8"))
    assert protocol["schema"] == "gate07.protocol.v2"
    assert protocol["amendment"]["amends"] == "GATE_07_PROTOCOL.json"
    assert protocol["amendment"]["headline_runs_before_amendment"] is False
    assert protocol["amendment"]["amendment_commit_status_at_headline_start"] == "NOT_COMMITTED"
    assert protocol["amendment"]["headline_start_git_head"] == "3b6770f673523f093e9e3ff54c0133a2f24c7413"
    assert protocol["dataset"]["graded_manifest_sha256"] == "sha256:32f0d29279dbbeb28ea7c3db1d076334242c7b2c092f4ac09cc32f8fb927890e"
