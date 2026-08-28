"""Prompt rendering and response parsing for Gate 07 LLM baselines."""

from __future__ import annotations

import json
import math
from numbers import Real
from typing import Any

from research.gate07.protocol.prompts import ALL_PROMPT_TEMPLATES


_EQUIVALENCE_VERDICTS = frozenset(
    {"equivalent", "equivalent_under_stated_convention", "not_equivalent"}
)
_TRANSFORM_KINDS = frozenset({"identity", "split", "join", "literal"})


def render_llm_prompt(arm_id: str, task: dict[str, Any]) -> tuple[str, str]:
    template = ALL_PROMPT_TEMPLATES[arm_id]
    encode = lambda value: json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)
    prompt = template["text"].format(
        task_description=task.get("task_description", ""),
        candidate_contracts=encode(task.get("new_contracts", [])),
        old_contracts=encode(task.get("old_contracts", [])),
        verified_old_traces=encode(task.get("verified_old_traces", [])),
    )
    return template["prompt_id"], prompt


def _candidate_names(task: dict[str, Any]) -> set[str]:
    candidates = task.get("candidate_new_tool_names", [])
    if not isinstance(candidates, list) or any(not isinstance(name, str) for name in candidates):
        raise ValueError("candidate_new_tool_names must be a list of strings")
    if len(set(candidates)) != len(candidates):
        raise ValueError("candidate_new_tool_names must not contain duplicates")
    return set(candidates)


def _normalize_transform(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("value_transform must be an object")
    kind = value.get("kind")
    if kind not in _TRANSFORM_KINDS:
        raise ValueError("value_transform kind is unsupported")
    if kind == "identity":
        return {"kind": "identity"}
    if kind == "literal":
        if "value" not in value:
            raise ValueError("literal value_transform requires value")
        return {"kind": "literal", "value": value["value"]}
    delimiter = value.get("delimiter")
    if not isinstance(delimiter, str) or not delimiter:
        raise ValueError(f"{kind} value_transform requires a non-empty delimiter")
    if kind == "split":
        part = value.get("part")
        if part not in {"prefix", "suffix"}:
            raise ValueError("split value_transform part must be prefix or suffix")
        return {"kind": "split", "delimiter": delimiter, "part": part}
    order = value.get("order")
    if not isinstance(order, int) or isinstance(order, bool) or order < 0:
        raise ValueError("join value_transform order must be a non-negative integer")
    return {"kind": "join", "delimiter": delimiter, "order": order}


def _normalize_argument_mapping(value: Any, candidates: set[str]) -> tuple[list[dict[str, Any]], list[list[str]]]:
    if not isinstance(value, list):
        raise ValueError("argument_mapping must be a list")
    normalized: list[dict[str, Any]] = []
    pairs: list[list[str]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("argument mapping entry is malformed")
        required = ("old_tool", "old_arg", "new_tool", "new_arg", "value_transform")
        if any(not isinstance(item.get(key), str) or not item[key] for key in required[:4]):
            raise ValueError("argument mapping names must be non-empty strings")
        if item["new_tool"] not in candidates:
            raise ValueError("argument mapping references a non-candidate tool")
        transform = _normalize_transform(item.get("value_transform"))
        entry = {
            "old_tool": item["old_tool"],
            "old_arg": item["old_arg"],
            "new_tool": item["new_tool"],
            "new_arg": item["new_arg"],
            "value_transform": transform,
        }
        normalized.append(entry)
        pairs.append([item["old_tool"], item["old_arg"], item["new_tool"], item["new_arg"]])
    return normalized, pairs


def _normalize_constructed_values(value: Any, candidates: set[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("constructed_argument_values must be a list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get("new_tool"), str) or not isinstance(item.get("arguments"), dict):
            raise ValueError("constructed argument value entry is malformed")
        tool_name = item["new_tool"]
        if tool_name not in candidates:
            raise ValueError("constructed argument values reference a non-candidate tool")
        if tool_name in seen:
            raise ValueError("constructed argument values must have one entry per tool")
        seen.add(tool_name)
        normalized.append({"new_tool": tool_name, "arguments": dict(item["arguments"])})
    return normalized


def parse_v4_llm_payload(payload: Any, task: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("response is not a JSON object")
    candidates = _candidate_names(task)
    selected = payload.get("best_candidate_tool_names")
    if not isinstance(selected, list) or any(not isinstance(name, str) or name not in candidates for name in selected):
        raise ValueError("best_candidate_tool_names must contain only public candidates")
    if len(set(selected)) != len(selected):
        raise ValueError("best_candidate_tool_names must not contain duplicates")
    verdict = payload.get("equivalence_verdict")
    if verdict not in _EQUIVALENCE_VERDICTS:
        raise ValueError("equivalence_verdict is invalid")
    if verdict == "not_equivalent":
        if selected:
            raise ValueError("not_equivalent must not select a candidate")
    elif not selected:
        raise ValueError("answerable V4 response must select at least one candidate")
    abstain = payload.get("abstain")
    if not isinstance(abstain, bool):
        raise ValueError("abstain must be boolean")
    if verdict == "not_equivalent" and abstain:
        raise ValueError("not_equivalent is a verdict, not an abstention")
    confidence = payload.get("confidence")
    if not isinstance(confidence, Real) or isinstance(confidence, bool) or not math.isfinite(float(confidence)) or not 0.0 <= float(confidence) <= 1.0:
        raise ValueError("confidence must be a finite number between 0 and 1")
    mapping, pairs = _normalize_argument_mapping(payload.get("argument_mapping"), candidates)
    if any(entry["new_tool"] not in selected for entry in mapping):
        raise ValueError("argument mapping must reference a selected candidate")
    constructed = _normalize_constructed_values(payload.get("constructed_argument_values"), candidates)
    if verdict == "not_equivalent" and constructed:
        raise ValueError("not_equivalent must not construct arguments")
    return {
        "best_candidate_tool_names": list(selected),
        "selected_tool_names": list(selected),
        "argument_mapping": mapping,
        "argument_pairs": pairs,
        "value_transforms": [entry["value_transform"] for entry in mapping],
        "constructed_argument_values": constructed,
        "equivalence_verdict": verdict,
        "confidence": float(confidence),
        "abstain": abstain,
        "selection_contract": "v4_forced",
    }


def parse_legacy_llm_payload(payload: Any, task: dict[str, Any]) -> dict[str, Any]:
    """Parse the retained v3 contract without changing its abstention semantics."""
    if not isinstance(payload, dict):
        raise ValueError("response is not a JSON object")
    candidates = _candidate_names(task)
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
    raw_pairs = payload.get("argument_mapping", [])
    if not isinstance(raw_pairs, list):
        raise ValueError("argument_mapping must be a list")
    normalized_pairs: list[list[str]] = []
    for pair in raw_pairs:
        if not isinstance(pair, dict) or any(not isinstance(pair.get(key), str) for key in ("old_tool", "old_arg", "new_tool", "new_arg")):
            raise ValueError("argument mapping entry is malformed")
        if pair["new_tool"] not in candidates:
            raise ValueError("argument mapping references a non-candidate tool")
        normalized_pairs.append([pair["old_tool"], pair["old_arg"], pair["new_tool"], pair["new_arg"]])
    ranked = list(selected) + [name for name in task.get("candidate_new_tool_names", []) if name not in selected]
    return {
        "selected_tool_names": selected,
        "best_candidate_tool_names": list(selected),
        "ranked_tool_names": ranked,
        "argument_pairs": normalized_pairs,
        "argument_mapping": [
            {
                "old_tool": pair[0],
                "old_arg": pair[1],
                "new_tool": pair[2],
                "new_arg": pair[3],
            }
            for pair in normalized_pairs
        ],
        "constructed_argument_values": [],
        "equivalence_verdict": "not_equivalent" if abstain else "equivalent",
        "confidence": 0.0,
        "abstain": abstain,
        "selection_contract": "v3_legacy",
    }


def parse_llm_payload(payload: Any, task: dict[str, Any]) -> dict[str, Any]:
    """Parse the V4 forced-selection response contract."""
    return parse_v4_llm_payload(payload, task)
