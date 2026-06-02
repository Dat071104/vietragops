# Phase 04 Audit

## Audit scope

Validate baseline retrieval outputs, reproducibility, benchmark provenance, and secret hygiene before Phase 5.

## Required outputs

- Present: `rag/retrieval/base.py`
- Present: `rag/retrieval/index_store.py`
- Present: `rag/retrieval/bm25_retriever.py`
- Present: `rag/retrieval/dense_retriever.py`
- Present: `rag/retrieval/hybrid_retriever.py`
- Present: `evals/datasets/dev_qa.jsonl`
- Present: `evals/metrics/retrieval_metrics.py`
- Present: `evals/experiments/run_retrieval_eval.py`
- Present: `reports/retrieval_baseline.md`
- Present: `tests/test_retrieval_metrics.py`
- Present: `tests/test_retriever.py`

## Schema and reproducibility checks

- `dev_qa.jsonl` rows: 20
- Required QA fields present on all rows: yes
- Retrieval outputs written to `dist/experiments/retrieval/`: yes
- Benchmark table values copied from experiment JSON artifacts only: yes

## Verification commands

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

## Results

- Compile check: passed
- Tests: `12 passed`
- Chunk validation: passed for all three chunk configs
- BM25 eval: passed
- Dense eval: passed with deterministic offline fallback backend
- Hybrid eval: passed
- Secret scans: no matches in repository files

## Reviewer notes

- No fake metrics were introduced; all reported values are backed by experiment JSON in `dist/experiments/retrieval/`.
- Dense retrieval currently falls back to the local sparse semantic backend because no cached sentence-transformer model was available.
- Two answerable dev questions remain missed across all baselines, which is acceptable for Phase 4 and becomes a concrete target for Phase 5 reranking and source-priority work.

## Sign-off

- Reviewer: pass with documented retrieval gaps
- Security/Release Auditor: pass
- Phase status: `ready_for_next_phase`
