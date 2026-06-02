# Phase 07 Plan

## Objective

Create the reproducible evaluation harness: build a larger golden QA dataset and split files, add generation, abstention, and system metrics, run pipeline comparisons across retrieval and guardrail settings, and export benchmark plus failure-analysis reports.

## Inputs found

- `data/chunks/chunks_300.jsonl`
- `data/chunks/chunks_500.jsonl`
- `data/chunks/chunks_800.jsonl`
- `evals/datasets/dev_qa.jsonl`
- `reports/retrieval_baseline.md`
- `reports/advanced_retrieval_benchmark.md`
- `reports/generation_behavior_report.md`

## Files to create or modify

- `ALWAYS_READ/02_CURRENT_PHASE.md`
- `evals/datasets/golden_qa.jsonl`
- `evals/datasets/dev_qa.jsonl`
- `evals/datasets/validation_qa.jsonl`
- `evals/datasets/test_qa.jsonl`
- `evals/metrics/generation_metrics.py`
- `evals/metrics/abstention_metrics.py`
- `evals/metrics/system_metrics.py`
- `evals/experiments/compare_pipelines.py`
- `evals/experiments/run_generation_eval.py`
- `evals/experiments/export_report.py`
- `reports/benchmark_report.md`
- `reports/failure_analysis.md`
- `reports/phase_07_audit.md`
- `reports/phase_07_completion_report.md`
- `tests/test_generation_metrics.py`
- `tests/test_abstention_metrics.py`
- `tests/test_compare_pipelines.py`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `project_context_cards/PHASE_07_EVALUATION_HARNESS.md`

## Implementation plan

1. Add a reproducible dataset builder or generation workflow to expand the QA corpus to at least 100 grounded examples.
2. Split the corpus into dev, validation, and locked test sets.
3. Add generation, abstention, and system metric modules.
4. Add generation-eval and pipeline-comparison runners using the current retrieval and generation stacks.
5. Run the pipeline matrix and export benchmark plus failure-analysis markdown reports from the experiment artifacts.

## Test plan

- `python -m compileall rag evals tests`
- `pytest -q`
- `python -m evals.experiments.run_generation_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/validation_qa.jsonl --retriever hybrid --top_k 5`
- `python -m evals.experiments.compare_pipelines`

## Audit plan

- Verify the golden QA total count is at least 100 and document the expansion strategy.
- Verify benchmark numbers come from experiment JSON, not manual edits.
- Verify deterministic or mock evaluation mode is labeled clearly where Groq is unavailable.
- Run secret scans before phase completion.

## Expected commands

```bash
python -m compileall rag evals tests
pytest -q
python -m evals.experiments.run_generation_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/validation_qa.jsonl --retriever hybrid --top_k 5
python -m evals.experiments.compare_pipelines
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\\s*=\\s*gsk_" .
```

## Risk list

- Template-generated QA pairs may bias the benchmark toward extractive behavior.
- The full experiment matrix could surface inconsistent latency if reranked and non-reranked pipelines share different candidate depths.
- Source-conflict labeling may require careful heuristics because the corpus includes multiple regulation vintages.

## Manual checks recommended

- Review a sample of generated QA rows from each category.
- Inspect a few failure labels manually before publishing the report.
- Keep deterministic evaluation mode explicit in all benchmark outputs until real-LLM validation is available.
