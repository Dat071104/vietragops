"""Run the bounded Gate 16 generation configuration probe.

The recorder deliberately omits request messages from its output.  It keeps
only the request contract, response metadata, usage, and product answer so the
ignored probe artifact is useful for accounting without duplicating prompts.
"""

from __future__ import annotations

import argparse
from collections import Counter
from io import BytesIO
import json
from pathlib import Path
import os
import sys
import time
from typing import Any
from urllib import error

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rag.generation import AnswerGenerator, ContextBuilder, GuardrailEngine
from rag.generation.answer_generator import AnswerGeneratorConfig
from rag.generation.openrouter_client import I2_FREE_MODEL_CATALOG, OpenRouterClient
from rag.generation.provider_router import ProviderRouter
from rag.retrieval import ChunkIndexStore, HybridRetriever


PRIMARY = "nvidia/nemotron-3-super-120b-a12b:free"
GEMMA = "google/gemma-4-31b-it:free"
FROZEN_PROBE = [
    ("dev_q003", "email_usage", "easy"),
    ("dev_q006", "academic_schedule", "medium"),
    ("dev_q012", "course_registration", "easy"),
    ("gold_credit_requirement_096", "credit_requirement", "hard"),
    ("gold_curriculum_structure_006", "curriculum_structure", "hard"),
    ("gold_manual_002", "policy_exception", "medium"),
    ("gold_manual_003", "source_conflict", "hard"),
    ("gold_training_regulation_068", "training_regulation", "hard"),
]


class _ReplayResponse:
    def __init__(self, status: int, headers: dict[str, str], body: bytes) -> None:
        self.status = status
        self.headers = headers
        self._body = body

    def __enter__(self) -> "_ReplayResponse":
        return self

    def __exit__(self, *args: Any) -> bool:
        return False

    def read(self) -> bytes:
        return self._body


def _safe_request_contract(raw_request: Any) -> dict[str, Any]:
    payload = json.loads(raw_request.data.decode("utf-8")) if raw_request.data else {}
    return {
        "method": raw_request.method,
        "url": raw_request.full_url,
        "models": payload.get("models"),
        "temperature": payload.get("temperature"),
        "response_format": payload.get("response_format"),
        "max_tokens": payload.get("max_tokens"),
        "reasoning": payload.get("reasoning"),
    }


def _body_summary(body: bytes) -> dict[str, Any]:
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"json": False, "raw_body": body.decode("utf-8", errors="replace")}
    summary: dict[str, Any] = {"json": True, "body": parsed}
    if isinstance(parsed, dict):
        choices = parsed.get("choices")
        choice = choices[0] if isinstance(choices, list) and choices else None
        if isinstance(choice, dict):
            summary["finish_reason"] = choice.get("finish_reason")
        usage = parsed.get("usage")
        if isinstance(usage, dict):
            details = usage.get("completion_tokens_details")
            summary["usage"] = {
                "input_tokens_actual": usage.get("prompt_tokens", usage.get("input_tokens")),
                "output_tokens_actual": usage.get("completion_tokens", usage.get("output_tokens")),
                "total_tokens_actual": usage.get("total_tokens"),
                "reasoning_tokens_actual": details.get("reasoning_tokens") if isinstance(details, dict) else None,
            }
        summary["served_model"] = parsed.get("model")
        summary["served_provider"] = parsed.get("provider")
        error_payload = parsed.get("error")
        if isinstance(error_payload, dict):
            summary["error"] = {
                "code": error_payload.get("code"),
                "message": error_payload.get("message"),
            }
    return summary


def _percentile(values: list[float | int], p: float) -> float | int | None:
    if not values:
        return None
    return sorted(values)[int((len(values) - 1) * p)]


def _response_summary(method: str, body: bytes) -> dict[str, Any]:
    if method == "POST":
        return _body_summary(body)
    return {"non_generation_body_bytes": len(body)}


def _usage_from_summary(summary: dict[str, Any]) -> dict[str, int] | None:
    usage = summary.get("usage")
    if not isinstance(usage, dict):
        return None
    return usage


def _run_configuration(
    config: dict[str, Any],
    *,
    qa_by_id: dict[str, dict[str, Any]],
    store: ChunkIndexStore,
    output_dir: Path,
    call_state: dict[str, Any],
) -> dict[str, Any]:
    model = config["model"]
    fallback_model = GEMMA if model == PRIMARY else PRIMARY
    client = OpenRouterClient(
        model=model,
        fallback_model=fallback_model,
        free_catalog=I2_FREE_MODEL_CATALOG,
        max_retries=1,
        reasoning=config["reasoning"],
    )
    router = ProviderRouter(provider="openrouter", mode="development", openrouter_client=client)
    generator = AnswerGenerator(
        context_builder=ContextBuilder(store, retriever=HybridRetriever(store)),
        guardrails=GuardrailEngine(),
        provider_router=router,
        config=AnswerGeneratorConfig(top_k=10, max_output_tokens=config["max_tokens"]),
    )
    raw_calls: list[dict[str, Any]] = []
    original_urlopen = __import__("rag.generation.openrouter_client", fromlist=["request"]).request.urlopen

    def recording_urlopen(raw_request: Any, timeout: float) -> Any:
        started = time.perf_counter()
        contract = _safe_request_contract(raw_request)
        question_id = call_state.get("question_id")
        try:
            response = original_urlopen(raw_request, timeout=timeout)
            body = response.read()
            headers = {str(key): str(value) for key, value in response.headers.items()}
            raw_calls.append(
                {
                    "question_id": question_id,
                    "method": contract["method"],
                    "request_contract": contract,
                    "http_status": response.status,
                    "response_headers": headers,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                    "response": _response_summary(contract["method"], body),
                }
            )
            if contract["method"] == "POST":
                call_state["generation_requests_used"] += 1
            return _ReplayResponse(response.status, headers, body)
        except error.HTTPError as exc:
            body = exc.read()
            headers = {str(key): str(value) for key, value in exc.headers.items()}
            raw_calls.append(
                {
                    "question_id": question_id,
                    "method": contract["method"],
                    "request_contract": contract,
                    "http_status": exc.code,
                    "response_headers": headers,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                    "response": _response_summary(contract["method"], body),
                }
            )
            if contract["method"] == "POST":
                call_state["generation_requests_used"] += 1
            raise error.HTTPError(exc.url, exc.code, exc.msg, exc.hdrs, BytesIO(body)) from exc

    module = __import__("rag.generation.openrouter_client", fromlist=["request"])
    module.request.urlopen = recording_urlopen
    answers: list[dict[str, Any]] = []
    try:
        for question_id, category, difficulty in FROZEN_PROBE:
            call_state["question_id"] = question_id
            row = qa_by_id[question_id]
            started = time.perf_counter()
            context = generator.context_builder.build(row["question"], top_k=10)
            response, provider_meta = generator.answer_with_meta_from_context(
                row["question"], context, debug=True
            )
            answers.append(
                {
                    "question_id": question_id,
                    "category": category,
                    "difficulty": difficulty,
                    "question": row["question"],
                    "answer": response.get("answer", ""),
                    "refusal": response.get("refusal"),
                    "retrieval_debug": response.get("retrieval_debug", {}),
                    "provider_meta": provider_meta,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                }
            )
            post_count = sum(1 for call in raw_calls if call["method"] == "POST")
            total_count = call_state["generation_requests_used"]
            print(f"config={config['id']} question={question_id} generation_requests={post_count} total_generation_requests={total_count}", flush=True)
            if total_count >= call_state["generation_budget_limit"]:
                raise RuntimeError("Gate 16 G3 hard stop reached before a 61st generation POST.")
    finally:
        module.request.urlopen = original_urlopen

    posts = [call for call in raw_calls if call["method"] == "POST"]
    finish = Counter(str(call["response"].get("finish_reason")) for call in posts)
    statuses = Counter(str(call["http_status"]) for call in posts)
    errors = Counter()
    served_models = Counter()
    completion: list[int] = []
    reasoning: list[int] = []
    for call in posts:
        summary = call["response"]
        if summary.get("served_model"):
            served_models[summary["served_model"]] += 1
        err = summary.get("error") if isinstance(summary.get("error"), dict) else {}
        code = err.get("code")
        if call["http_status"] == 429 or code == 429 or any(
            str(key).casefold().startswith("x-ratelimit-") or str(key).casefold() == "retry-after"
            for key in call["response_headers"]
        ):
            errors["rate_limited"] += 1
        elif code is not None or call["http_status"] >= 500 or summary.get("finish_reason") == "length":
            errors["provider_error"] += 1
        else:
            errors["success"] += 1
        usage = _usage_from_summary(summary)
        if isinstance(usage, dict):
            if isinstance(usage.get("output_tokens_actual"), int):
                completion.append(usage["output_tokens_actual"])
            if isinstance(usage.get("reasoning_tokens_actual"), int):
                reasoning.append(usage["reasoning_tokens_actual"])
    first_attempts = {}
    for call in posts:
        first_attempts.setdefault(call["question_id"], call)
    schema_valid = 0
    for call in first_attempts.values():
        body = call["response"].get("body")
        choices = body.get("choices") if isinstance(body, dict) else None
        content = choices[0].get("message", {}).get("content") if isinstance(choices, list) and choices else None
        if isinstance(content, str):
            try:
                if isinstance(json.loads(content), dict):
                    schema_valid += 1
            except json.JSONDecodeError:
                pass
    latencies = [row["latency_ms"] for row in answers]
    payload = {
        "configuration": config,
        "fallback_model": fallback_model,
        "question_ids": [question_id for question_id, _, _ in FROZEN_PROBE],
        "request_count": len(posts),
        "raw_call_count_including_catalog_gets": len(raw_calls),
        "finish_reason": dict(finish),
        "http_status": dict(statuses),
        "error_taxonomy": dict(errors),
        "first_attempt_schema": {"valid": schema_valid, "attempted": len(first_attempts)},
        "latency_ms": {"p50": _percentile(latencies, 0.50), "p95": _percentile(latencies, 0.95)},
        "completion_tokens": {"p50": _percentile(completion, 0.50), "p95": _percentile(completion, 0.95), "max": max(completion) if completion else None, "n": len(completion), "missing": len(posts) - len(completion)},
        "reasoning_tokens": {"p50": _percentile(reasoning, 0.50), "p95": _percentile(reasoning, 0.95), "max": max(reasoning) if reasoning else None, "n": len(reasoning), "missing": len(posts) - len(reasoning)},
        "served_models": dict(served_models),
        "client_status": client.status(),
        "answers": answers,
        "raw_calls": raw_calls,
    }
    config_path = output_dir / f"{config['id']}.json"
    config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa", default="evals/datasets/golden_qa.jsonl")
    parser.add_argument("--chunks", default="data/chunks/chunks_500.jsonl")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--already-consumed", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv(dotenv_path=Path(".env"), override=False)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    qa_by_id = {
        row["question_id"]: row
        for row in (json.loads(line) for line in Path(args.qa).read_text(encoding="utf-8").splitlines() if line.strip())
    }
    missing = [question_id for question_id, _, _ in FROZEN_PROBE if question_id not in qa_by_id]
    if missing:
        raise SystemExit(f"Missing frozen probe IDs: {missing}")
    store = ChunkIndexStore.from_jsonl(args.chunks)
    call_state: dict[str, Any] = {
        "question_id": None,
        "generation_requests_used": args.already_consumed,
        "generation_budget_limit": 60,
    }
    configs = [
        {"id": "cfg1", "model": PRIMARY, "reasoning": None, "max_tokens": 2048},
        {"id": "cfg2", "model": PRIMARY, "reasoning": None, "max_tokens": 8192},
        {"id": "cfg3", "model": PRIMARY, "reasoning": {"effort": "none"}, "max_tokens": 8192},
        {"id": "cfg4", "model": GEMMA, "reasoning": None, "max_tokens": 8192},
    ]
    for config in configs:
        os.environ.pop("OPENROUTER_REASONING_EFFORT", None)
        os.environ.pop("OPENROUTER_REASONING_MAX_TOKENS", None)
        os.environ.pop("OPENROUTER_REASONING_EXCLUDE", None)
        os.environ.pop("OPENROUTER_REASONING_ENABLED", None)
        # The explicit constructor value is the registered probe configuration.
        _run_configuration(config, qa_by_id=qa_by_id, store=store, output_dir=output_dir, call_state=call_state)
    print(json.dumps({"output_dir": str(output_dir), "configurations": ["cfg1", "cfg2", "cfg3", "cfg4"]}))


if __name__ == "__main__":
    main()
