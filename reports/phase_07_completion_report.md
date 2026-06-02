# Phase 07 Completion Report

## Summary

Phase 7 added a reproducible QA-dataset builder, split evaluation files, generation and abstention metrics, pipeline experiment runners, and benchmark plus failure-analysis reports backed by actual experiment JSON artifacts.

## Deliverables completed

- `scripts/build_golden_qa.py`
- `evals/datasets/golden_qa.jsonl`
- `evals/datasets/dev_qa.jsonl`
- `evals/datasets/validation_qa.jsonl`
- `evals/datasets/test_qa.jsonl`
- `evals/metrics/generation_metrics.py`
- `evals/metrics/abstention_metrics.py`
- `evals/metrics/system_metrics.py`
- `evals/experiments/run_generation_eval.py`
- `evals/experiments/compare_pipelines.py`
- `evals/experiments/export_report.py`
- `reports/benchmark_report.md`
- `reports/failure_analysis.md`
- `reports/phase_07_plan.md`
- `reports/phase_07_audit.md`
- `reports/phase_07_completion_report.md`
- `tests/test_generation_metrics.py`
- `tests/test_abstention_metrics.py`
- `tests/test_compare_pipelines.py`

## Commands run

```bash
python -m compileall rag evals scripts tests
pytest -q
python scripts/build_golden_qa.py
python -m evals.experiments.run_generation_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/validation_qa.jsonl --retriever hybrid --top_k 5 --guardrails
python -m evals.experiments.compare_pipelines
python -m evals.experiments.export_report --input dist/experiments/pipelines/compare_pipelines_20260601_212747.json
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

## Test and experiment results

- `pytest -q`: `27 passed`
- `golden_qa.jsonl`: 120 rows
- Best matrix config: `chunks_300 + bm25 + top_k 3 + guardrails off`
- Best matrix token F1: `0.2093`
- Reference hybrid deterministic run token F1: `0.2047`
- Citation support rate in measured runs: `1.0`
- Refusal accuracy in measured runs: up to `1.0`

## Bugs found and fixed

- Symptom: the first full pipeline matrix timed out before completion on a 40-row validation split.
- Root cause: 216 configs times the deterministic answer stack was too slow for the local runtime budget.
- Fix: deduplicated operationally identical configs inside `compare_pipelines.py` and reduced the validation split to a documented small tuning set while preserving the larger golden pool.
- Files changed: `scripts/build_golden_qa.py`, `evals/experiments/compare_pipelines.py`
- Verification: reran `python scripts/build_golden_qa.py` and `python -m evals.experiments.compare_pipelines`
- Regression risk: medium, because the smaller validation split is faster but less statistically robust.

## Remaining risks

- The evaluation mode is still deterministic or mock-only, not a real LLM benchmark.
- The validation split is intentionally tiny for runtime reasons and should be expanded later if more compute time is available.
- Retrieval misses remain the dominant failure label in the current experiment set.

## Manual checks recommended

- Review a sample of QA rows from `golden_qa.jsonl` before publishing.
- Re-run the benchmark with a larger validation split if the runtime budget allows.
- Add more human-authored paraphrases and source-conflict examples in a future iteration.

## Readiness for next phase

- Status: `ready_for_next_phase`
- Next phase: `Phase 8 — FastAPI Backend`
