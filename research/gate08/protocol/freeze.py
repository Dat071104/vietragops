"""Gate 08 protocol freeze and pre-run verification.

The freeze proves three things before a headline run: the protocol is committed,
the Gate 07 dataset it evaluates on is byte-identical to the one Gate 07 froze,
and the method interface has not changed since the protocol was written.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research.gate07.protocol.freeze import (
    FreezePreflightError,
    _git,
    _git_output,
    _live_cases,
    _resolve_protocol_path,
    canonical_digest,
    candidate_order_digest,
    dataset_manifest_digests,
)
from research.gate08.ablations import ALL_CONFIGS, INFORMATION_RIGHTS, REUSED_ABLATION
from research.gate08.harness import CLAIM_FAMILIES, CONTROL_FAMILIES, calibration_cases, eval_cases
from research.gate08.method.alignment import TRANSFORM_KINDS
from research.gate08.method.calibration import (
    ABSTAIN_COVERAGE_TARGET,
    CONFIDENCE_WEIGHTS,
    RETRIEVAL_FLOOR_GRID,
)
from research.gate08.method.correspondence import DIMENSION_WEIGHTS
from research.gate08.method.models import INTERFACE_VERSION, method_interface_digest
from research.gate08.method.prompts import ALL_PROMPTS, PROMPT_VERSION


SCHEMA = "gate08.protocol.v1"

# The Gate 07 V4.1 surface. Any other value would evaluate the method on a
# different candidate list than the frozen baselines saw.
CANDIDATE_ORDER = "v4_seeded_permutation"

# Same practical/saturation bars Gate 07 V4 used, so a Gate 08 number can be
# read against a Gate 07 number without re-deriving a threshold.
METRIC_THRESHOLDS = {
    "tool_alignment_at_1": {"practical": 0.80, "saturation": 0.95},
    "argument_mapping_f1": {"practical": 0.75, "saturation": 0.90},
    "no_equivalent_accuracy": {"practical": 0.80, "saturation": 0.90},
    "first_attempt_task_success": {"practical": 0.80, "saturation": 0.90},
}

FAMILY_MINIMUM = 15


def surface_digest() -> dict[str, str]:
    return {
        "eval_case_ids_sha256": canonical_digest(sorted(case.case_id for case in eval_cases())),
        "calibration_case_ids_sha256": canonical_digest(sorted(case.case_id for case in calibration_cases())),
    }


def _prompt_records() -> list[dict[str, Any]]:
    return [
        {
            "prompt_id": prompt["prompt_id"],
            "version": prompt["version"],
            "side": prompt["side"],
            "information_rights": list(prompt["information_rights"]),
            "text_sha256": canonical_digest(prompt["text"]),
        }
        for prompt in sorted(ALL_PROMPTS.values(), key=lambda value: value["prompt_id"])
    ]


def build_protocol(
    *,
    model_ids: tuple[str, ...],
    cost_cap_usd: float,
    repo_root: str | Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[3]
    head = _git_output(root, "rev-parse", "HEAD")
    cases = _live_cases(CANDIDATE_ORDER)
    return {
        "schema": SCHEMA,
        "gate": "gate08",
        "created_at": created_at,
        "git_head_at_freeze": head,
        "authorized_by": "gates/results/GATE_07_RESULT.md narrow V4.1 GO",
        "dataset": {
            **dataset_manifest_digests(cases),
            "candidate_order": CANDIDATE_ORDER,
            "candidate_order_oracle_sha256": candidate_order_digest(cases),
            "source": "research/gate07/dataset/generator.py build_v4_cases (unchanged)",
        },
        "evaluation_surface": {
            "claim_families": list(CLAIM_FAMILIES),
            "control_families": list(CONTROL_FAMILIES),
            "eval_case_count": len(eval_cases()),
            "calibration_case_count": len(calibration_cases()),
            "calibration_split": "held_out",
            "family_minimum": FAMILY_MINIMUM,
            **surface_digest(),
        },
        "method": {
            "interface_version": INTERFACE_VERSION,
            "interface_digest": method_interface_digest(),
            "prompt_version": PROMPT_VERSION,
            "prompts": _prompt_records(),
            "correspondence_weights": dict(DIMENSION_WEIGHTS),
            "confidence_weights": dict(CONFIDENCE_WEIGHTS),
            "retrieval_floor_grid": list(RETRIEVAL_FLOOR_GRID),
            "abstain_coverage_target": ABSTAIN_COVERAGE_TARGET,
            "transform_kinds": list(TRANSFORM_KINDS),
            "unresolved_join_policy": (
                "A merge whose separator is stated nowhere in the method-facing information is "
                "emitted as join_unresolved: the correspondence is reported and scored, and no "
                "value is constructed. Gate 07's executor therefore reports an unconstructible "
                "call rather than a value built from an invented separator."
            ),
        },
        "arms": [
            {
                "arm_id": config.arm_id,
                "config": config.to_record(),
                "information_rights": list(INFORMATION_RIGHTS[config.arm_id]),
                "models": list(model_ids),
            }
            for config in ALL_CONFIGS
        ],
        "reused_ablation": dict(REUSED_ABLATION)
        | {"information_rights": list(INFORMATION_RIGHTS["ablate_direct_frontier_llm_mapper"])},
        "metrics": {
            "definitions": {
                "tool_alignment_at_1": "Exact match between the selected candidate set and the correct new tool set.",
                "argument_mapping_f1": "F1 over (old_tool, old_arg, new_tool, new_arg) quadruples.",
                "false_alignment_rate": "Share of proposed old/new tool pairs that are not correct.",
                "no_equivalent_accuracy": "Share of no-equivalent cases answered not_equivalent.",
                "abstention_rate": "Share of cases whose decision carried the abstention flag.",
                "first_attempt_task_success": "One adapted execution per case, scored by the frozen Gate 07 executor.",
            },
            "thresholds": METRIC_THRESHOLDS,
            "interval_methods": {"proportion": "wilson", "continuous": "bootstrap"},
            "bootstrap_samples": 2000,
        },
        "provider": {
            "models": list(model_ids),
            "mode": "research",
            "fallback": "disabled",
            "cost_cap_usd": cost_cap_usd,
            "max_tokens": 900,
        },
        "exclusions": {
            "provider_failure": "Never enters an accuracy numerator or denominator.",
            "parse_failure": "Never enters an accuracy numerator or denominator.",
            "signature_unavailable": "A case whose signature could not be collected is reported, not scored.",
        },
    }


def write_protocol(protocol: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(protocol, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def preflight_gate08_run(protocol_path: str | Path, *, repo_root: str | Path | None = None) -> dict[str, Any]:
    root, path = _resolve_protocol_path(protocol_path, repo_root)
    if not path.is_file():
        raise FreezePreflightError(f"Protocol file does not exist: {path}")
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise FreezePreflightError(f"Protocol is outside repository root: {path}") from exc

    if _git(root, "ls-files", "--error-unmatch", "--", relative).returncode != 0:
        raise FreezePreflightError(f"Protocol is not tracked in git: {relative}")
    status = _git(root, "status", "--porcelain", "--", relative)
    if status.returncode != 0:
        raise FreezePreflightError(f"Could not inspect protocol status: {status.stderr.strip()}")
    if status.stdout.strip():
        raise FreezePreflightError(f"Protocol is dirty or uncommitted: {status.stdout.strip()}")

    protocol = json.loads(path.read_text(encoding="utf-8"))
    recorded = protocol.get("git_head_at_freeze")
    if not isinstance(recorded, str) or not recorded.strip():
        raise FreezePreflightError("Protocol has no recorded git_head_at_freeze.")
    resolved = _git_output(root, "rev-parse", "--verify", f"{recorded}^{{commit}}")
    current = _git_output(root, "rev-parse", "HEAD")
    if _git(root, "merge-base", "--is-ancestor", resolved, current).returncode != 0:
        raise FreezePreflightError(f"Frozen revision {recorded} is not an ancestor of current HEAD {current}.")

    cases = _live_cases(CANDIDATE_ORDER)
    live_dataset = dataset_manifest_digests(cases)
    expected_dataset = protocol.get("dataset") or {}
    mismatches = {
        key: {"expected": expected_dataset.get(key), "live": value}
        for key, value in live_dataset.items()
        if expected_dataset.get(key) != value
    }
    if mismatches:
        raise FreezePreflightError(f"Live Gate 07 dataset digest mismatch: {mismatches}")
    live_oracle = candidate_order_digest(cases)
    if expected_dataset.get("candidate_order_oracle_sha256") != live_oracle:
        raise FreezePreflightError("Candidate-order oracle digest mismatch.")

    live_interface = method_interface_digest()
    if (protocol.get("method") or {}).get("interface_digest") != live_interface:
        raise FreezePreflightError("Method interface digest changed since the freeze.")

    live_surface = surface_digest()
    expected_surface = protocol.get("evaluation_surface") or {}
    surface_mismatch = {
        key: {"expected": expected_surface.get(key), "live": value}
        for key, value in live_surface.items()
        if expected_surface.get(key) != value
    }
    if surface_mismatch:
        raise FreezePreflightError(f"Evaluation surface digest mismatch: {surface_mismatch}")

    return {
        "status": "passed",
        "protocol_path": relative,
        "protocol_git_head_at_freeze": recorded,
        "protocol_git_head_resolved": resolved,
        "current_head": current,
        "dataset_digests": live_dataset,
        "candidate_order_oracle_sha256": live_oracle,
        "method_interface_digest": live_interface,
        "evaluation_surface": live_surface,
    }


__all__ = [
    "CANDIDATE_ORDER",
    "FAMILY_MINIMUM",
    "METRIC_THRESHOLDS",
    "SCHEMA",
    "build_protocol",
    "preflight_gate08_run",
    "surface_digest",
    "write_protocol",
]
