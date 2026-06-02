# Advanced Retrieval Benchmark

## Setup

- Chunks: `data/chunks/chunks_500.jsonl`
- QA set: `evals/datasets/dev_qa.jsonl`
- Experiment artifact: `dist/experiments/retrieval/compare_retrievers_20260601_204043.json`
- `top_k`: 5

## Metrics table

| Config | Recall@3 | Recall@5 | Recall@10 | MRR | Precision@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| BM25 only | 0.7222 | 0.8889 | 0.8889 | 0.5917 | 0.1889 |
| Dense only | 0.6667 | 0.7778 | 0.7778 | 0.4694 | 0.1667 |
| Hybrid | 0.8333 | 0.8889 | 0.8889 | 0.5972 | 0.1889 |
| Hybrid + reranker | 0.7222 | 0.7778 | 0.7778 | 0.6157 | 0.1667 |
| Hybrid + reranker + source priority | 0.7222 | 0.7778 | 0.7778 | 0.6157 | 0.1667 |

## Latency table

| Config | Avg latency (ms) |
| --- | ---: |
| BM25 only | 2.65 |
| Dense only | 14.57 |
| Hybrid | 18.11 |
| Hybrid + reranker | 33.78 |
| Hybrid + reranker + source priority | 33.03 |

## Best config

- Best overall config for Phase 6: `hybrid`
- Reason: it preserved the strongest `Recall@3` and `Recall@5` while staying materially faster than the reranked variants.

## Cases improved

- `dev_q006`: reranking moved the academic-year guide to rank 1 for the summer-term duration question.
- `dev_q007`: reranking moved the study-plan registration guide to rank 1.
- `dev_q008`: reranking slightly improved the credit-limit question rank within the study-plan guide.

## Cases worsened

- `dev_q013`: reranking pushed down the regulation chunk describing prerequisite and co-requisite constraints.
- `dev_q014`: reranking dropped the transfer-credit cap chunk out of the top 5.
- `dev_q018`: reranking dropped the 2021 graduation-conditions chunk out of the top 5.

## Interpretation

- The lexical fallback reranker helps short procedural guide questions.
- The same reranker overweights broad token overlap on regulation-heavy questions, which reduces recall even after hybrid anchoring.
- Source priority and recency were correctly integrated, but they did not compensate for the reranker trade-off on this dev set.

## Qdrant note

- `rag/retrieval/qdrant_indexer.py` is available as an optional integration surface.
- Qdrant was not required for the local benchmark and did not block the phase.

## Recommendation for Phase 6 context builder

- Use baseline `hybrid` retrieval as the default context-builder input.
- Preserve the reranker abstraction, but keep the lexical fallback behind an optional switch until a stronger local reranker model is available.
- Keep source authority and recency scoring available for future experiments, but do not force them into the default Phase 6 retrieval path yet.
