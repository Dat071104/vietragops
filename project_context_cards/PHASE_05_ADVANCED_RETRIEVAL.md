# Phase 5 - Advanced retrieval

## Phase goal

Add BGE-M3/hybrid retrieval, reranking, source priority, and ablation report.

## Required inputs

- Current project context.
- Implementation log.
- Relevant previous phase outputs.

## Expected outputs

rag/retrieval/reranker.py, source_priority.py, reports/advanced_retrieval_benchmark.md

## Quality gate

Hybrid plus reranker is measured against baseline; if not better, report explains why.

## Do not do

- Do not skip logging.
- Do not fake metrics.
- Do not expand scope without recording a decision.
- Do not read unrelated code files unless zone-brain identifies them.

## Current status

done

## Handoff notes

Completed files:

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

Commands run:

```bash
python -m compileall rag evals tests
pytest -q
python -m evals.experiments.compare_retrievers --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --top_k 5
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

Blockers:

- No blocker. Qdrant stayed optional and was not required for the local benchmark.

Next phase risks:

- The lexical reranker abstraction is useful, but the current offline fallback should not become the default retrieval path for grounded generation.
- Phase 6 should use the baseline hybrid retriever as the default context input while keeping the advanced reranker path optional for debugging.
