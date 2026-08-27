"""Versioned, leakage-resistant prompt templates for direct LLM baselines."""

from __future__ import annotations


PROMPT_VERSION = "gate07-llm-v1"

COMMON = """You are evaluating a synthetic API migration task. Use only the information explicitly included below. Do not assume hidden identifiers or a migration guide. You may abstain when no candidate is behaviorally equivalent. Return JSON only with this shape: {{\"selected_tool_names\": [string], \"argument_mapping\": [{{\"old_tool\": string, \"old_arg\": string, \"new_tool\": string, \"new_arg\": string}}], \"abstain\": boolean}}. The selected list may contain more than one tool only when the task requires a composed correspondence. Do not include analysis or markdown.\n\nTASK:\n{task_description}\n\nCANDIDATE TOOL CONTRACTS:\n{candidate_contracts}\n"""


PROMPT_TEMPLATES = {
    "llm_new_schema_only": {
        "prompt_id": "gate07-llm-new-only-v1",
        "version": PROMPT_VERSION,
        "information_rights": ["new_contracts", "task_description", "candidate_list"],
        "text": COMMON,
    },
    "llm_old_new_direct": {
        "prompt_id": "gate07-llm-direct-v1",
        "version": PROMPT_VERSION,
        "information_rights": ["old_contract", "new_contracts", "task_description", "candidate_list"],
        "text": COMMON + "\nOLD TOOL CONTRACTS:\n{old_contracts}\n",
    },
    "llm_old_new_history": {
        "prompt_id": "gate07-llm-history-v1",
        "version": PROMPT_VERSION,
        "information_rights": ["old_contract", "new_contracts", "verified_old_traces", "task_description", "candidate_list"],
        "text": COMMON + "\nOLD TOOL CONTRACTS:\n{old_contracts}\n\nVERIFIED OLD TRACES:\n{verified_old_traces}\n",
    },
    "llm_reasoning": {
        "prompt_id": "gate07-llm-reasoning-v1",
        "version": PROMPT_VERSION,
        "information_rights": ["old_contract", "new_contracts", "task_description", "candidate_list"],
        "text": COMMON + "\nOLD TOOL CONTRACTS:\n{old_contracts}\n\nBefore emitting the JSON, privately compare identity, inputs, outputs, preconditions, and effects. Do not expose that reasoning in the response.\n",
    },
}
