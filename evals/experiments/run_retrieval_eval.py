"""Run baseline retrieval evaluation against a QA dataset."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import time

from evals.metrics.retrieval_metrics import aggregate_retrieval_metrics
from rag.retrieval import BM25Retriever, ChunkIndexStore, DenseRetriever, HybridRetriever


def load_jsonl(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def build_retriever(name: str, store: ChunkIndexStore):
    retrievers = {
        "bm25": BM25Retriever,
        "dense": DenseRetriever,
        "hybrid": HybridRetriever,
    }
    try:
        return retrievers[name](store)
    except KeyError as error:
        raise ValueError(f"Unsupported retriever: {name}") from error


def run_eval(chunks_path: str, qa_path: str, retriever_name: str, top_k: int) -> dict:
    store = ChunkIndexStore.from_jsonl(chunks_path)
    qa_items = load_jsonl(qa_path)
    retriever = build_retriever(retriever_name, store)
    predictions = []

    for qa_item in qa_items:
        started = time.perf_counter()
        results = retriever.retrieve(qa_item["question"], top_k=top_k)
        latency_ms = (time.perf_counter() - started) * 1000
        predictions.append(
            {
                "question_id": qa_item["question_id"],
                "question": qa_item["question"],
                "latency_ms": round(latency_ms, 2),
                "predicted_chunk_ids": [result.chunk_id for result in results],
                "results": [result.to_dict() for result in results],
            }
        )

    aggregated = aggregate_retrieval_metrics(qa_items, predictions)
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    experiment_id = f"retrieval_{retriever_name}_{Path(chunks_path).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return {
        "experiment_id": experiment_id,
        "created_at": timestamp,
        "chunks_path": chunks_path,
        "qa_path": qa_path,
        "retriever": retriever.metadata(),
        "top_k": top_k,
        "metrics": aggregated["metrics"],
        "per_query": aggregated["per_query"],
        "predictions": predictions,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run retrieval evaluation.")
    parser.add_argument("--chunks", required=True, help="Path to chunks JSONL file.")
    parser.add_argument("--qa", required=True, help="Path to QA JSONL file.")
    parser.add_argument("--retriever", required=True, choices=["bm25", "dense", "hybrid"])
    parser.add_argument("--top_k", type=int, default=5)
    parser.add_argument("--output", help="Optional explicit output path for the experiment JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run_eval(args.chunks, args.qa, args.retriever, args.top_k)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = (
            Path("dist")
            / "experiments"
            / "retrieval"
            / f"{payload['experiment_id']}.json"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "experiment_id": payload["experiment_id"],
        "output_path": str(output_path),
        "retriever": payload["retriever"],
        "top_k": payload["top_k"],
        "metrics": payload["metrics"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
