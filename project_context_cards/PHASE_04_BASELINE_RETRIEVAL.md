# Phase 4 - Baseline retrieval

## Phase goal

Implement BM25, dense, and basic hybrid retrieval and evaluate on dev QA.

## Required inputs

- Current project context.
- Implementation log.
- Relevant previous phase outputs.

## Expected outputs

rag/retrieval, evals/experiments/run_retrieval_eval.py, reports/retrieval_baseline.md

## Quality gate

Recall@3, Recall@5, MRR, and latency table exists for baseline retrievers.

## Do not do

- Do not skip logging.
- Do not fake metrics.
- Do not expand scope without recording a decision.
- Do not read unrelated code files unless zone-brain identifies them.

## Current status

done

## Handoff notes

Completed files:

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

Commands run:

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

Blockers:

- No blocker. Dense retrieval fell back to the deterministic local backend because no cached sentence-transformer model was available.

Next phase risks:

- Generic regulation language still outranks some procedural guide chunks on schedule and overload-registration questions.
- Phase 5 should improve high-value top-rank ordering without letting source authority overpower semantic relevance.
