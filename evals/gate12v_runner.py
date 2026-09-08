"""Gate 12-V protocol freeze, live product-path collection, and reporting.

The live mode calls the same ``/ask`` route function used by the FastAPI
application.  It only changes provider selection and retry settings in the
current process; it never edits ``.env`` and never writes prompts to tracked
files.  Raw provider responses are retained only below the ignored
``gates/artifacts`` tree.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import time
from typing import Any, Iterator
from urllib import error, request

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROTOCOL_PATH = ROOT / "gates" / "baselines" / "GATE_12V_PROTOCOL.json"
GOLDEN_PATH = ROOT / "evals" / "datasets" / "golden_qa.jsonl"
CHUNKS_PATH = ROOT / "data" / "chunks" / "chunks_500.jsonl"
MANIFEST_PATH = ROOT / "data" / "manifests" / "documents_manifest.csv"
ARTIFACT_ROOT = ROOT / "gates" / "artifacts" / "gate12v"
SAMPLE_METADATA_FIELDS = (
    "question_id",
    "question",
    "category",
    "difficulty",
    "is_answerable",
    "must_cite",
    "relevant_chunk_ids",
)
REQUEST_BUDGET = 200
OPENROUTER_MIN_INTERVAL_SECONDS = 3.1
PROVIDER_TRANSPORT_RETRIES = 1
MAX_OUTPUT_TOKENS_CONTRACT = 1024
TEMPERATURE_CONTRACT = 0.1
SAMPLE_SEED = 20260908
V0_OVERLAY_PATHS = [
    "AGENTS.md",
    "PROJECT_STATE.md",
    "_agent_ops/PROJECT_CONTEXT_CARD.md",
    "_agent_ops/REPO_MAP.md",
    "_agent_ops/THIRD_PARTY_TOOLING.md",
    "skills/implementation-logger/scripts/append_log.py",
    "skills/project-context-cards/scripts/new_phase_card.py",
    "skills/rag-eval-harness/scripts/compute_retrieval_metrics.py",
    "skills/release-quality-gate/scripts/check_required_files.py",
    "skills/zone-brain/scripts/scan_deps.py",
    "_agent_ops/archive/",
    "_agent_ops/env_templates/",
    "_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_03.md",
    "_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_04.md",
    "_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07.md",
    "_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07_EXECUTION_PROMPT.md",
    "_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07_REPAIR_PROMPT.md",
    "_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_08.md",
    "_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_09.md",
    "_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_10.md",
    "_agent_ops/tools/check_repo_hygiene.py",
    "_agent_ops/tools/generate_context_card.py",
    "_agent_ops/tools/scan_deps.py",
    "_agent_ops/tools/summarize_implementation_log.py",
    "gates/results/GATE_07_FIX_PROMPT.md",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _load_metadata_rows(path: Path = GOLDEN_PATH) -> list[dict[str, Any]]:
    """Load only fields permitted before the live runs.

    In particular, this function does not copy or inspect ``expected_answer``.
    The report mode loads that field only after both provider runs exist.
    """

    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        rows.append({field: payload[field] for field in SAMPLE_METADATA_FIELDS})
    return rows


def select_stratified_sample(
    rows: list[dict[str, Any]],
    *,
    seed: int = SAMPLE_SEED,
    sample_size: int = 40,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Select a reproducible joint-stratified sample without expected answers."""

    if len(rows) < sample_size:
        raise ValueError(f"Need {sample_size} rows but found {len(rows)}.")
    unanswerable = sorted((row for row in rows if not row["is_answerable"]), key=lambda row: row["question_id"])
    answerable = [row for row in rows if row["is_answerable"]]
    if len(unanswerable) != 4:
        raise ValueError(f"Protocol expects exactly 4 unanswerable rows; found {len(unanswerable)}.")

    cells: dict[tuple[str, str, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in answerable:
        cells[(str(row["category"]), str(row["difficulty"]), bool(row["is_answerable"]))].append(row)
    ordered_cells = sorted(cells)
    answerable_target = sample_size - len(unanswerable)
    if answerable_target < len(ordered_cells):
        raise ValueError("Sample size is too small to cover every answerable joint stratum.")

    exact_targets = {
        key: answerable_target * len(cells[key]) / len(answerable)
        for key in ordered_cells
    }
    allocation = {key: 1 for key in ordered_cells}
    extra_ideal = {key: max(0.0, exact_targets[key] - 1.0) for key in ordered_cells}
    extra_floor = {
        key: min(len(cells[key]) - 1, math.floor(extra_ideal[key]))
        for key in ordered_cells
    }
    for key in ordered_cells:
        allocation[key] += extra_floor[key]
    target_extra = answerable_target - len(ordered_cells)
    if sum(extra_floor.values()) > target_extra:
        remove_count = sum(extra_floor.values()) - target_extra
        for key in sorted(
            ordered_cells,
            key=lambda item: (
                extra_ideal[item] - extra_floor[item],
                extra_ideal[item],
                tuple(str(part) for part in item),
            ),
        ):
            while remove_count and allocation[key] > 1:
                allocation[key] -= 1
                remove_count -= 1
            if not remove_count:
                break
    remaining = answerable_target - sum(allocation.values())
    while remaining > 0:
        candidates = [key for key in ordered_cells if allocation[key] < len(cells[key])]
        if not candidates:
            raise ValueError("Could not allocate the requested sample size.")
        key = max(
            candidates,
            key=lambda item: (
                extra_ideal[item] - (allocation[item] - 1),
                len(cells[item]),
                tuple(str(part) for part in item),
            ),
        )
        allocation[key] += 1
        remaining -= 1

    rng = random.Random(seed)
    selected = list(unanswerable)
    for key in ordered_cells:
        candidates = list(cells[key])
        rng.shuffle(candidates)
        selected.extend(candidates[: allocation[key]])
    selected.sort(key=lambda row: row["question_id"])

    allocation_rows = [
        {
            "category": key[0],
            "difficulty": key[1],
            "is_answerable": key[2],
            "population": len(cells[key]),
            "sample_count": allocation[key],
        }
        for key in ordered_cells
    ]
    dimensions = {
        field: dict(sorted(Counter(str(row[field]) for row in selected).items()))
        for field in ("category", "difficulty")
    }
    dimensions["is_answerable"] = dict(
        sorted(Counter(str(bool(row["is_answerable"])) for row in selected).items())
    )
    return selected, {
        "seed": seed,
        "sample_size": sample_size,
        "selection_fields": ["category", "difficulty", "is_answerable"],
        "metadata_only": True,
        "expected_answer_used_before_runs": False,
        "unanswerable_population": len(unanswerable),
        "unanswerable_included": len([row for row in selected if not row["is_answerable"]]),
        "joint_stratum_allocation": allocation_rows,
        "marginal_sample_counts": dimensions,
        "question_ids": [row["question_id"] for row in selected],
    }


def _canonical_protocol_bytes(payload: dict[str, Any]) -> bytes:
    without_integrity = dict(payload)
    without_integrity.pop("protocol_sha256", None)
    return (json.dumps(without_integrity, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_protocol() -> dict[str, Any]:
    rows = _load_metadata_rows()
    selected, sample = select_stratified_sample(rows)
    payload: dict[str, Any] = {
        "schema": "gate12v.protocol.v1",
        "gate": "12-V",
        "title": "Live validation of the OpenRouter product lane on the real corpus",
        "created_at_utc": _utc_now(),
        "scope": {
            "production_source_change": False,
            "deployment": False,
            "gcp_calls": False,
            "research_lane_invoked": False,
            "paid_openrouter_models": False,
            "env_file_edited": False,
        },
        "entry_receipts": {
            "head": _run_git("rev-parse", "HEAD"),
            "expected_head": "a6d50cb1a2349d8820de904dcc9ac842f2dc8d47",
            "remote_main_sha": "a6d50cb1a2349d8820de904dcc9ac842f2dc8d47",
            "status_path_count_at_v0": len(V0_OVERLAY_PATHS),
            "status_paths_at_v0": V0_OVERLAY_PATHS,
            "cached_path_count_at_v0": 0,
            "pytest": {
                "command": ".venv\\Scripts\\python.exe -m pytest -q --basetemp=<external dir>",
                "result": "591 passed, 3 warnings",
                "duration_seconds": 456.01,
                "basetemp_external": True,
            },
            "env_presence_count_only": {
                "OPENROUTER_API_KEY": 1,
                "OPENROUTER_MODEL": 1,
                "OPENROUTER_MODEL_FALLBACK": 1,
                "GROQ_API_KEY": 1,
            },
            "openrouter_credit_preflight": {
                "endpoint": "GET https://openrouter.ai/api/v1/key",
                "http_status": 200,
                "limit_remaining": 0.2,
                "usage": 0,
                "usage_daily": 0,
                "secret_value_recorded": False,
            },
            "openrouter_adapter_ledger_preflight": {
                "scope": "new per-process ledger; prior process history is not durable",
                "utc_day": datetime.now(timezone.utc).date().isoformat(),
                "ceiling": 1000,
                "used": 0,
                "reserved": 0,
                "remaining": 1000,
            },
            "local_corpus": {
                "chunks_path": "data/chunks/chunks_500.jsonl",
                "chunks_sha256": _sha256(CHUNKS_PATH),
                "chunk_count": 695,
                "manifest_path": "data/manifests/documents_manifest.csv",
                "manifest_sha256": _sha256(MANIFEST_PATH),
                "manifest_document_count": 37,
                "retrieval_smoke": {
                    "retriever": "HybridRetriever",
                    "query": "Điều kiện tốt nghiệp là gì?",
                    "top_k": 5,
                    "retrieved_count": 5,
                    "first_chunk_id": "ug_graduation_conditions_s001_c001",
                },
            },
        },
        "dataset_boundary": {
            "product_qa_path": "evals/datasets/golden_qa.jsonl",
            "product_qa_sha256": _sha256(GOLDEN_PATH),
            "product_qa_count": len(rows),
            "product_qa_fields": list(SAMPLE_METADATA_FIELDS) + ["expected_answer"],
            "research_lane_excluded": True,
            "gate07_protocol": "gates/baselines/GATE_07_PROTOCOL_V4.json",
            "gate08_protocol": "gates/baselines/GATE_08_PROTOCOL.json",
            "gate07_source": "research/gate07/dataset/generator.py build_v4_cases",
            "gate07_manifest_sha256": "sha256:435d91e1d5c97f1a484eee4f2934c7b97d328d4437a04d51970aec30b7c41983",
            "gate08_source": "research/gate07/dataset/generator.py build_v4_cases (unchanged)",
            "distinction_statement": "golden_qa.jsonl is the product evaluation set over the 37-document policy corpus; Gate 07/08 use the separate research/gate07 generated contract-drift corpus and research protocols. No research runner, protocol, baseline, metric, or dataset is invoked or modified.",
        },
        "sample": sample,
        "product_path": {
            "entrypoint": "app.api.routes_query.ask",
            "request_contract": "POST /ask equivalent AskRequest(question, top_k=5, debug=true, use_guardrail=true)",
            "path": "routes_query.ask -> app.core.config.get_answer_generator -> ContextBuilder -> HybridRetriever -> GuardrailEngine -> PromptBuilder -> ProviderRouter -> AnswerGenerator citation verification/evidence state",
            "retriever": "default HybridRetriever over data/chunks/chunks_500.jsonl",
            "top_k": 5,
            "guardrails_enabled": True,
            "debug_enabled": True,
            "research_mode": False,
            "no_agent_or_mcp_path": True,
        },
        "provider_configuration": {
            "mode": "development",
            "groq_control": "explicit LLM_PROVIDER=groq process override; one Groq client/key seam",
            "openrouter_lane": "explicit LLM_PROVIDER=openrouter process override; shipped free models array",
            "openrouter_primary": "nvidia/nemotron-3-super-120b-a12b:free",
            "openrouter_fallback": "google/gemma-4-31b-it:free",
            "temperature_contract": TEMPERATURE_CONTRACT,
            "max_output_tokens_contract": MAX_OUTPUT_TOKENS_CONTRACT,
            "actual_payload_field_check": "record whether max_tokens was transmitted; no production source injection is allowed",
            "paid_guard": "OpenRouter allow_paid_models=false; live catalog and frozen free catalog guards remain active",
        },
        "retry_policy": {
            "runner_question_retries": 0,
            "provider_transport_max_retries": PROVIDER_TRANSPORT_RETRIES,
            "answer_generator_citation_retry": "unchanged product behavior: one retry is eligible only when current_provider is groq or ollama; openrouter is not eligible in the shipped _can_retry_provider contract",
            "first_attempt_rule": "A question with any retry is not a first-attempt success even if a later response parses or answers well.",
            "request_budget_includes_retries": True,
        },
        "request_budget": {
            "hard_ceiling_total_generation_post_requests": REQUEST_BUDGET,
            "nominal_questions_per_provider": 40,
            "nominal_generation_requests": 80,
            "openrouter_min_inter_post_interval_seconds": OPENROUTER_MIN_INTERVAL_SECONDS,
            "catalog_and_credit_gets_not_generation_requests": True,
            "stop_condition": "Stop before any generation POST that would exceed 200 total.",
        },
        "metrics": {
            "citation_validity": "overall numerator = final product responses whose CitationVerification.is_valid is true; denominator = all 40 completed questions. Refusals are valid because the product verifier treats a refusal as having no citation obligation. Also report non-refusal-only rate.",
            "citation_grounding": "Use unique cited chunk_ids on answerable questions. Precision numerator = cited ids intersect relevant_chunk_ids; denominator = all unique cited ids. Recall numerator = same intersection; denominator = all relevant_chunk_ids. Report Wilson 95% intervals and raw counts.",
            "refusal_correctness": "A refusal is correct exactly when is_answerable=false; report accuracy over all 40 and false-answer rate over the 4 unanswerable rows.",
            "must_cite": "For each must_cite row, a refusal is safe-compliant; otherwise compliance requires at least one citation and CitationVerification.is_valid=true.",
            "schema_validity": "Denominator = sampled questions that reached at least one provider generation POST. First-attempt numerator = first raw provider response had choices[0].message.content that parsed as a JSON object. Later retries never count as first-attempt success.",
            "answer_quality": "For 36 answerable rows, use existing evals.metrics.generation_metrics.token_f1 against expected_answer after both provider runs; answer_correctness is token_f1 >= 0.45. Expected answers are loaded only in post-run report mode.",
            "latency": "End-to-end elapsed time for the /ask product path per question; report p50 and p95 using the floor((n-1)*p) index rule. Also report per-generation-POST latency.",
            "token_behavior": "Use provider usage fields from every raw generation response; report reasoning_tokens_actual and output_tokens_actual distributions, missingness, completion values above 1024, and finish_reason=length count.",
            "fallback_activation": "OpenRouter question-level rate = rows whose actual serving model is gemma divided by provider-attempted questions; unknown/unserved rows remain visible. Break down all metrics by actual serving model class.",
            "error_taxonomy": "Count typed error kinds from final provider invocation and raw calls; preserve provider error bodies in ignored artifacts and never smooth errors into success.",
        },
        "thresholds": {
            "justification": "The lane is a user-facing grounded QA product path. Thresholds require reliable first-attempt structured output, grounded citations, safe abstention, useful answer overlap, bounded latency, and enough primary serving to make the configured primary meaningful; the 10-point parity margin is the maximum acceptable degradation against the incumbent control.",
            "openrouter_schema_validity_first_attempt_min": 0.90,
            "openrouter_citation_validity_min": 0.90,
            "openrouter_citation_grounding_precision_min": 0.90,
            "openrouter_citation_grounding_recall_min": 0.75,
            "openrouter_false_answer_rate_unanswerable_max": 0.05,
            "openrouter_must_cite_compliance_min": 0.90,
            "openrouter_answer_correctness_rate_min": 0.70,
            "openrouter_answer_token_f1_min": 0.45,
            "openrouter_p95_latency_ms_max": 30000,
            "openrouter_finish_length_rate_max": 0.05,
            "openrouter_fallback_activation_rate_max": 0.50,
            "quality_gap_openrouter_minus_groq_min": -0.10,
            "zero_paid_spend_required": True,
            "all_40_questions_completed_per_provider_required": True,
        },
        "artifacts": {
            "raw_and_run_root": "gates/artifacts/gate12v/ (ignored by gates/artifacts/.gitignore)",
            "tracked_result": "gates/results/GATE_12V_RESULT.md",
            "protocol_sha256_definition": "SHA-256 of canonical sorted-key JSON with protocol_sha256 omitted; the stored value is prefixed sha256:.",
            "raw_prompt_policy": "No prompt or corpus context is written to any tracked file; raw provider response records are ignored artifacts only.",
        },
    }
    payload["protocol_sha256"] = "sha256:" + hashlib.sha256(_canonical_protocol_bytes(payload)).hexdigest()
    return payload


def freeze_protocol(path: Path = PROTOCOL_PATH) -> dict[str, Any]:
    payload = build_protocol()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _load_protocol(path: Path = PROTOCOL_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = payload.get("protocol_sha256")
    actual = "sha256:" + hashlib.sha256(_canonical_protocol_bytes(payload)).hexdigest()
    if expected != actual:
        raise RuntimeError(f"Protocol SHA mismatch: stored={expected} actual={actual}")
    if payload.get("sample", {}).get("expected_answer_used_before_runs") is not False:
        raise RuntimeError("Protocol does not freeze metadata-only sampling.")
    if payload.get("scope", {}).get("research_lane_invoked") is not False:
        raise RuntimeError("Research lane boundary is not frozen closed.")
    return payload


def _redact(value: Any) -> Any:
    text = str(value)
    for name in ("OPENROUTER_API_KEY", "GROQ_API_KEY"):
        secret = os.environ.get(name, "").strip()
        if secret:
            text = text.replace(secret, "<redacted>")
    return text


class _CapturedResponse:
    def __init__(self, response: Any, recorder: "LiveRecorder", call: dict[str, Any]) -> None:
        self._response = response
        self._recorder = recorder
        self._call = call
        self.status = getattr(response, "status", None)
        self.headers = getattr(response, "headers", {})

    def __enter__(self) -> "_CapturedResponse":
        self._response.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> Any:
        return self._response.__exit__(exc_type, exc_value, traceback)

    def read(self, *args: Any, **kwargs: Any) -> bytes:
        body = self._response.read(*args, **kwargs)
        if isinstance(body, bytes):
            raw = body.decode("utf-8", errors="replace")
        else:
            raw = str(body)
        self._call["raw_body"] = _redact(raw)
        try:
            self._call["parsed_body"] = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            self._call["parsed_body"] = None
        return body


class LiveRecorder:
    def __init__(
        self,
        provider: str,
        *,
        request_budget: int = REQUEST_BUDGET,
        shared_budget: dict[str, int] | None = None,
    ) -> None:
        self.provider = provider
        self.request_budget = request_budget
        self.shared_budget = shared_budget if shared_budget is not None else {"count": 0}
        self.generation_request_count = 0
        self.calls: list[dict[str, Any]] = []
        self.current_question_id: str | None = None
        self.current_question_started: float | None = None
        self.next_openrouter_post_at = 0.0
        self.pacing_sleep_seconds = 0.0

    def before_question(self, question_id: str) -> None:
        self.current_question_id = question_id
        self.current_question_started = time.perf_counter()

    def _is_generation_post(self, req: Any) -> bool:
        url = str(getattr(req, "full_url", ""))
        method = getattr(req, "method", None)
        if not method and hasattr(req, "get_method"):
            method = req.get_method()
        method = method or "GET"
        return method.upper() == "POST" and url.endswith("/chat/completions")

    def urlopen(self, original: Any, req: Any, *args: Any, **kwargs: Any) -> Any:
        is_generation = self._is_generation_post(req)
        url = str(getattr(req, "full_url", ""))
        if is_generation:
            if self.shared_budget["count"] >= self.request_budget:
                raise RuntimeError("GATE_12V_REQUEST_BUDGET_EXCEEDED")
            if self.provider == "openrouter":
                wait = max(0.0, self.next_openrouter_post_at - time.monotonic())
                if wait:
                    time.sleep(wait)
                    self.pacing_sleep_seconds += wait
                self.next_openrouter_post_at = time.monotonic() + OPENROUTER_MIN_INTERVAL_SECONDS
            self.shared_budget["count"] += 1
            self.generation_request_count += 1
        call = {
            "call_index": len(self.calls) + 1,
            "question_id": self.current_question_id,
            "provider": self.provider,
            "request_kind": "generation_post" if is_generation else "other",
            "url": url,
            "method": str(getattr(req, "method", None) or req.get_method()),
            "started_at_utc": _utc_now(),
            "http_status": None,
            "latency_ms": None,
            "raw_body": None,
            "parsed_body": None,
        }
        if is_generation:
            try:
                request_payload = json.loads(getattr(req, "data", b"").decode("utf-8"))
            except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
                request_payload = {}
            if isinstance(request_payload, dict):
                call["request_contract"] = {
                    "max_tokens_present": "max_tokens" in request_payload,
                    "max_tokens": request_payload.get("max_tokens"),
                    "temperature": request_payload.get("temperature"),
                    "model": request_payload.get("model"),
                    "models": request_payload.get("models"),
                }
        started = time.perf_counter()
        try:
            response = original(req, *args, **kwargs)
        except error.HTTPError as exc:
            body = exc.read()
            if isinstance(body, bytes):
                raw = body.decode("utf-8", errors="replace")
            else:
                raw = str(body)
            call["http_status"] = exc.code
            call["raw_body"] = _redact(raw)
            try:
                call["parsed_body"] = json.loads(raw)
            except (TypeError, ValueError, json.JSONDecodeError):
                call["parsed_body"] = None
            call["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
            self.calls.append(call)
            exc.fp = io.BytesIO(body if isinstance(body, bytes) else str(body).encode("utf-8"))
            raise
        except Exception as exc:
            call["error_type"] = type(exc).__name__
            call["error_text"] = _redact(exc)
            call["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
            self.calls.append(call)
            raise
        call["http_status"] = getattr(response, "status", None)
        call["response_headers"] = {
            str(key): _redact(value)
            for key, value in getattr(response, "headers", {}).items()
            if str(key).casefold() in {"retry-after", "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset"}
        }
        call["_started_monotonic"] = started
        self.calls.append(call)
        return _CapturedResponse(response, self, call)

    def calls_for_question(self, question_id: str) -> list[dict[str, Any]]:
        return [call for call in self.calls if call.get("question_id") == question_id and call.get("request_kind") == "generation_post"]


@contextmanager
def capture_urlopen(recorder: LiveRecorder) -> Iterator[None]:
    original = request.urlopen
    request.urlopen = lambda req, *args, **kwargs: recorder.urlopen(original, req, *args, **kwargs)
    try:
        yield
    finally:
        request.urlopen = original


def _response_to_dict(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump(mode="json")
    if hasattr(response, "dict"):
        return response.dict()
    return dict(response)


def _classify_serving_model(model: Any) -> str:
    value = str(model or "")
    if "nemotron-3-super" in value:
        return "nemotron"
    if "gemma-4-31b-it" in value:
        return "gemma"
    if not value:
        return "unserved"
    return value


def _extract_usage(body: Any) -> dict[str, int] | None:
    if not isinstance(body, dict) or not isinstance(body.get("usage"), dict):
        return None
    usage = body["usage"]
    details = usage.get("completion_tokens_details")
    values = {
        "input_tokens_actual": usage.get("prompt_tokens", usage.get("input_tokens")),
        "output_tokens_actual": usage.get("completion_tokens", usage.get("output_tokens")),
        "total_tokens_actual": usage.get("total_tokens"),
        "reasoning_tokens_actual": details.get("reasoning_tokens") if isinstance(details, dict) else None,
    }
    normalized = {
        key: int(value)
        for key, value in values.items()
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
    }
    if "total_tokens_actual" not in normalized and {"input_tokens_actual", "output_tokens_actual"} <= normalized.keys():
        normalized["total_tokens_actual"] = normalized["input_tokens_actual"] + normalized["output_tokens_actual"]
    return normalized or None


def _first_attempt_schema_valid(call: dict[str, Any]) -> bool:
    body = call.get("parsed_body")
    if not isinstance(body, dict):
        return False
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return False
    message = choices[0].get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        return False
    try:
        parsed = json.loads(content)
    except (TypeError, ValueError, json.JSONDecodeError):
        return False
    return isinstance(parsed, dict)


def _call_summary(call: dict[str, Any], *, typed_error_kind: str | None) -> dict[str, Any]:
    body = call.get("parsed_body")
    choice = None
    if isinstance(body, dict) and isinstance(body.get("choices"), list) and body["choices"]:
        if isinstance(body["choices"][0], dict):
            choice = body["choices"][0]
    served_model = body.get("model") if isinstance(body, dict) and isinstance(body.get("model"), str) else None
    served_provider = body.get("provider") if isinstance(body, dict) and isinstance(body.get("provider"), str) else None
    return {
        "call_index": call.get("call_index"),
        "http_status": call.get("http_status"),
        "latency_ms": call.get("latency_ms"),
        "finish_reason": choice.get("finish_reason") if isinstance(choice, dict) else None,
        "usage": _extract_usage(body),
        "served_model": served_model,
        "served_provider": served_provider,
        "typed_error_kind": typed_error_kind,
        "response_headers": call.get("response_headers", {}),
        "raw_body": call.get("raw_body"),
        "parsed_body": call.get("parsed_body"),
        "request_contract": call.get("request_contract", {}),
    }


def _typed_error_kind(invocation: Any) -> str | None:
    return getattr(invocation, "failure_kind", None)


def _provider_client_snapshot(router: Any, provider: str) -> dict[str, Any]:
    if provider == "openrouter":
        client = router.openrouter_client
        status = client.status()
        return {
            "model": status.get("model"),
            "configured_model": status.get("configured_model"),
            "fallback_model": status.get("fallback_model"),
            "daily_requests_used": status.get("daily_requests_used"),
            "daily_requests_remaining": status.get("daily_requests_remaining"),
            "last_served_model": status.get("last_served_model"),
            "last_served_provider": status.get("last_served_provider"),
            "last_error_kind": status.get("last_error_kind"),
        }
    return router.groq_client.stats()


def _clear_product_caches() -> Any:
    from app.core import config

    for name in (
        "get_settings",
        "get_store",
        "get_version_resolver",
        "get_context_builder",
        "get_provider_router",
        "get_answer_generator",
    ):
        getattr(config, name).cache_clear()
    from app.api import routes_query

    return routes_query


def _run_provider(
    protocol: dict[str, Any],
    provider: str,
    output_root: Path,
    *,
    shared_budget: dict[str, int],
) -> dict[str, Any]:
    if provider not in {"groq", "openrouter"}:
        raise ValueError(f"Unsupported provider: {provider}")
    load_dotenv(dotenv_path=ROOT / ".env", override=True)
    os.environ["LLM_PROVIDER"] = provider
    os.environ["PROVIDER_MODE"] = "development"
    os.environ["GROQ_MAX_RETRIES"] = str(PROVIDER_TRANSPORT_RETRIES)
    os.environ["OPENROUTER_MAX_RETRIES"] = str(PROVIDER_TRANSPORT_RETRIES)
    os.environ["OPENROUTER_ALLOW_PAID_MODELS"] = "false"
    routes_query = _clear_product_caches()
    from app.core.config import get_provider_router
    from app.schemas.query import AskRequest

    router = get_provider_router()
    if router.current_provider() != provider:
        raise RuntimeError(f"Provider selection mismatch: requested={provider} actual={router.current_provider()}")
    if provider == "openrouter" and router.mode == "research":
        raise RuntimeError("OpenRouter research mode is forbidden for Gate 12-V.")
    recorder = LiveRecorder(provider, request_budget=REQUEST_BUDGET, shared_budget=shared_budget)
    output_dir = output_root / provider
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _load_metadata_rows()
    by_id = {row["question_id"]: row for row in rows}
    sample_ids = protocol["sample"]["question_ids"]
    if set(sample_ids) - set(by_id):
        raise RuntimeError("Protocol sample contains an unknown question id.")
    run_records: list[dict[str, Any]] = []
    raw_path = output_dir / "raw_responses.jsonl"
    records_path = output_dir / "records.jsonl"
    with raw_path.open("w", encoding="utf-8") as raw_handle, records_path.open("w", encoding="utf-8") as record_handle:
        with capture_urlopen(recorder):
            for position, question_id in enumerate(sample_ids, start=1):
                question_row = by_id[question_id]
                recorder.before_question(question_id)
                started = time.perf_counter()
                try:
                    response = routes_query.ask(
                        AskRequest(
                            question=question_row["question"],
                            top_k=protocol["product_path"]["top_k"],
                            debug=True,
                            use_guardrail=True,
                        )
                    )
                    final_response = _response_to_dict(response)
                    route_error = None
                except Exception as exc:
                    final_response = {
                        "answer": "",
                        "citations": [],
                        "confidence": 0.0,
                        "refusal": False,
                        "refusal_reason": None,
                        "citation_verification": {"is_valid": False, "errors": [type(exc).__name__]},
                        "evidence_state": None,
                        "generation": None,
                        "retrieval_debug": {},
                    }
                    route_error = _redact(exc)
                elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
                calls = recorder.calls_for_question(question_id)
                generation = final_response.get("generation") or {}
                error_kind = generation.get("failure_kind")
                if route_error and not error_kind:
                    error_kind = "route_error"
                summaries = [_call_summary(call, typed_error_kind=error_kind) for call in calls]
                for call, summary in zip(calls, summaries, strict=False):
                    raw_payload = dict(call)
                    raw_payload.pop("_started_monotonic", None)
                    raw_payload["typed_error_kind"] = error_kind
                    raw_payload["finish_reason"] = summary.get("finish_reason")
                    raw_payload["usage"] = summary.get("usage")
                    raw_payload["served_model"] = summary.get("served_model")
                    raw_payload["served_provider"] = summary.get("served_provider")
                    raw_handle.write(json.dumps(raw_payload, ensure_ascii=False) + "\n")
                first_call = calls[0] if calls else None
                first_schema_valid = _first_attempt_schema_valid(first_call) if first_call else None
                served_model = generation.get("model") or (summaries[-1].get("served_model") if summaries else None)
                record = {
                    "started_at_utc": _utc_now(),
                    "position": position,
                    "question_id": question_id,
                    "category": question_row["category"],
                    "difficulty": question_row["difficulty"],
                    "is_answerable": question_row["is_answerable"],
                    "must_cite": question_row["must_cite"],
                    "relevant_chunk_ids": question_row["relevant_chunk_ids"],
                    "final_response": final_response,
                    "retrieved_chunk_ids": (final_response.get("retrieval_debug") or {}).get("chunk_ids", []),
                    "latency_ms": elapsed_ms,
                    "provider_request_count": len(calls),
                    "raw_calls": summaries,
                    "first_attempt_schema_valid": first_schema_valid,
                    "retried": len(calls) > 1,
                    "typed_error_kind": error_kind,
                    "error": route_error,
                    "requested_model": generation.get("requested_model"),
                    "served_model": served_model,
                    "served_provider": generation.get("served_provider") or (summaries[-1].get("served_provider") if summaries else None),
                    "serving_model_class": _classify_serving_model(served_model),
                    "fallback_used": generation.get("fallback_used"),
                }
                record_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                record_handle.flush()
                raw_handle.flush()
                run_records.append(record)
                print(
                    json.dumps(
                        {
                            "provider": provider,
                            "position": position,
                            "total": len(sample_ids),
                            "question_id": question_id,
                            "generation_posts_total": recorder.generation_request_count,
                            "question_generation_posts": len(calls),
                            "serving_model": record["serving_model_class"],
                            "typed_error_kind": error_kind,
                            "latency_ms": elapsed_ms,
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
                if shared_budget["count"] >= REQUEST_BUDGET and position < len(sample_ids):
                    raise RuntimeError("GATE_12V_REQUEST_BUDGET_EXCEEDED")
    receipt = {
        "schema": "gate12v.run_receipt.v1",
        "provider": provider,
        "mode": router.mode,
        "started_at_utc": run_records[0].get("started_at_utc") if run_records else _utc_now(),
        "finished_at_utc": _utc_now(),
        "protocol_sha256": protocol["protocol_sha256"],
        "question_count": len(run_records),
        "generation_post_count": recorder.generation_request_count,
        "generation_post_count_total_budget": shared_budget["count"],
        "pacing_sleep_seconds": round(recorder.pacing_sleep_seconds, 3),
        "provider_client_snapshot": _provider_client_snapshot(router, provider),
        "raw_path": str(raw_path.relative_to(ROOT)).replace("\\", "/"),
        "records_path": str(records_path.relative_to(ROOT)).replace("\\", "/"),
        "paid_spend": 0,
        "secret_values_recorded": False,
    }
    (output_dir / "run_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def _load_records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _attach_expected_answers(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expected_by_id: dict[str, str] = {}
    for line in GOLDEN_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            expected_by_id[payload["question_id"]] = str(payload["expected_answer"])
    enriched = []
    for record in records:
        copy = dict(record)
        copy["expected_answer"] = expected_by_id[record["question_id"]]
        enriched.append(copy)
    return enriched


def _redact_example(text: Any) -> str:
    return _redact(text)


def _failure_analysis(groq_records: list[dict[str, Any]], open_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groq_by_id = {row["question_id"]: row for row in groq_records}
    output: list[dict[str, Any]] = []
    for row in open_records:
        groq = groq_by_id.get(row["question_id"], {})
        final = row.get("final_response") or {}
        answerable = bool(row.get("is_answerable"))
        relevant = set(row.get("relevant_chunk_ids") or [])
        retrieved = set(row.get("retrieved_chunk_ids") or [])
        groq_retrieved = set(groq.get("retrieved_chunk_ids") or [])
        kind = row.get("typed_error_kind")
        cause = None
        detail = None
        if kind == "rate_limited":
            cause, detail = "rate_limit", "typed rate_limited outcome"
        elif kind == "provider_error":
            error_text = " ".join(
                str(call.get("raw_body") or "") for call in row.get("raw_calls") or []
            ).casefold()
            cause = "upstream_502" if "502" in error_text or "overload" in error_text else "provider_error"
            detail = "typed provider_error; raw response retained in ignored artifact"
        elif any(call.get("finish_reason") == "length" for call in row.get("raw_calls") or []):
            cause, detail = "truncation", "finish_reason=length"
        elif row.get("first_attempt_schema_valid") is False and row.get("provider_request_count", 0):
            cause, detail = "schema_violation", "first provider response was not a JSON object"
        elif not answerable and not bool(final.get("refusal")):
            cause, detail = "wrong_refusal", "unanswerable question received a non-refusal final response"
        elif answerable and not relevant.intersection(retrieved) and not relevant.intersection(groq_retrieved):
            cause, detail = "retrieval_miss_affecting_both", "both provider runs missed the relevant chunk set"
        elif answerable and bool((final.get("citation_verification") or {}).get("is_valid")) is False:
            cause, detail = "hallucinated_citation", "final product citation verification failed"
        if cause:
            output.append(
                {
                    "question_id": row["question_id"],
                    "classification": cause,
                    "provider_caused": cause not in {"retrieval_miss_affecting_both"},
                    "detail": detail,
                    "openrouter_error_kind": kind,
                    "openrouter_serving_model": row.get("serving_model_class"),
                }
            )
    return output


def _examples(groq_records: list[dict[str, Any]], open_records: list[dict[str, Any]], failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groq_by_id = {row["question_id"]: row for row in groq_records}
    examples: list[dict[str, Any]] = []
    failure_ids = [item["question_id"] for item in failures]
    for question_id in failure_ids[:2]:
        row = next(item for item in open_records if item["question_id"] == question_id)
        examples.append(
            {
                "question_id": question_id,
                "classification": next(item["classification"] for item in failures if item["question_id"] == question_id),
                "openrouter_answer_verbatim": _redact_example((row.get("final_response") or {}).get("answer", "")),
                "openrouter_error_verbatim": _redact_example(
                    "\n".join(str(call.get("raw_body") or "") for call in row.get("raw_calls") or [])
                ),
                "openrouter_citations_verbatim": row.get("final_response", {}).get("citations", []),
            }
        )
    for row in open_records:
        if len(examples) >= 5:
            break
        groq = groq_by_id.get(row["question_id"], {})
        if not groq:
            continue
        if row["question_id"] in failure_ids:
            continue
        open_answer = str((row.get("final_response") or {}).get("answer", ""))
        groq_answer = str((groq.get("final_response") or {}).get("answer", ""))
        if open_answer != groq_answer:
            examples.append(
                {
                    "question_id": row["question_id"],
                    "classification": "provider_output_difference_for_review",
                    "openrouter_answer_verbatim": _redact_example(open_answer),
                    "groq_answer_verbatim": _redact_example(groq_answer),
                    "openrouter_citations_verbatim": row.get("final_response", {}).get("citations", []),
                    "groq_citations_verbatim": groq.get("final_response", {}).get("citations", []),
                }
            )
    return examples[:5]


def report(protocol: dict[str, Any], artifact_root: Path = ARTIFACT_ROOT) -> dict[str, Any]:
    from evals.metrics.gate12v_metrics import compute_gate12v_metrics, quality_gap

    groq_records = _attach_expected_answers(_load_records(artifact_root / "groq" / "records.jsonl"))
    open_records = _attach_expected_answers(_load_records(artifact_root / "openrouter" / "records.jsonl"))
    if len(groq_records) != 40 or len(open_records) != 40:
        raise RuntimeError(f"Expected 40 records per provider; got groq={len(groq_records)} openrouter={len(open_records)}")
    groq_metrics = compute_gate12v_metrics(groq_records)
    open_metrics = compute_gate12v_metrics(open_records)
    failures = _failure_analysis(groq_records, open_records)
    payload = {
        "schema": "gate12v.report.v1",
        "generated_at_utc": _utc_now(),
        "protocol_sha256": protocol["protocol_sha256"],
        "groq": groq_metrics,
        "openrouter": open_metrics,
        "quality_gap_openrouter_minus_groq": quality_gap(open_metrics["overall"], groq_metrics["overall"]),
        "failure_analysis": failures,
        "examples": _examples(groq_records, open_records, failures),
        "request_accounting": {
            "groq_generation_post_count": groq_metrics["overall"]["raw_generation_request_count"],
            "openrouter_generation_post_count": open_metrics["overall"]["raw_generation_request_count"],
            "total_generation_post_count": groq_metrics["overall"]["raw_generation_request_count"] + open_metrics["overall"]["raw_generation_request_count"],
            "hard_ceiling": REQUEST_BUDGET,
            "openrouter_paid_spend": 0,
            "paid_spend_evidence": "OpenRouter /key preflight and per-run free guard; no paid model override; reported cost is zero.",
        },
    }
    output_path = artifact_root / "metrics_report.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report_path": str(output_path), "total_generation_post_count": payload["request_accounting"]["total_generation_post_count"], "failure_count": len(failures)}, ensure_ascii=False, indent=2))
    return payload


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Gate 12-V protocol/live runner/report.")
    parser.add_argument("--freeze-protocol", action="store_true")
    parser.add_argument("--provider", choices=["groq", "openrouter", "both"])
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--protocol", default=str(PROTOCOL_PATH))
    parser.add_argument("--artifact-root", default=str(ARTIFACT_ROOT))
    args = parser.parse_args(argv)
    protocol_path = Path(args.protocol)
    artifact_root = Path(args.artifact_root)
    if args.freeze_protocol:
        payload = freeze_protocol(protocol_path)
        print(json.dumps({"protocol_path": str(protocol_path), "protocol_sha256": payload["protocol_sha256"], "sample_question_ids": payload["sample"]["question_ids"]}, ensure_ascii=False, indent=2))
        return 0
    protocol = _load_protocol(protocol_path)
    if args.report:
        report(protocol, artifact_root)
        return 0
    if not args.provider:
        parser.error("one of --freeze-protocol, --report, or --provider is required")
    providers = ["groq", "openrouter"] if args.provider == "both" else [args.provider]
    shared_budget = {"count": 0}
    for provider in providers:
        _run_provider(protocol, provider, artifact_root, shared_budget=shared_budget)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
