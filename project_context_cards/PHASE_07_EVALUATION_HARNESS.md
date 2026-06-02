# Phase 7 - Evaluation harness

## Phase goal

Create repeatable retrieval/generation/system evaluations and failure analysis.

## Required inputs

- Current project context.
- Implementation log.
- Relevant previous phase outputs.

## Expected outputs

evals/metrics, evals/experiments/compare_pipelines.py, reports/benchmark_report.md

## Quality gate

At least 5 experiment configs, golden QA split, metrics table, and failure cases exist.

## Do not do

- Do not skip logging.
- Do not fake metrics.
- Do not expand scope without recording a decision.
- Do not read unrelated code files unless zone-brain identifies them.

## Current status

done

## Handoff notes

Completed files:

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

Commands run:

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

Blockers:

- No blocker. The validation split was intentionally reduced to keep the full matrix reproducible within the local runtime budget.

Next phase risks:

- Phase 8 should expose experiment artifacts and benchmark metadata cleanly through the API so the frontend can consume them without re-running evals.
