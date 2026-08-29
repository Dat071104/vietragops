"""Gate 08 protocol freeze and preflight."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.gate07.protocol.freeze import FreezePreflightError
from research.gate08.protocol import build_protocol, preflight_gate08_run, surface_digest, write_protocol

MODELS = ("openai/gpt-oss-120b", "openai/gpt-oss-20b")


def _protocol():
    return build_protocol(model_ids=MODELS, cost_cap_usd=1.20, created_at="2026-08-29T00:00:00Z")


def test_protocol_records_everything_a_rerun_needs():
    protocol = _protocol()
    assert protocol["schema"] == "gate08.protocol.v1"
    assert protocol["git_head_at_freeze"]
    assert protocol["dataset"]["graded_manifest_sha256"].startswith("sha256:")
    assert protocol["dataset"]["held_out_manifest_sha256"].startswith("sha256:")
    assert protocol["method"]["interface_digest"].startswith("sha256:")
    assert protocol["evaluation_surface"]["eval_case_count"] == 45
    assert protocol["evaluation_surface"]["calibration_case_count"] == 36
    assert protocol["evaluation_surface"]["calibration_split"] == "held_out"
    assert protocol["provider"]["mode"] == "research"
    assert protocol["provider"]["fallback"] == "disabled"
    assert protocol["provider"]["cost_cap_usd"] == 1.20
    assert len(protocol["arms"]) == 6
    assert protocol["reused_ablation"]["re_collected"] is False


def test_surface_is_byte_identical_to_the_frozen_gate07_v4_surface():
    """The comparison is only fair if both sides saw the same candidate lists."""
    gate07 = json.loads(
        (Path(__file__).resolve().parents[1] / "gates" / "baselines" / "GATE_07_PROTOCOL_V4.json").read_text(encoding="utf-8")
    )["dataset"]
    gate08 = _protocol()["dataset"]
    assert gate08["graded_manifest_sha256"] == gate07["graded_manifest_sha256"]
    assert gate08["held_out_manifest_sha256"] == gate07["held_out_manifest_sha256"]
    assert gate08["candidate_order"] == gate07["candidate_order"] == "v4_seeded_permutation"
    assert gate08["candidate_order_oracle_sha256"] == gate07["candidate_order_oracle_sha256"]


def test_protocol_pins_every_prompt_by_digest():
    protocol = _protocol()
    prompts = protocol["method"]["prompts"]
    assert len(prompts) == 4
    assert all(entry["text_sha256"].startswith("sha256:") for entry in prompts)
    assert {entry["side"] for entry in prompts} == {"old", "new"}
    new_side = [entry for entry in prompts if entry["side"] == "new"]
    assert all("old_contract" not in entry["information_rights"] for entry in new_side)
    assert all("verified_old_traces" not in entry["information_rights"] for entry in new_side)


def test_surface_digest_is_deterministic():
    assert surface_digest() == surface_digest()


def test_preflight_rejects_an_untracked_protocol(tmp_path):
    target = tmp_path / "GATE_08_PROTOCOL.json"
    write_protocol(_protocol(), target)
    with pytest.raises(FreezePreflightError):
        preflight_gate08_run(target)


def test_preflight_rejects_a_changed_method_interface(tmp_path, monkeypatch):
    protocol = _protocol()
    protocol["method"]["interface_digest"] = "sha256:" + "0" * 64
    target = tmp_path / "protocol.json"
    target.write_text(json.dumps(protocol), encoding="utf-8")
    with pytest.raises(FreezePreflightError):
        preflight_gate08_run(target)


def test_committed_protocol_passes_preflight_when_present():
    committed = Path(__file__).resolve().parents[1] / "gates" / "baselines" / "GATE_08_PROTOCOL.json"
    if not committed.exists():
        pytest.skip("Gate 08 protocol has not been frozen yet")
    receipt = preflight_gate08_run("gates/baselines/GATE_08_PROTOCOL.json")
    assert receipt["status"] == "passed"
    assert receipt["method_interface_digest"].startswith("sha256:")
