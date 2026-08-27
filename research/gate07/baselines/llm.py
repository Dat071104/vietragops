"""Prompt rendering and response parsing for research-mode LLM baselines."""

from __future__ import annotations

import json
from typing import Any

from research.gate07.protocol.prompts import PROMPT_TEMPLATES


def render_llm_prompt(arm_id: str, task: dict[str, Any]) -> tuple[str, str]:
    template = PROMPT_TEMPLATES[arm_id]
    encode = lambda value: json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)
    prompt = template["text"].format(
        task_description=task.get("task_description", ""),
        candidate_contracts=encode(task.get("new_contracts", [])),
        old_contracts=encode(task.get("old_contracts", [])),
        verified_old_traces=encode(task.get("verified_old_traces", [])),
    )
    return template["prompt_id"], prompt


def parse_llm_payload(payload: Any, task: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("response is not a JSON object")
    candidates = set(task.get("candidate_new_tool_names", []))
    selected = payload.get("selected_tool_names")
    abstain = payload.get("abstain")
    if not isinstance(selected, list) or not isinstance(abstain, bool):
        raise ValueError("response must contain selected_tool_names list and abstain boolean")
    if abstain and selected:
        raise ValueError("abstention cannot contain selected tools")
    if any(not isinstance(name, str) or name not in candidates for name in selected):
        raise ValueError("selected tool is not in the public candidate list")
    if not abstain and not selected:
        raise ValueError("non-abstaining response selected no tool")
    pairs = payload.get("argument_mapping", [])
    if not isinstance(pairs, list):
        raise ValueError("argument_mapping must be a list")
    normalized_pairs = []
    for pair in pairs:
        if not isinstance(pair, dict) or any(not isinstance(pair.get(key), str) for key in ("old_tool", "old_arg", "new_tool", "new_arg")):
            raise ValueError("argument mapping entry is malformed")
        if pair["new_tool"] not in candidates:
            raise ValueError("argument mapping references a non-candidate tool")
        normalized_pairs.append([pair["old_tool"], pair["old_arg"], pair["new_tool"], pair["new_arg"]])
    ranked = list(selected) + [name for name in task.get("candidate_new_tool_names", []) if name not in selected]
    return {"selected_tool_names": selected, "ranked_tool_names": ranked, "argument_pairs": normalized_pairs, "abstain": abstain}
