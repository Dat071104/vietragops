"""Gate 08 report assembly and dataset diagnostics."""

from __future__ import annotations

import json

import pytest

from research.gate08.harness import EVAL_FAMILIES
from research.gate08.metrics.diagnostics import oracle_reachability
from research.gate08.metrics.report import COMPARED_METRICS, build_report


def test_oracle_reachability_covers_every_evaluated_family():
    result = oracle_reachability()
    assert set(result["families"]) == set(EVAL_FAMILIES)
    for family, bucket in result["families"].items():
        assert bucket["unreachable_pairs"] <= bucket["pairs"]
        if bucket["pairs"]:
            assert 0.0 <= bucket["unreachable_share"] <= 1.0
            assert bucket["max_attainable_recall"] == pytest.approx(1.0 - bucket["unreachable_share"])


def test_argument_split_ground_truth_is_fully_reachable():
    """The claim family Gate 07 leaned on must not be capped by its own oracle."""
    assert oracle_reachability()["families"]["argument_split"]["unreachable_pairs"] == 0


def test_no_equivalent_accuracy_is_compared():
    assert "no_equivalent_accuracy" in COMPARED_METRICS


def test_report_rejects_a_non_gate08_protocol(tmp_path):
    protocol = tmp_path / "protocol.json"
    protocol.write_text(json.dumps({"schema": "gate07.protocol.v4"}), encoding="utf-8")
    decisions = tmp_path / "decisions.jsonl"
    decisions.write_text("", encoding="utf-8")
    with pytest.raises(ValueError):
        build_report(protocol, decisions, {})
