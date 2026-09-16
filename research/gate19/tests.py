"""Offline tests for the Gate 19 reachability auditor.

This file is intentionally named ``tests.py`` so the existing 612-test suite
remains an entry receipt. Run it explicitly with pytest for the Gate 19 checks.
"""

from __future__ import annotations

from research.gate19.auditor import (
    CONVENTION_UNOBSERVABLE,
    REACHABLE,
    TARGET_ABSENT,
    audit_items,
    build_gate07_items,
    build_gate07_required_field_items,
)


RIGHTS = {"schema": "test.rights.v1"}


def _item(*, fields: list[str], target: str, sources: list[str], visible: str) -> dict:
    return {
        "item_id": "test-item",
        "new_tool": "new_tool",
        "new_arg": "target",
        "target_value": target,
        "source_values": sources,
        "visible_source_values": sources,
        "visible_text": [visible],
        "new_contract_fields": {"new_tool": fields},
    }


def test_reachable_identity_item_passes() -> None:
    result = audit_items([_item(fields=["target"], target="A", sources=["A"], visible="A")], RIGHTS)
    assert result["items"][0]["status"] == REACHABLE


def test_target_absent_item_is_flagged() -> None:
    result = audit_items([_item(fields=[], target="A", sources=["A"], visible="A")], RIGHTS)
    assert result["items"][0]["status"] == TARGET_ABSENT


def test_hidden_separator_is_flagged_as_unobservable_convention() -> None:
    item = _item(fields=["target"], target="A::B", sources=["A", "B"], visible="A B")
    result = audit_items([item], RIGHTS)
    assert result["items"][0]["status"] == CONVENTION_UNOBSERVABLE


def test_omitting_a_needed_field_flips_reachable_to_unreachable() -> None:
    item = _item(fields=["target"], target="A", sources=["A"], visible="A")
    reachable = audit_items([item], RIGHTS)["items"][0]["status"]
    item["new_contract_fields"] = {"new_tool": []}
    absent = audit_items([item], RIGHTS)["items"][0]["status"]
    assert reachable == REACHABLE
    assert absent == TARGET_ABSENT


def test_frozen_gate07_reproduction_counts() -> None:
    result = audit_items(build_gate07_items(), {"schema": "gate19.information_rights.v1"})
    replacement = result["families"]["tool_replacement"]
    split = result["families"]["argument_split"]
    assert replacement["pairs"] == 35
    assert replacement["status_counts"][TARGET_ABSENT] == 10
    assert replacement["status_counts"][CONVENTION_UNOBSERVABLE] == 10
    assert replacement["convention_case_count"] == 5
    assert replacement["case_count"] == 15
    assert split["pairs"] == 40
    assert split["unreachable_pairs"] == 0


def test_required_field_scan_is_separate_and_finds_hidden_ack_defaults() -> None:
    result = audit_items(build_gate07_required_field_items(), {"schema": "gate19.information_rights.v1"})
    assert result["item_count"] == 45
    assert result["families"]["added_required_field"]["unreachable_pairs"] == 15
    assert result["families"]["tool_replacement"]["unreachable_pairs"] == 5


# --- Version 3 repair tests -------------------------------------------------
# Added for manuscript version 3, in response to three review findings: that
# the rights object does not drive classification, that the auditor evaluates
# a reachability rule the frozen rights file does not declare, and that the
# external sample's 20/20 is partly hand-supplied.


def test_rights_instantiation_controls_the_visible_surface() -> None:
    """A rights change is a change to the materialized surface, and it bites.

    classify_item does not parse the rights object; the builders instantiate
    the declared rights into each item's visible surface. This test states
    that relationship as an executable claim: withdraw a source value from
    the granted surface and a reachable target becomes unreachable.
    """

    granted = _item(fields=["target"], target="CRS", sources=["CRS-026"], visible="CRS-026")
    assert audit_items([granted], RIGHTS)["items"][0]["status"] == REACHABLE

    withdrawn = dict(granted, visible_source_values=[], source_values=[], visible_text=[""])
    assert audit_items([withdrawn], RIGHTS)["items"][0]["status"] == CONVENTION_UNOBSERVABLE


def test_headline_is_invariant_under_rule_ablation() -> None:
    """50/310 does not depend on the undeclared visible_literal rule."""

    from research.gate19.ablation import VARIANTS, _summarize, verify_default_matches_auditor

    items = build_gate07_items()
    verify_default_matches_auditor(items, {"schema": "gate19.information_rights.v1"})

    expected = {REACHABLE: 260, TARGET_ABSENT: 10, CONVENTION_UNOBSERVABLE: 40}
    for name, config in VARIANTS.items():
        counts = _summarize(items, **config)["status_counts"]
        assert counts == expected, f"variant {name} moved the headline: {counts}"


def test_visible_literal_and_visible_split_are_coextensive_here() -> None:
    """The undeclared rule accepts exactly the items the declared rule accepts."""

    from research.gate19.ablation import _summarize

    items = build_gate07_items()
    baseline = _summarize(items)["rule_fire_counts"]
    ablated = _summarize(items, use_visible_literal=False)["rule_fire_counts"]

    assert baseline["visible_literal"] == 35
    assert baseline.get("visible_split", 0) == 0
    assert ablated.get("visible_literal", 0) == 0
    assert ablated["visible_split"] == 35


def test_external_sample_is_mostly_hand_adjudicated() -> None:
    """Withholding the hand annotation leaves 5 of 20 external pairs reachable."""

    import json
    from pathlib import Path

    from research.gate19.ablation import _summarize
    from research.gate19.external_audit import build_audit_input

    repo_root = Path(__file__).resolve().parents[2]
    register = json.loads(
        (repo_root / "gates/baselines/GATE_19_EXTERNAL_MCP_PAIRS.json").read_text(encoding="utf-8")
    )
    items = build_audit_input(register)

    with_annotation = _summarize(items, allow_declared_external=True)
    without = _summarize(items, allow_declared_external=False)

    assert with_annotation["status_counts"][REACHABLE] == 20
    assert with_annotation["rule_fire_counts"]["declared_external_derivation"] == 15
    assert with_annotation["rule_fire_counts"]["visible_literal"] == 5
    assert without["status_counts"][REACHABLE] == 5
    assert without["status_counts"][CONVENTION_UNOBSERVABLE] == 15
