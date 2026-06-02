"""Run the Phase 7 pipeline comparison matrix."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from evals.experiments.defaults import DEFAULT_GENERATION_QA_PATH
from evals.experiments.run_generation_eval import GenerationEvalConfig, run_generation_eval


CHUNK_OPTIONS = {
    "300": "data/chunks/chunks_300.jsonl",
    "500": "data/chunks/chunks_500.jsonl",
    "800": "data/chunks/chunks_800.jsonl",
}

QA_PATH = DEFAULT_GENERATION_QA_PATH


def main() -> None:
    experiments = []
    cache = {}
    for chunk_size, chunk_path in CHUNK_OPTIONS.items():
        for retriever in ["bm25", "dense", "hybrid"]:
            for reranker in [False, True]:
                for top_k in [3, 5, 8]:
                    for guardrails in [False, True]:
                        for source_priority in [False, True]:
                            config = GenerationEvalConfig(
                                chunks_path=chunk_path,
                                qa_path=QA_PATH,
                                retriever=retriever,
                                top_k=top_k,
                                reranker=reranker,
                                guardrails=guardrails,
                                source_priority=source_priority,
                            )
                            effective_key = (
                                chunk_path,
                                retriever,
                                top_k,
                                guardrails,
                                reranker if retriever == "hybrid" else False,
                                source_priority if retriever == "hybrid" else False,
                            )
                            if effective_key not in cache:
                                cache[effective_key] = run_generation_eval(config)
                            payload = cache[effective_key]
                            experiments.append(
                                {
                                    "config": payload["config"],
                                    "metrics": payload["metrics"],
                                    "records": payload["records"],
                                }
                            )

    experiment_id = f"compare_pipelines_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output = {
        "experiment_id": experiment_id,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "qa_path": QA_PATH,
        "experiments": experiments,
    }
    output_path = Path("dist") / "experiments" / "pipelines" / f"{experiment_id}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"experiment_id": experiment_id, "output_path": str(output_path), "experiment_count": len(experiments)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
