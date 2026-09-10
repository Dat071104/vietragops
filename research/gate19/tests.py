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
