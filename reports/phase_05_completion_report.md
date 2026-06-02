# Phase 05 Completion Report

## Summary

Phase 5 added reciprocal-rank fusion utilities, a reranker abstraction with an offline lexical fallback, metadata-aware source priority and recency scoring, optional Qdrant integration, and a reproducible ablation runner for advanced retrieval experiments.

## Deliverables completed

- `rag/retrieval/rrf.py`
- `rag/retrieval/reranker.py`
- `rag/retrieval/source_priority.py`
- `rag/retrieval/qdrant_indexer.py`
- `rag/retrieval/advanced_hybrid_retriever.py`
- `evals/experiments/compare_retrievers.py`
- `reports/advanced_retrieval_benchmark.md`
- `reports/phase_05_plan.md`
- `reports/phase_05_audit.md`
- `reports/phase_05_completion_report.md`
- `tests/test_reranker.py`
- `tests/test_source_priority.py`
- `tests/test_rrf.py`

## Files created or modified

- `ALWAYS_READ/02_CURRENT_PHASE.md`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `project_context_cards/PHASE_05_ADVANCED_RETRIEVAL.md`
- `reports/phase_05_plan.md`
- `reports/advanced_retrieval_benchmark.md`
- `reports/phase_05_audit.md`
- `reports/phase_05_completion_report.md`
- `rag/retrieval/__init__.py`
- `rag/retrieval/dense_retriever.py`
- `rag/retrieval/hybrid_retriever.py`
- `rag/retrieval/rrf.py`
- `rag/retrieval/reranker.py`
- `rag/retrieval/source_priority.py`
- `rag/retrieval/qdrant_indexer.py`
- `rag/retrieval/advanced_hybrid_retriever.py`
- `evals/experiments/compare_retrievers.py`
- `tests/test_reranker.py`
- `tests/test_source_priority.py`
- `tests/test_rrf.py`

## Commands run

```bash
python -m compileall rag evals tests
pytest -q
python -m evals.experiments.compare_retrievers --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --top_k 5
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

## Test results

- `python -m compileall rag evals tests`: passed
- `pytest -q`: `16 passed`
- `python -m evals.experiments.compare_retrievers --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --top_k 5`: passed

## Metrics produced

- Best config remained `hybrid`
- `hybrid`: `Recall@3 0.8333`, `Recall@5 0.8889`, `MRR 0.5972`, `Latency 18.11 ms`
- `hybrid + reranker`: `Recall@3 0.7222`, `Recall@5 0.7778`, `MRR 0.6157`, `Latency 33.78 ms`
- `hybrid + reranker + source priority`: `Recall@3 0.7222`, `Recall@5 0.7778`, `MRR 0.6157`, `Latency 33.03 ms`

## Bugs found and fixed

- Symptom: the first lexical reranker version over-trusted broad regulation chunks and dropped high-value baseline hits out of the top 5.
- Root cause: rerank scores were used too independently from the baseline hybrid signal.
- Fix: anchored the rerank score to normalized hybrid scores before applying the final advanced scoring formula.
- Files changed: `rag/retrieval/advanced_hybrid_retriever.py`
- Verification: rerun `pytest -q` and `python -m evals.experiments.compare_retrievers --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --top_k 5`
- Regression risk: medium, because the lexical fallback still helps some procedural guide questions while remaining weaker than the hybrid baseline on regulation-heavy queries.

## Remaining risks

- The offline lexical reranker is still not strong enough to replace the baseline hybrid as the default retriever.
- Qdrant integration is unexercised locally because no Qdrant client or running service was required for this phase.
- The current dev set is still small, so reranker behavior should be revalidated against the larger Phase 7 benchmark set.

## Manual checks recommended

- Review the improved questions `dev_q006`, `dev_q007`, and `dev_q008`.
- Review the worsened questions `dev_q013`, `dev_q014`, and `dev_q018`.
- Keep the reranker abstraction, but gate its default use on stronger eval evidence in later phases.

## Readiness for next phase

- Status: `ready_for_next_phase`
- Next phase: `Phase 6 — Generation + Citation Verifier + Refusal Guardrails`
