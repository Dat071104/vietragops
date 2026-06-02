"""Run retrieval ablations across baseline and advanced retrievers."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path

from evals.experiments.defaults import DEFAULT_CHUNKS_PATH, DEFAULT_RETRIEVAL_QA_PATH
from evals.experiments.run_retrieval_eval import load_jsonl
from evals.metrics.retrieval_metrics import aggregate_retrieval_metrics
from rag.retrieval import AdvancedHybridRetriever, BM25Retriever, ChunkIndexStore, DenseRetriever, HybridRetriever
from rag.retrieval.advanced_hybrid_retriever import AdvancedHybridConfig


CONFIGS = {
    "bm25_only": lambda store: BM25Retriever(store),
    "dense_only": lambda store: DenseRetriever(store),
    "hybrid": lambda store: HybridRetriever(store),
    "hybrid_reranker": lambda store: AdvancedHybridRetriever(
        store,
        config=AdvancedHybridConfig(enable_reranker=True, enable_source_priority=False, enable_recency=False),
    ),
    "hybrid_reranker_source_priority": lambda store: AdvancedHybridRetriever(store),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare retrieval configurations.")
    parser.add_argument("--chunks", default=DEFAULT_CHUNKS_PATH)
    parser.add_argument("--qa", default=DEFAULT_RETRIEVAL_QA_PATH)
    parser.add_argument("--top_k", type=int, default=5)
    parser.add_argument("--output", help="Optional explicit output path.")
    return parser.parse_args(argv)


def run_compare(chunks_path: str, qa_path: str, top_k: int) -> dict:
    store = ChunkIndexStore.from_jsonl(chunks_path)
    qa_items = load_jsonl(qa_path)
    experiments = []

    for config_name, builder in CONFIGS.items():
        retriever = builder(store)
        predictions = []
        for qa_item in qa_items:
            import time

            started = time.perf_counter()
            results = retriever.retrieve(qa_item["question"], top_k=top_k)
            latency_ms = (time.perf_counter() - started) * 1000
            predictions.append(
                {
                    "question_id": qa_item["question_id"],
                    "latency_ms": round(latency_ms, 2),
                    "predicted_chunk_ids": [result.chunk_id for result in results],
                    "results": [result.to_dict() for result in results],
                }
            )
        aggregated = aggregate_retrieval_metrics(qa_items, predictions)
        experiments.append(
            {
                "name": config_name,
                "retriever": retriever.metadata(),
                "metrics": aggregated["metrics"],
                "per_query": aggregated["per_query"],
                "predictions": predictions,
            }
        )

    experiment_id = f"compare_retrievers_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    best = max(experiments, key=lambda item: (item["metrics"]["recall_at_3"], item["metrics"]["mrr"]))
    return {
        "experiment_id": experiment_id,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "chunks_path": chunks_path,
        "qa_path": qa_path,
        "top_k": top_k,
        "experiments": experiments,
        "best_config": best["name"],
    }


def main() -> None:
    args = parse_args()
    payload = run_compare(args.chunks, args.qa, args.top_k)
    output_path = Path(args.output) if args.output else Path("dist") / "experiments" / "retrieval" / f"{payload['experiment_id']}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "experiment_id": payload["experiment_id"],
        "best_config": payload["best_config"],
        "output_path": str(output_path),
        "metrics": {item["name"]: item["metrics"] for item in payload["experiments"]},
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
