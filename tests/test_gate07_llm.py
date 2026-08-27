"""Gate 07 LLM prompt/parser and rate-ledger unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from research.gate07.baselines.llm import parse_llm_payload, render_llm_prompt
from research.gate07.runner.rate_ledger import RateLimitLedger, RateLimits


def _task():
    return {
        "case_id": "G07-G-0001",
        "task_description": "For the supplied synthetic record, find a course.",
        "old_contracts": [{"name": "search_course", "description": "Find one course."}],
        "new_contracts": [{"name": "find_module", "description": "Find one module."}, {"name": "browse_catalog", "description": "Search modules."}],
        "candidate_new_tool_names": ["find_module", "browse_catalog"],
        "verified_old_traces": [],
    }


def test_gate07_prompt_rendering_has_no_hidden_fields():
    prompt_id, prompt = render_llm_prompt("llm_old_new_history", _task())
    assert prompt_id == "gate07-llm-history-v1"
    assert "G07-G-0001" not in prompt  # case id is not included in the template
    assert "family" not in prompt and "lineage_key" not in prompt and "20260827" not in prompt
    assert "search_course" in prompt and "find_module" in prompt


def test_gate07_parser_accepts_abstention_and_rejects_leaks():
    parsed = parse_llm_payload({"selected_tool_names": [], "argument_mapping": [], "abstain": True}, _task())
    assert parsed["abstain"] is True
    with pytest.raises(ValueError):
        parse_llm_payload({"selected_tool_names": ["secret_tool"], "argument_mapping": [], "abstain": False}, _task())


def test_gate07_rate_ledger_enforces_declared_ceiling(tmp_path: Path):
    limits = RateLimits(per_key={"rpm": 10, "tpm": 1000, "rpd": 10, "tpd": 1000}, pool={"rpm": 1, "tpm": 1000, "rpd": 10, "tpd": 1000}, org={"rpm": 10, "tpm": 1000, "rpd": 10, "tpd": 1000}, reserve_fraction=0.0)
    ledger = RateLimitLedger(tmp_path / "router.sqlite3", tmp_path / "requests.jsonl", limits)
    allowed, reason = ledger.allow(10, 10)
    assert allowed and reason is None
    ledger.record(arm_id="arm", model="model", case_id="case", input_tokens=10, output_tokens=10, outcome="success")
    allowed, reason = ledger.allow(10, 10)
    assert allowed is False and reason == "pool_rpm"
    ledger.close()
