"""Versioned, leakage-resistant prompt templates for Gate 07 baselines."""

from __future__ import annotations


LEGACY_PROMPT_VERSION = "gate07-llm-v1"
PROMPT_VERSION = "gate07-llm-v4"

# This text is retained verbatim as the v3 comparison arm. Its abstention
# semantics are intentionally not repaired; the arm exists to measure the
# change introduced by the V4 contract.
LEGACY_COMMON = """You are evaluating a synthetic API migration task. Use only the information explicitly included below. Do not assume hidden identifiers or a migration guide. You may abstain when no candidate is behaviorally equivalent. Return JSON only with this shape: {{\"selected_tool_names\": [string], \"argument_mapping\": [{{\"old_tool\": string, \"old_arg\": string, \"new_tool\": string, \"new_arg\": string}}], \"abstain\": boolean}}. The selected list may contain more than one tool only when the task requires a composed correspondence. Do not include analysis or markdown.\n\nTASK:\n{task_description}\n\nCANDIDATE TOOL CONTRACTS:\n{candidate_contracts}\n"""

# V4 decouples uncertainty from selection. In particular, a model may mark
# uncertainty while still naming the best candidate required for scoring.
V4_COMMON = """You are evaluating a synthetic API migration task. Use only the contracts, task description, candidate contracts, and any verified old traces supplied below. Candidate order is randomized; never use position as evidence. A candidate may require deriving a new argument value from a value already held in an old input. Such derivation is permitted when supported by the supplied task or contracts and must be declared with value_transform in the mapping or with a literal constructed_argument_values entry. Do not invent hidden identifiers, external migration guides, or unsupported values. For every answerable task, always select one or more best candidates even when uncertain; use abstain only as a separate uncertainty flag and never leave the selection empty to express doubt. Record doubt in equivalence_verdict. If no candidate is behaviorally equivalent, use an empty selection and empty mapping, set equivalence_verdict to not_equivalent, and set abstain to false. Use confidence between 0 and 1. Return JSON only with this shape: {{\"best_candidate_tool_names\": [string], \"argument_mapping\": [{{\"old_tool\": string, \"old_arg\": string, \"new_tool\": string, \"new_arg\": string, \"value_transform\": object}}], \"equivalence_verdict\": \"equivalent | equivalent_under_stated_convention | not_equivalent\", \"confidence\": number, \"abstain\": boolean, \"constructed_argument_values\": [{{\"new_tool\": string, \"arguments\": object}}]}}. For identity use value_transform {{\"kind\": \"identity\"}}. For a split use {{\"kind\": \"split\", \"delimiter\": string, \"part\": \"prefix | suffix\"}}. For a merge use {{\"kind\": \"join\", \"delimiter\": string, \"order\": integer}}. Do not include analysis or markdown.\n\nTASK:\n{task_description}\n\nCANDIDATE TOOL CONTRACTS (in randomized order):\n{candidate_contracts}\n"""

COMMON = LEGACY_COMMON


PROMPT_TEMPLATES = {
    "llm_new_schema_only": {
        "prompt_id": "gate07-llm-new-only-v4",
        "version": PROMPT_VERSION,
        "selection_contract": "v4_forced",
        "information_rights": ["new_contracts", "task_description", "candidate_list"],
        "text": V4_COMMON,
    },
    "llm_old_new_direct": {
        "prompt_id": "gate07-llm-direct-v4-forced",
        "version": PROMPT_VERSION,
        "selection_contract": "v4_forced",
        "information_rights": ["old_contract", "new_contracts", "task_description", "candidate_list"],
        "text": V4_COMMON + "\nOLD TOOL CONTRACTS:\n{old_contracts}\n",
    },
    "llm_old_new_history": {
        "prompt_id": "gate07-llm-history-v4",
        "version": PROMPT_VERSION,
        "selection_contract": "v4_forced",
        "information_rights": ["old_contract", "new_contracts", "verified_old_traces", "task_description", "candidate_list"],
        "text": V4_COMMON + "\nOLD TOOL CONTRACTS:\n{old_contracts}\n\nVERIFIED OLD TRACES:\n{verified_old_traces}\n",
    },
    "llm_reasoning": {
        "prompt_id": "gate07-llm-reasoning-v4",
        "version": PROMPT_VERSION,
        "selection_contract": "v4_forced",
        "information_rights": ["old_contract", "new_contracts", "task_description", "candidate_list"],
        "text": V4_COMMON + "\nOLD TOOL CONTRACTS:\n{old_contracts}\n\nBefore emitting the JSON, privately compare identity, inputs, outputs, preconditions, and effects. Do not expose that reasoning in the response.\n",
    },
}


LEGACY_PROMPT_TEMPLATES = {
    "llm_old_new_direct_v3_legacy": {
        "prompt_id": "gate07-llm-direct-v1-legacy",
        "version": LEGACY_PROMPT_VERSION,
        "selection_contract": "v3_legacy",
        "information_rights": ["old_contract", "new_contracts", "task_description", "candidate_list"],
        "text": LEGACY_COMMON + "\nOLD TOOL CONTRACTS:\n{old_contracts}\n",
    },
}


ALL_PROMPT_TEMPLATES = {**PROMPT_TEMPLATES, **LEGACY_PROMPT_TEMPLATES}
