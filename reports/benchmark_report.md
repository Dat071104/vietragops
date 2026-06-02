# Benchmark Report

## Evaluation mode

- Source experiment: `dist/experiments/pipelines/compare_pipelines_20260602_004911.json`
- Mode: deterministic or mock generation evaluation
- Groq-backed generation: not exercised in this benchmark because `GROQ_API_KEY` was not present locally

## Dataset summary

- `golden_qa.jsonl`: 120 rows
- `dev_qa.jsonl`: 20 rows
- `validation_qa.jsonl`: 6 rows
- `test_qa.jsonl`: 20 rows
- Reason for small validation split: keep the full 216-config matrix reproducible within local runtime limits while preserving a larger golden pool for later expansion

## Best config from the full matrix

- Chunks: `chunks_500.jsonl`
- Retriever: `bm25`
- `top_k`: `3`
- Reranker: `off`
- Guardrails: `off`
- Source priority: `off`

## Best-config metrics

| Metric | Value |
| --- | ---: |
| Recall@3 | 0.7500 |
| Recall@5 | 0.7500 |
| MRR | 0.4583 |
| Precision@5 | 0.1500 |
| Token F1 | 0.2807 |
| Citation support rate | 1.0000 |
| Answer correctness rate | 0.2500 |
| Refusal accuracy | 1.0000 |
| Unsupported answer rate | 0.0000 |
| Latency p50 (ms) | 226.17 |
| Latency p95 (ms) | 236.48 |

## Reference single-config generation run

- Source experiment: `dist/experiments/generation/generation_eval_20260602_004248.json`
- Config: `chunks_500 + hybrid + top_k 5 + guardrails on`

| Metric | Value |
| --- | ---: |
| Recall@5 | 0.7500 |
| Token F1 | 0.2047 |
| Citation support rate | 1.0000 |
| Refusal accuracy | 1.0000 |
| Latency p50 (ms) | 250.27 |
| Latency p95 (ms) | 273.33 |

## Interpretation

- The current benchmark favors compact lexical retrieval under deterministic answer generation.
- Citation support is strong because the fallback answerer is strictly extractive and citation-bound.
- Token-level answer quality remains modest, which is consistent with the current deterministic fallback being grounded but verbose and only lightly synthesized.
- These numbers should be read as a reproducible offline benchmark, not as a final LLM-quality benchmark.

## Operational note

- The best matrix config above is useful as a reproducible benchmark result, but the project keeps `chunks_500 + hybrid + top_k 5 + guardrails on` as the more demo-friendly runtime default because it offers stronger retrieval grounding and safer interactive behavior.
