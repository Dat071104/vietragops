# Phase 04 Plan

## Objective

Implement deterministic offline baseline retrieval for the chunk corpus, create a real development QA set, and produce reproducible baseline metrics for BM25, dense, and hybrid retrieval.

## Inputs found

- `data/chunks/chunks_300.jsonl`
- `data/chunks/chunks_500.jsonl`
- `data/chunks/chunks_800.jsonl`
- `reports/chunking_report.md`
- `reports/phase_03_completion_report.md`
- `data/manifests/documents_manifest.csv`
- `data/processed/processed_docs.jsonl`

## Files to create or modify

- `ALWAYS_READ/02_CURRENT_PHASE.md`
- `.gitignore`
- `rag/retrieval/base.py`
- `rag/retrieval/index_store.py`
- `rag/retrieval/bm25_retriever.py`
- `rag/retrieval/dense_retriever.py`
- `rag/retrieval/hybrid_retriever.py`
- `rag/retrieval/__init__.py`
- `evals/datasets/dev_qa.jsonl`
- `evals/metrics/retrieval_metrics.py`
- `evals/experiments/run_retrieval_eval.py`
- `reports/retrieval_baseline.md`
- `reports/phase_04_audit.md`
- `reports/phase_04_completion_report.md`
- `tests/test_retrieval_metrics.py`
- `tests/test_retriever.py`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `project_context_cards/PHASE_04_BASELINE_RETRIEVAL.md`

## Implementation plan

1. Add retrieval abstractions and chunk index loading helpers.
2. Implement offline BM25 retrieval with deterministic tokenization.
3. Implement dense retrieval with optional `sentence-transformers` support and a hashing or TF-IDF style fallback that works offline.
4. Implement hybrid score fusion for BM25 plus dense retrieval.
5. Build a real `dev_qa.jsonl` grounded in the existing chunk corpus and document metadata.
6. Add retrieval metrics and a CLI evaluation runner for all baseline retrievers.
7. Run benchmark commands on `chunks_500.jsonl` and write the report using only measured outputs.

## Test plan

- `python -m compileall rag evals tests`
- `pytest -q`
- `python scripts/validate_chunks.py --chunks-dir data/chunks`
- `python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5`
- `python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever dense --top_k 5`
- `python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5`

## Audit plan

- Verify required retrieval files exist and import cleanly.
- Verify the dev QA schema includes all required fields.
- Verify benchmark tables use only script-generated numbers.
- Run secret scans before phase completion.
- Update the implementation log and phase card with exact commands and risks.

## Expected commands

```bash
python -m compileall rag evals tests
pytest -q
python scripts/validate_chunks.py --chunks-dir data/chunks
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever dense --top_k 5
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\\s*=\\s*gsk_" .
```

## Risk list

- Short navigation-heavy chunks may create noisy QA examples if not curated carefully.
- Dense retrieval fallback quality may lag BM25 on list-heavy or legal chunks.
- Vietnamese tokenization without extra dependencies may reduce recall on some phrasing variants.

## Manual checks recommended

- Inspect at least 10 QA entries for answerability and relevant chunk IDs.
- Review retrieval misses on curriculum or schedule questions.
- Verify no real API keys appear in any newly created docs or configs.
