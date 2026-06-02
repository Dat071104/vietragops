# Phase 04 Completion Report

## Summary

Phase 4 added a full baseline retrieval stack with offline BM25, deterministic dense fallback retrieval, hybrid reciprocal-rank fusion, a grounded dev QA set, retrieval metrics, experiment runners, and baseline benchmark artifacts.

## Deliverables completed

- `rag/retrieval/__init__.py`
- `rag/retrieval/base.py`
- `rag/retrieval/index_store.py`
- `rag/retrieval/bm25_retriever.py`
- `rag/retrieval/dense_retriever.py`
- `rag/retrieval/hybrid_retriever.py`
- `evals/datasets/dev_qa.jsonl`
- `evals/metrics/retrieval_metrics.py`
- `evals/experiments/run_retrieval_eval.py`
- `reports/retrieval_baseline.md`
- `reports/phase_04_plan.md`
- `reports/phase_04_audit.md`
- `reports/phase_04_completion_report.md`
- `tests/test_retrieval_metrics.py`
- `tests/test_retriever.py`

## Files created or modified

- `ALWAYS_READ/02_CURRENT_PHASE.md`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `.gitignore`
- `project_context_cards/PHASE_04_BASELINE_RETRIEVAL.md`
- `rag/retrieval/*`
- `evals/datasets/dev_qa.jsonl`
- `evals/metrics/retrieval_metrics.py`
- `evals/experiments/run_retrieval_eval.py`
- `reports/retrieval_baseline.md`
- `reports/phase_04_plan.md`
- `reports/phase_04_audit.md`
- `reports/phase_04_completion_report.md`
- `tests/test_retrieval_metrics.py`
- `tests/test_retriever.py`

## Commands run

```bash
python -m compileall rag evals tests
pytest -q
python scripts/validate_chunks.py --chunks-dir data/chunks
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever dense --top_k 5
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

## Test results

- `python -m compileall rag evals tests`: passed
- `pytest -q`: `12 passed`
- `python scripts/validate_chunks.py --chunks-dir data/chunks`: passed
- Retrieval benchmarks: passed for BM25, dense fallback, and hybrid

## Metrics produced

- BM25: `Recall@3 0.7222`, `Recall@5 0.8889`, `MRR 0.5917`, `Precision@5 0.1889`, `Latency 2.62 ms`
- Dense fallback: `Recall@3 0.6667`, `Recall@5 0.7778`, `MRR 0.4694`, `Precision@5 0.1667`, `Latency 14.47 ms`
- Hybrid: `Recall@3 0.8333`, `Recall@5 0.8889`, `MRR 0.5972`, `Precision@5 0.1889`, `Latency 18.52 ms`

## Bugs found and fixed

- Symptom: Windows console output inspection mangled Vietnamese chunk text during manual sampling.
- Root cause: the default console encoding was not UTF-8 during ad hoc Python inspection commands.
- Fix: reran QA-mining commands with `PYTHONIOENCODING=utf-8`.
- Files changed: none
- Verification: sampled chunks displayed correctly afterward.
- Regression risk: low, because the corpus files were valid and only the shell display path was affected.

## Remaining risks

- Dense retrieval currently uses the deterministic sparse fallback because no local sentence-transformer model cache was available.
- Questions dominated by generic semester or credit-limit wording still mis-rank specialized support-guide chunks.
- The dev QA set is intentionally small and will need expansion in Phase 7 for robust benchmarking.

## Manual checks recommended

- Review the missed baseline questions `dev_q005` and `dev_q009` before locking the final hybrid strategy.
- Inspect experiment JSON artifacts in `dist/experiments/retrieval/`.
- Validate that Phase 5 reranking improves noisy regulation-vs-guide cases rather than overfitting the dev set.

## Readiness for next phase

- Status: `ready_for_next_phase`
- Next phase: `Phase 5 — Advanced Retrieval`
