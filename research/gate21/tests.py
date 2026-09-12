"""Offline unit tests for the Gate 21 external-register adapter."""

from __future__ import annotations

import pytest

from research.gate21.mcpevol_adapter import (
    AdapterRefusal,
    EvolutionRecord,
    adapt_record,
)


def _evolution(record: dict, *, task_idx: int = 7) -> EvolutionRecord:
    return EvolutionRecord(
        stage=1,
        source_path="external/HYBRID/evolution.json",
        server="demo-server",
        tool="demo_tool",
        mutation_type="PARAM",
        task_idx=task_idx,
        record=record,
    )


def _case(arguments: dict) -> dict:
    return {
        "idx": 7,
        "case_id": "mcpevol-case-7",
        "question": "Use the demo tool.",
        "tool_calls": [{"tool_name": "demo_tool", "arguments": arguments}],
        "new_contract_fields": {"demo_tool": list(arguments)},
        "visible_text": ["Use the demo tool."],
    }


def test_added_required_parameter_is_translated_without_classification() -> None:
    items = adapt_record(
        _evolution(
            {
                "parameter_additions": [
                    {"name": "approval", "type": "string", "required": True, "description": "Approval code"}
                ]
            }
        ),
        task_cases={7: _case({"approval": "A-1"})},
    )
    assert len(items) == 1
    assert items[0]["new_arg"] == "approval"
    assert items[0]["target_value"] == "A-1"
    assert items[0]["new_contract_fields"] == {"demo_tool": ["approval"]}


def test_added_optional_parameter_is_translated_without_classification() -> None:
    items = adapt_record(
        _evolution(
            {
                "parameter_additions": [
                    {"name": "limit", "type": "integer", "required": False, "description": "Result limit"}
                ]
            }
        ),
        task_cases={7: _case({"limit": 3})},
    )
    assert len(items) == 1
    assert items[0]["new_arg"] == "limit"
    assert items[0]["target_value"] == 3


def test_explicit_rename_is_translated_when_expected_call_has_new_name() -> None:
    items = adapt_record(
        _evolution(
            {
                "parameter_changes": [
                    {
                        "action": "rename",
                        "old_name": "query",
                        "new_name": "search_query",
                        "required": True,
                    }
                ]
            }
        ),
        task_cases={7: _case({"search_query": "history"})},
    )
    assert len(items) == 1
    assert items[0]["old_arg"] == "query"
    assert items[0]["new_arg"] == "search_query"


def test_desc_record_is_refused_as_outside_argument_target_schema() -> None:
    evolution = EvolutionRecord(
        stage=1,
        source_path="external/HYBRID/evolution.json",
        server="demo-server",
        tool="demo_tool",
        mutation_type="DESC",
        task_idx=7,
        record={"tool": {"original_description": "old", "modified_description": "new"}},
    )
    with pytest.raises(AdapterRefusal, match="not argument-target"):
        adapt_record(evolution, task_cases={7: _case({})})


def test_param_record_without_declared_task_join_is_refused() -> None:
    with pytest.raises(AdapterRefusal, match="task_idx-to-test_cases"):
        adapt_record(
            _evolution(
                {
                    "parameter_additions": [
                        {"name": "approval", "type": "string", "required": True, "description": "Approval code"}
                    ]
                }
            ),
            task_cases=None,
        )
