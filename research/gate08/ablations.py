"""The Gate 08 method arm and the six required ablations.

Every arm names the information it is allowed to use. `project_task` from Gate 07
enforces the same rights vocabulary, so an arm cannot quietly read a field it did
not declare.
"""

from __future__ import annotations

from research.gate08.method.pipeline import MethodConfig


METHOD_ARM = MethodConfig(arm_id="gate08_method")

ABLATIONS = (
    MethodConfig(arm_id="ablate_no_history", old_variant="no_history"),
    MethodConfig(arm_id="ablate_schema_only", old_variant="task_only"),
    MethodConfig(arm_id="ablate_no_intent_abstraction", use_intent_abstraction=False),
    MethodConfig(arm_id="ablate_no_preconditions_effects", include_preconditions_effects=False),
    MethodConfig(arm_id="ablate_no_calibration", calibration_enabled=False),
)

ALL_CONFIGS = (METHOD_ARM,) + ABLATIONS

# The sixth required ablation. It is not re-collected: the frozen Gate 07 V4.1
# `llm_old_new_history` rows are a single-shot frontier-LLM mapper with strictly
# greater information rights than this method (it sees the old contract, the
# traces, and every candidate at once). Re-running it would spend budget to
# reproduce evidence that is already frozen.
REUSED_ABLATION = {
    "ablation_id": "ablate_direct_frontier_llm_mapper",
    "source": "gates/artifacts/gate07/v4/llm/llm_results.jsonl",
    "source_arm_id": "llm_old_new_history",
    "collected_by": "gate07_v4_1",
    "re_collected": False,
}

INFORMATION_RIGHTS = {
    "gate08_method": ["old_contract", "verified_old_traces", "task_description", "new_contracts", "candidate_list"],
    "ablate_no_history": ["old_contract", "task_description", "new_contracts", "candidate_list"],
    "ablate_schema_only": ["task_description", "new_contracts", "candidate_list"],
    "ablate_no_intent_abstraction": ["old_contract", "verified_old_traces", "task_description", "new_contracts", "candidate_list"],
    "ablate_no_preconditions_effects": ["old_contract", "verified_old_traces", "task_description", "new_contracts", "candidate_list"],
    "ablate_no_calibration": ["old_contract", "verified_old_traces", "task_description", "new_contracts", "candidate_list"],
    "ablate_direct_frontier_llm_mapper": ["old_contract", "verified_old_traces", "task_description", "new_contracts", "candidate_list"],
}


def config_by_id(arm_id: str) -> MethodConfig:
    for config in ALL_CONFIGS:
        if config.arm_id == arm_id:
            return config
    raise KeyError(f"Unknown Gate 08 arm: {arm_id!r}")


__all__ = [
    "ABLATIONS",
    "ALL_CONFIGS",
    "INFORMATION_RIGHTS",
    "METHOD_ARM",
    "REUSED_ABLATION",
    "config_by_id",
]
