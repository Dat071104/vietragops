# Phase 07 Audit

## Audit scope

Validate the QA corpus, experiment runners, benchmark provenance, and secret hygiene before Phase 8.

## Required outputs

- Present: `evals/datasets/golden_qa.jsonl`
- Present: `evals/datasets/dev_qa.jsonl`
- Present: `evals/datasets/validation_qa.jsonl`
- Present: `evals/datasets/test_qa.jsonl`
- Present: `evals/metrics/generation_metrics.py`
- Present: `evals/metrics/abstention_metrics.py`
- Present: `evals/metrics/system_metrics.py`
- Present: `evals/experiments/compare_pipelines.py`
- Present: `evals/experiments/run_generation_eval.py`
- Present: `evals/experiments/export_report.py`
- Present: `reports/benchmark_report.md`
- Present: `reports/failure_analysis.md`
- Present: `tests/test_generation_metrics.py`
- Present: `tests/test_abstention_metrics.py`
- Present: `tests/test_compare_pipelines.py`

## Verification commands

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

## Results

- Compile check: passed
- Tests: `27 passed`
- Golden QA generation: passed
- Single generation eval: passed
- Full pipeline matrix: passed with 216 recorded configs
- Secret scans: no matches in repository files

## Reviewer notes

- `golden_qa.jsonl` contains 120 rows, which satisfies the minimum acceptable target.
- Validation was intentionally kept to 6 rows so the full config matrix could finish locally; this trade-off is documented in the benchmark report.
- All benchmark and failure-analysis numbers come from generated experiment artifacts, not manual edits.
- Generation evaluation remains deterministic or mock-only because no local Groq key was available.

## Sign-off

- Reviewer: pass with documented validation-split trade-off
- Security/Release Auditor: pass
- Phase status: `ready_for_next_phase`
