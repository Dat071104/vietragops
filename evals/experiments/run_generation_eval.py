"""Run generation evaluation for one pipeline configuration."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
import time
from typing import Any

from evals.experiments.defaults import DEFAULT_CHUNKS_PATH, DEFAULT_GENERATION_QA_PATH
from evals.experiments.run_retrieval_eval import load_jsonl
from evals.metrics.abstention_metrics import aggregate_abstention_metrics
from evals.metrics.generation_metrics import aggregate_generation_metrics
from evals.metrics.retrieval_metrics import aggregate_retrieval_metrics
from evals.metrics.system_metrics import error_rate, latency_summary
from rag.generation import AnswerGenerator, ContextBuilder, GuardrailEngine
from rag.retrieval import AdvancedHybridRetriever, BM25Retriever, ChunkIndexStore, DenseRetriever, HybridRetriever
from rag.retrieval.advanced_hybrid_retriever import AdvancedHybridConfig


@dataclass(frozen=True)
class GenerationEvalConfig:
    chunks_path: str
    qa_path: str
    retriever: str = "hybrid"
    top_k: int = 5
    reranker: bool = False
    guardrails: bool = True
    source_priority: bool = False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run generation evaluation.")
    parser.add_argument("--chunks", default=DEFAULT_CHUNKS_PATH)
    parser.add_argument("--qa", default=DEFAULT_GENERATION_QA_PATH)
    parser.add_argument("--retriever", choices=["bm25", "dense", "hybrid"], default="hybrid")
    parser.add_argument("--top_k", type=int, default=5)
    parser.add_argument("--reranker", action="store_true")
    parser.add_argument("--source_priority", action="store_true")
    parser.add_argument(
        "--guardrails",
        action=argparse.BooleanOptionalAction,
        default=GenerationEvalConfig.guardrails,
    )
    parser.add_argument("--output")
    return parser.parse_args(argv)


def build_retriever(config: GenerationEvalConfig, store: ChunkIndexStore):
    if config.retriever == "bm25":
        return BM25Retriever(store)
    if config.retriever == "dense":
        return DenseRetriever(store)
    if config.reranker or config.source_priority:
        return AdvancedHybridRetriever(
            store,
            config=AdvancedHybridConfig(
                enable_reranker=config.reranker,
                enable_source_priority=config.source_priority,
                enable_recency=config.source_priority,
            ),
        )
    return HybridRetriever(store)


def build_guardrails(enabled: bool) -> GuardrailEngine:
    if enabled:
        return GuardrailEngine()
    return GuardrailEngine(min_support_score=0.0, min_lexical_score=0.0, min_bigram_overlap=0.0)


def run_generation_eval(config: GenerationEvalConfig) -> dict[str, Any]:
    store = ChunkIndexStore.from_jsonl(config.chunks_path)
    qa_rows = load_jsonl(config.qa_path)
    retriever = build_retriever(config, store)
    generator = AnswerGenerator(
        context_builder=ContextBuilder(store, retriever=retriever),
        guardrails=build_guardrails(config.guardrails),
    )
    records = []
    retrieval_predictions = []

    for row in qa_rows:
        started = time.perf_counter()
        response = generator.answer(row["question"], debug=True, top_k=config.top_k)
        latency_ms = (time.perf_counter() - started) * 1000
        citations_valid = response["refusal"] or all(
            citation.get("chunk_id") in response["retrieval_debug"].get("chunk_ids", [])
            for citation in response.get("citations", [])
        )
        retrieved_chunk_ids = response["retrieval_debug"].get("chunk_ids", [])
        record = {
            "question_id": row["question_id"],
            "question": row["question"],
            "expected_answer": row["expected_answer"],
            "answer": response["answer"],
            "citations_valid": citations_valid,
            "refusal": response["refusal"],
            "refusal_reason": response["refusal_reason"],
            "is_answerable": row["is_answerable"],
            "category": row["category"],
            "latency_ms": round(latency_ms, 2),
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "relevant_chunk_ids": row["relevant_chunk_ids"],
            "failure_label": infer_failure_label(row, response, citations_valid, retrieved_chunk_ids),
            "error": False,
        }
        records.append(record)
        retrieval_predictions.append(
            {
                "question_id": row["question_id"],
                "predicted_chunk_ids": retrieved_chunk_ids,
                "latency_ms": round(latency_ms, 2),
            }
        )

    retrieval = aggregate_retrieval_metrics(qa_rows, retrieval_predictions)
    generation = aggregate_generation_metrics(records)
    abstention = aggregate_abstention_metrics(records)
    system = latency_summary([row["latency_ms"] for row in records])
    system["error_rate"] = error_rate(records)
    return {
        "experiment_id": f"generation_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "config": asdict(config),
        "retriever_backend": getattr(retriever, "backend_name", "unknown"),
        "metrics": {
            **retrieval["metrics"],
            **generation,
            **abstention,
            **system,
        },
        "records": records,
    }


def infer_failure_label(row: dict[str, Any], response: dict[str, Any], citations_valid: bool, retrieved_chunk_ids: list[str]) -> str | None:
    if not row["is_answerable"] and not response["refusal"]:
        return "generation_hallucination"
    if row["is_answerable"] and not set(row["relevant_chunk_ids"]).intersection(retrieved_chunk_ids):
        return "retrieval_miss"
    if row["is_answerable"] and not citations_valid:
        return "citation_mismatch"
    if row["category"] == "source_conflict":
        return "stale_source"
    if len(row["relevant_chunk_ids"]) > 1 and not response["refusal"]:
        return "ambiguous_query"
    return None


def main() -> None:
    args = parse_args()
    config = GenerationEvalConfig(
        chunks_path=args.chunks,
        qa_path=args.qa,
        retriever=args.retriever,
        top_k=args.top_k,
        reranker=args.reranker,
        guardrails=args.guardrails,
        source_priority=args.source_priority,
    )
    payload = run_generation_eval(config)
    output_path = Path(args.output) if args.output else Path("dist") / "experiments" / "generation" / f"{payload['experiment_id']}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"experiment_id": payload["experiment_id"], "output_path": str(output_path), "metrics": payload["metrics"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
