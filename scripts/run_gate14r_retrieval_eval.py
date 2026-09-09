"""Retrieval-only Gate 14-R product-surface evaluation.

This runner never constructs an answer generator or provider client.  It runs
the same ContextBuilder candidate depth and selection path used by `/ask`.
"""

from __future__ import annotations

import argparse
import json
from math import sqrt
from pathlib import Path
import statistics
import time
from typing import Any

from evals.experiments.run_retrieval_eval import load_jsonl
from rag.generation.context_builder import ContextBuilder
from rag.retrieval import AdvancedHybridRetriever, ChunkIndexStore, HybridRetriever
from rag.retrieval.advanced_hybrid_retriever import AdvancedHybridConfig
from rag.retrieval.dense_retriever import DenseConfig
from rag.retrieval.hybrid_retriever import HybridConfig


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 14-R retrieval-only product evaluation.")
    parser.add_argument("--chunks", required=True)
    parser.add_argument("--qa", required=True)
    parser.add_argument("--top-k", type=int, required=True)
    parser.add_argument("--model-name", default="sparse")
    parser.add_argument("--artifact-dir", default=None)
    parser.add_argument("--use-reranker", action="store_true")
    parser.add_argument("--question-start", type=int, default=0)
    parser.add_argument("--question-limit", type=int, default=None)
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def wilson(successes: int, total: int, z: float = 1.96) -> dict[str, Any]:
    if total <= 0:
        return {"successes": successes, "total": total, "rate": None, "low": None, "high": None}
    p = successes / total
    denominator = 1 + (z * z / total)
    centre = (p + (z * z / (2 * total))) / denominator
    margin = z * sqrt((p * (1 - p) / total) + (z * z / (4 * total * total))) / denominator
    return {
        "successes": successes,
        "total": total,
        "rate": round(p, 6),
        "low": round(max(0.0, centre - margin), 6),
        "high": round(min(1.0, centre + margin), 6),
        "method": "95% Wilson",
    }


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * percentile))))
    return round(ordered[index], 3)


def _dense_component(retriever: Any) -> Any | None:
    if hasattr(retriever, "dense"):
        return retriever.dense
    if hasattr(retriever, "hybrid") and hasattr(retriever.hybrid, "dense"):
        return retriever.hybrid.dense
    return None


def build_retriever(store: ChunkIndexStore, args: argparse.Namespace) -> Any:
    if args.model_name == "sparse":
        return HybridRetriever(store)
    dense_config = DenseConfig(
        model_name=args.model_name,
        onnx_artifact_dir=args.artifact_dir,
    )
    if args.use_reranker:
        return AdvancedHybridRetriever(
            store,
            config=AdvancedHybridConfig(
                enable_reranker=True,
                enable_source_priority=False,
                enable_recency=False,
                dense_config=dense_config,
            ),
        )
    return HybridRetriever(store, config=HybridConfig(dense_config=dense_config))


def _metric_set(rows: list[dict[str, Any]], per_query: list[dict[str, Any]], k: int) -> dict[str, Any]:
    answerable = [row for row in rows if row.get("is_answerable", True)]
    answerable_ids = {row["question_id"] for row in answerable}
    scored = [item for item in per_query if item["question_id"] in answerable_ids]
    recall_values = [item["recall"] for item in scored]
    precision_values = [item["precision"] for item in scored]
    reciprocal_ranks = [item["reciprocal_rank"] for item in scored]
    question_hits = sum(1 for item in scored if item["question_hit"])
    relevant_hits = sum(item["relevant_hits"] for item in scored)
    relevant_total = sum(len(item["relevant_chunk_ids"]) for item in scored)
    latency = [item["latency_ms"] for item in per_query]
    encode_latency = [item["query_encode_ms"] for item in per_query if item["query_encode_ms"] is not None]
    return {
        "answerable_count": len(answerable),
        "k": k,
        "macro_recall_at_k": round(statistics.fmean(recall_values), 6) if recall_values else 0.0,
        "macro_precision_at_k": round(statistics.fmean(precision_values), 6) if precision_values else 0.0,
        "mrr": round(statistics.fmean(reciprocal_ranks), 6) if reciprocal_ranks else 0.0,
        "question_hit_count": question_hits,
        "answerable_ceiling": wilson(question_hits, len(answerable)),
        "micro_recall": wilson(relevant_hits, relevant_total),
        "micro_precision": wilson(relevant_hits, len(answerable) * k),
        "latency_ms": {
            "mean": round(statistics.fmean(latency), 3) if latency else None,
            "p50": _percentile(latency, 0.50),
            "p95": _percentile(latency, 0.95),
        },
        "query_encode_ms": {
            "mean": round(statistics.fmean(encode_latency), 3) if encode_latency else None,
            "p50": _percentile(encode_latency, 0.50),
            "p95": _percentile(encode_latency, 0.95),
            "observations": len(encode_latency),
        },
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    store = ChunkIndexStore.from_jsonl(args.chunks)
    all_rows = load_jsonl(args.qa)
    end = None if args.question_limit is None else args.question_start + args.question_limit
    rows = all_rows[args.question_start:end]
    started_init = time.perf_counter()
    retriever = build_retriever(store, args)
    initialization_seconds = time.perf_counter() - started_init
    context_builder = ContextBuilder(store, retriever=retriever)
    dense = _dense_component(retriever)
    per_query: list[dict[str, Any]] = []
    run_started = time.perf_counter()
    for row in rows:
        started = time.perf_counter()
        bundle = context_builder.build(row["question"], top_k=args.top_k)
        elapsed_ms = (time.perf_counter() - started) * 1000
        selected_ids = [chunk["chunk_id"] for chunk in bundle.chunks]
        relevant = set(row.get("relevant_chunk_ids", []))
        hits = len(relevant.intersection(selected_ids)) if row.get("is_answerable", True) else 0
        relevant_count = len(relevant)
        reciprocal_rank = 0.0
        for rank, chunk_id in enumerate(selected_ids, start=1):
            if chunk_id in relevant:
                reciprocal_rank = 1.0 / rank
                break
        per_query.append(
            {
                "question_id": row["question_id"],
                "category": row.get("category"),
                "difficulty": row.get("difficulty"),
                "is_answerable": row.get("is_answerable", True),
                "selected_chunk_ids": selected_ids,
                "relevant_chunk_ids": list(row.get("relevant_chunk_ids", [])),
                "relevant_hits": hits,
                "question_hit": bool(hits),
                "recall": (hits / relevant_count) if relevant_count else 0.0,
                "precision": hits / args.top_k,
                "reciprocal_rank": reciprocal_rank,
                "latency_ms": round(elapsed_ms, 3),
                "query_encode_ms": (
                    round(float(getattr(getattr(dense, "_backend", None), "last_query_encode_ms", 0.0)), 3)
                    if dense is not None and hasattr(getattr(dense, "_backend", None), "last_query_encode_ms")
                    else None
                ),
            }
        )

    curriculum = [item for item in per_query if item.get("category") == "curriculum_structure"]
    curriculum_rows = [row for row in rows if row.get("category") == "curriculum_structure"]
    metrics = _metric_set(rows, per_query, args.top_k)
    metrics["curriculum_structure"] = _metric_set(curriculum_rows, curriculum, args.top_k)
    return {
        "gate": "14-R",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "chunks_path": args.chunks,
        "qa_path": args.qa,
        "question_start": args.question_start,
        "question_limit": args.question_limit,
        "total_question_count": len(all_rows),
        "model_name": args.model_name,
        "artifact_dir": args.artifact_dir,
        "use_reranker": args.use_reranker,
        "top_k": args.top_k,
        "candidate_depth": 50,
        "initialization_seconds": round(initialization_seconds, 3),
        "wall_clock_seconds": round(time.perf_counter() - run_started, 3),
        "retriever_status": retriever.status(),
        "metrics": metrics,
        "per_query": per_query,
    }


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    payload = run(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "metrics": payload["metrics"], "status": payload["retriever_status"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
