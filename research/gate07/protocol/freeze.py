"""Create the immutable machine-readable Gate 07 protocol record."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Iterable

from research.gate0.evaluator.capability import EvaluatorCapability
from research.gate07.dataset.models import FAMILY_NAMES, Gate07Case
from research.gate07.oracle.ground_truth import ground_truth_digest
from research.gate07.protocol.prompts import PROMPT_TEMPLATES
from research.gate07.harness.method_facing import build_method_facing_task


class FreezePreflightError(RuntimeError):
    """Raised when a headline run does not have a valid committed freeze."""


def canonical_digest(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _manifest_records(cases: Iterable[Gate07Case], held_out: bool) -> list[dict[str, Any]]:
    return [case.manifest_record() for case in cases if case.held_out is held_out]


def dataset_manifest_digests(cases: Iterable[Gate07Case]) -> dict[str, str]:
    materialized = tuple(cases)
    return {
        "graded_manifest_sha256": canonical_digest(_manifest_records(materialized, False)),
        "held_out_manifest_sha256": canonical_digest(_manifest_records(materialized, True)),
    }


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _git_output(repo_root: Path, *args: str) -> str:
    result = _git(repo_root, *args)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise FreezePreflightError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def _resolve_protocol_path(protocol_path: str | Path, repo_root: str | Path | None) -> tuple[Path, Path]:
    default_root = Path(__file__).resolve().parents[3]
    root = Path(repo_root).resolve() if repo_root is not None else default_root
    candidate = Path(protocol_path)
    path = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    return root, path


def preflight_headline_run(protocol_path: str | Path, *, repo_root: str | Path | None = None) -> dict[str, Any]:
    """Verify the committed protocol and live dataset before a headline run."""
    root, path = _resolve_protocol_path(protocol_path, repo_root)
    if not path.is_file():
        raise FreezePreflightError(f"Protocol file does not exist: {path}")
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise FreezePreflightError(f"Protocol is outside repository root: {path}") from exc

    tracked = _git(root, "ls-files", "--error-unmatch", "--", relative)
    if tracked.returncode != 0:
        raise FreezePreflightError(f"Protocol is not tracked in git: {relative}")
    status = _git(root, "status", "--porcelain", "--", relative)
    if status.returncode != 0:
        raise FreezePreflightError(f"Could not inspect protocol status: {status.stderr.strip()}")
    if status.stdout.strip():
        raise FreezePreflightError(f"Protocol is dirty or uncommitted: {status.stdout.strip()}")

    try:
        protocol = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FreezePreflightError(f"Protocol cannot be read as JSON: {path}") from exc
    recorded = protocol.get("git_head_at_freeze")
    if not isinstance(recorded, str) or not recorded.strip():
        raise FreezePreflightError("Protocol has no recorded git_head_at_freeze.")
    resolved = _git_output(root, "rev-parse", "--verify", f"{recorded}^{{commit}}")
    current = _git_output(root, "rev-parse", "HEAD")
    ancestor = _git(root, "merge-base", "--is-ancestor", resolved, current)
    if ancestor.returncode != 0:
        raise FreezePreflightError(f"Frozen revision {recorded} is not an ancestor of current HEAD {current}.")

    expected_dataset = protocol.get("dataset")
    if not isinstance(expected_dataset, dict):
        raise FreezePreflightError("Protocol has no dataset digest block.")
    live_dataset = dataset_manifest_digests(_live_cases())
    mismatches = {
        key: {"expected": expected_dataset.get(key), "live": value}
        for key, value in live_dataset.items()
        if expected_dataset.get(key) != value
    }
    if mismatches:
        raise FreezePreflightError(f"Live dataset digest mismatch: {mismatches}")
    return {
        "status": "passed",
        "protocol_path": relative,
        "protocol_git_head_at_freeze": recorded,
        "protocol_git_head_resolved": resolved,
        "current_head": current,
        "dataset_digests": live_dataset,
    }


def _live_cases() -> tuple[Gate07Case, ...]:
    from research.gate07.dataset.generator import build_all_cases

    return build_all_cases()


def _arms(model_ids: tuple[str, ...]) -> list[dict[str, Any]]:
    offline = [
        ("lexical_name", "Normalized lexical similarity over tool names only.", ["old_contract", "new_contracts", "task_description", "candidate_list"]),
        ("lexical_serialized", "Normalized lexical similarity over serialized contract text.", ["old_contract", "new_contracts", "task_description", "candidate_list"]),
        ("embed_name_desc", "Nearest tool under the pinned BGE-M3 name/description embedding.", ["old_contract", "new_contracts", "task_description", "candidate_list"]),
        ("embed_serialized_schema", "Nearest tool under the pinned BGE-M3 serialized-schema embedding.", ["old_contract", "new_contracts", "task_description", "candidate_list"]),
        ("cross_encoder", "Pairwise scoring under the pinned BGE reranker cross-encoder.", ["old_contract", "new_contracts", "task_description", "candidate_list"]),
    ]
    arms = [{"arm_id": arm_id, "description": description, "information_rights": rights, "models": ["deterministic_offline"], "headline": True} for arm_id, description, rights in offline]
    for arm_id, description, rights in (
        ("llm_new_schema_only", "Direct LLM mapping from new contracts only.", PROMPT_TEMPLATES["llm_new_schema_only"]["information_rights"]),
        ("llm_old_new_direct", "Direct LLM mapping from old and new contracts.", PROMPT_TEMPLATES["llm_old_new_direct"]["information_rights"]),
        ("llm_old_new_history", "Direct LLM mapping with verified old traces.", PROMPT_TEMPLATES["llm_old_new_history"]["information_rights"]),
        ("llm_reasoning", "Reasoning-style direct LLM mapping with direct-arm rights.", PROMPT_TEMPLATES["llm_reasoning"]["information_rights"]),
    ):
        arms.append({"arm_id": arm_id, "description": description, "information_rights": rights, "models": list(model_ids), "headline": True})
    return arms


def _metric_definitions() -> dict[str, str]:
    return {
        "tool_alignment_at_1": "mean over graded cases of 1 when every expected new tool is in the first predicted selected_tool_names set (or abstain is correct for NO_EQUIVALENT), else 0.",
        "tool_alignment_at_k": "mean over graded cases of 1 when every expected new tool is contained in the top-k ranked tool list; for one-to-many, all expected tools must be present.",
        "argument_mapping_precision": "|P intersect E| / |P|, with 1.0 when P and E are both empty; E and P are exact quadruple sets (old_tool, old_arg, new_tool, new_arg).",
        "argument_mapping_recall": "|P intersect E| / |E|, with 1.0 when E is empty.",
        "argument_mapping_f1": "2 * precision * recall / (precision + recall), with 1.0 when both are 1.0 and 0.0 when the denominator is zero otherwise.",
        "false_alignment_rate": "mean over cases of |P_tool minus E_tool| / |P_tool|, where E_tool and P_tool are old-tool/new-tool pair sets; 0.0 for a correct abstention.",
        "no_equivalent_accuracy": "mean over cases whose expected new tool set is empty of 1 when abstain is true and 0 otherwise.",
        "first_attempt_task_success": "mean over evaluated predictions of 1 only when the predicted adapted call or composed call actually succeeds in a fresh sandbox; provider and parse failures are excluded and counted separately.",
        "many_to_many_scoring": "D9 uses the full set of one-old-to-two-new tool and argument quadruples; D10 uses two old-tool-to-one-new-tool quadruples. Partial sets receive exact precision/recall, never a forced one-to-one reduction.",
    }


def _render_for_estimate(template: dict[str, Any], task: Any) -> str:
    encode = lambda values: json.dumps(values, ensure_ascii=True, sort_keys=True, default=str)
    return template["text"].format(
        task_description=task.task_description,
        candidate_contracts=encode([asdict(contract) for contract in task.new_contracts]),
        old_contracts=encode([asdict(contract) for contract in task.old_contracts]),
        verified_old_traces=encode([asdict(trace) for trace in task.verified_old_traces]),
    )


def _rate_limit_budget(
    cases: tuple[Gate07Case, ...],
    model_ids: tuple[str, ...],
    limits: dict[str, Any],
    ledger: dict[str, str] | None = None,
) -> dict[str, Any]:
    graded = tuple(case for case in cases if not case.held_out)
    arm_estimates: dict[str, dict[str, int]] = {}
    for arm_id, template in PROMPT_TEMPLATES.items():
        estimates = [max(1, math.ceil(len(_render_for_estimate(template, build_method_facing_task(case))) / 4)) for case in graded]
        arm_estimates[arm_id] = {"total_input_tokens_per_model": sum(estimates), "max_input_tokens_per_call": max(estimates)}
    base_calls = len(graded) * 4 * len(model_ids)
    total_input = sum(value["total_input_tokens_per_model"] for value in arm_estimates.values()) * len(model_ids)
    total_output = base_calls * 512
    return {
        "cases": len(graded),
        "arms": 4,
        "models": len(model_ids),
        "base_calls": base_calls,
        "retry_budget": 2,
        "max_attempts": base_calls * 3,
        "prompt_token_estimates": arm_estimates,
        "projected_input_tokens": total_input,
        "projected_output_tokens_at_max": total_output,
        "configured_limits": limits,
        "ledger": {
            "router_state_db": (ledger or {}).get("router_state_db", "gates/artifacts/gate07/router_state.sqlite3"),
            "request_ledger": (ledger or {}).get("request_ledger", "gates/artifacts/gate07/request_ledger.jsonl"),
            "owner": "one sequential runner process",
        },
        "headroom_rule": "Do not begin or continue when projected/actual demand would exceed any applicable org, pool, or per-key ceiling; keep the declared reserve frozen in the result.",
    }


def build_protocol(cases: tuple[Gate07Case, ...], model_ids: tuple[str, ...], *, repo_root: str | Path | None = None, created_at: str | None = None, model_verification: dict[str, Any] | None = None, rate_limits: dict[str, Any] | None = None, ledger: dict[str, str] | None = None, schema: str = "gate07.protocol.v1", amendment: dict[str, Any] | None = None) -> dict[str, Any]:
    graded = _manifest_records(cases, False)
    held_out = _manifest_records(cases, True)
    family_counts = {family: sum(record["family"] == family for record in graded) for family in FAMILY_NAMES}
    held_out_counts = {family: sum(record["family"] == family for record in held_out) for family in FAMILY_NAMES}
    capability = EvaluatorCapability()
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[3]
    git_head = _git_output(root, "rev-parse", "HEAD")
    return {
        "schema": schema,
        "amendment": amendment or {},
        "created_at_utc": created_at or datetime.now(timezone.utc).isoformat(),
        "git_head_at_freeze": git_head,
        "dataset": {
            "generator_seed": 20260827,
            "graded_count": len(graded),
            "held_out_count": len(held_out),
            "family_counts": family_counts,
            "held_out_family_counts": held_out_counts,
            **dataset_manifest_digests(cases),
        },
        "ground_truth": {
            "graded_sha256": ground_truth_digest(capability, graded_only=True),
            "all_cases_sha256": ground_truth_digest(capability, graded_only=False),
        },
        "baseline_arms": _arms(model_ids),
        "prompt_templates": PROMPT_TEMPLATES,
        "models": {
            "llm_ids": list(model_ids),
            "verification": model_verification or {"status": "not_run"},
            "offline": {
                "bi_encoder": {"name": "BAAI/bge-m3", "revision": "5617a9f61b028005a4858fdac845db406aefb181"},
                "cross_encoder": {"name": "BAAI/bge-reranker-v2-m3", "revision": "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"},
            },
        },
        "decoding": {
            "offline": {"device": "cpu", "normalize_embeddings": True, "local_files_only": True},
            "llm": {"temperature": 0.0, "seed": None, "seed_note": "Existing GroqClient does not transmit a seed; no provider determinism claim is made.", "max_tokens": 512},
        },
        "rate_limit_budget": _rate_limit_budget(cases, model_ids, rate_limits or {}, ledger),
        "timeouts_retries": {
            "llm_timeout_seconds": 120,
            "max_retries": 2,
            "max_attempts_per_call": 3,
            "429_policy": "Use existing GroqClient Retry-After or 15-second cooldown plus configured jitter; preserve round-robin cooldown.",
            "other_retry_cooldowns": {"auth_401": 3600, "server_5xx": 5, "network_or_timeout": 5},
            "failure_kinds": ["rate_limited", "timeout", "auth_failure", "network_failure", "provider_error", "parse_failure"],
        },
        "metrics": _metric_definitions(),
        "exclusions": {
            "provider_failure": "Exclude from all accuracy denominators after the frozen retry budget; report by typed failure kind and arm/model.",
            "parse_failure": "Exclude from accuracy denominators and report separately; never coerce an unparseable output into a wrong answer.",
            "case_exclusion": "A case may be excluded only when its frozen retry budget is exhausted by provider/parse failure; record the case and reason in a separate failure table.",
            "manifest_changes": "No post-freeze case selection, dropping, reweighting, or candidate reordering is allowed.",
            "held_out": "Held-out cases are not run in Phases 7.4 or 7.5.",
        },
        "decision_thresholds": {
            "family_minimum": 15,
            "strong_llm_saturates": {"tool_alignment_at_1": 0.95, "argument_mapping_f1": 0.90, "no_equivalent_accuracy": 0.90, "first_attempt_task_success": 0.90},
            "practically_meaningful_failure": {"tool_alignment_at_1_below": 0.80, "argument_mapping_f1_below": 0.75, "no_equivalent_accuracy_below": 0.80, "first_attempt_task_success_below": 0.80},
            "stable_failure_region": "A family with at least 15 graded cases whose strongest direct LLM and strongest offline arms are below a practically-meaningful threshold on the same load-bearing metric, with bootstrap 95% upper bound still below the saturation bar, ambiguity rate below 0.20, and observed first-attempt consequences.",
            "go": "Requires a stable failure region, low ambiguity, first-attempt linkage, and concrete information/mechanism unavailable to every baseline.",
            "reformulate": "Use when direct alignment saturates but no-equivalent/uncertainty remains hard, only split/merge remains, or history helps only under a narrower condition.",
            "stop": "Use when strong direct LLM mapping saturates realistic cases, hard cases are artificial/ambiguous, history adds no useful signal, or errors are generic planning/state failures.",
        },
        "research_fallback": "disabled; every live LLM call must use ProviderRouter(mode='research') and never Ollama fallback",
        "raw_artifact_policy": "Retain raw outputs under gates/artifacts/gate07/raw; never commit provider dumps or credential metadata.",
        "claims_boundary": "No novelty claim over ToolEVO, ContDa, or MCPEvol-Bench; schema similarity is not behavioral equivalence.",
    }


def write_protocol(protocol: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(protocol, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return target
