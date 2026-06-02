# Phase 05 Plan

## Objective

Upgrade the baseline retriever into a more production-like advanced hybrid stack with reranking, source-priority scoring, recency-aware scoring, optional Qdrant integration, and an ablation benchmark that explains the best retrieval configuration for Phase 6.

## Inputs found

- `data/chunks/chunks_500.jsonl`
- `data/manifests/documents_manifest.csv`
- `evals/datasets/dev_qa.jsonl`
- `dist/experiments/retrieval/retrieval_bm25_chunks_500_20260601_202848.json`
- `dist/experiments/retrieval/retrieval_dense_chunks_500_20260601_202909.json`
- `dist/experiments/retrieval/retrieval_hybrid_chunks_500_20260601_202910.json`
- `reports/retrieval_baseline.md`

## Files to create or modify

- `ALWAYS_READ/02_CURRENT_PHASE.md`
- `rag/retrieval/rrf.py`
- `rag/retrieval/reranker.py`
- `rag/retrieval/source_priority.py`
- `rag/retrieval/qdrant_indexer.py`
- `rag/retrieval/advanced_hybrid_retriever.py`
- `rag/retrieval/hybrid_retriever.py`
- `rag/retrieval/__init__.py`
- `evals/experiments/compare_retrievers.py`
- `reports/advanced_retrieval_benchmark.md`
- `reports/phase_05_audit.md`
- `reports/phase_05_completion_report.md`
- `tests/test_reranker.py`
- `tests/test_source_priority.py`
- `tests/test_rrf.py`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `project_context_cards/PHASE_05_ADVANCED_RETRIEVAL.md`

## Implementation plan

1. Add generic reciprocal-rank fusion utilities and refactor hybrid retrieval to use them.
2. Add a reranker abstraction with a deterministic lexical fallback and optional BGE local-model support.
3. Add source-priority and recency scoring helpers backed by chunk plus manifest metadata.
4. Add the advanced hybrid retriever that combines rerank, hybrid, authority, and recency scores using the required weighted formula.
5. Add optional Qdrant indexer helpers that fail gracefully when Qdrant is unavailable.
6. Build an ablation runner for BM25, dense, hybrid, hybrid plus reranker, and hybrid plus reranker plus source priority.
7. Benchmark the ablations, document gains and regressions, and recommend the best context-builder input for Phase 6.

## Test plan

- `python -m compileall rag evals tests`
- `pytest -q`
- `python -m evals.experiments.compare_retrievers --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --top_k 5`

## Audit plan

- Verify advanced retrieval outputs exist and import cleanly.
- Verify the final score formula matches the requested weights.
- Verify Qdrant support is optional and does not break local offline runs.
- Verify the benchmark report only contains script-produced numbers.
- Run secret scans before phase completion.

## Expected commands

```bash
python -m compileall rag evals tests
pytest -q
python -m evals.experiments.compare_retrievers --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --top_k 5
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\\s*=\\s*gsk_" .
```

## Risk list

- Reranking may improve the known misses but hurt already-strong BM25 answers if the lexical fallback is too aggressive.
- Recency signals inferred from mixed metadata and title years may be noisy.
- Qdrant package availability may differ across machines, so the integration must stay optional and well-isolated.

## Manual checks recommended

- Inspect how the advanced reranker changes ranks for `dev_q005` and `dev_q009`.
- Verify `source_priority` boosts student-guide chunks only modestly when relevance is already close.
- Confirm the best ablation remains explainable for Phase 6 context construction.
