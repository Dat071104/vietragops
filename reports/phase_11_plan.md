# Phase 11 Plan

## Objective

Turn the project into a recruiter-ready package with an accurate README, technical report, architecture assets, demo script, and final handoff document backed only by generated metrics and real verification logs.

## Inputs found

- `reports/benchmark_report.md`
- `reports/failure_analysis.md`
- `dist/experiments`
- `Dockerfile`
- `docker-compose.yml`
- `frontend/streamlit_app.py`

## Files to create or modify

- `ALWAYS_READ/02_CURRENT_PHASE.md`
- `README.md`
- `reports/technical_report.md`
- `reports/benchmark_report.md`
- `reports/failure_analysis.md`
- `assets/architecture.md`
- `assets/architecture.mmd`
- `demo_video_script.md`
- `reports/FINAL_PROJECT_HANDOFF.md`
- `reports/phase_11_audit.md`
- `reports/phase_11_completion_report.md`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `project_context_cards/PHASE_11_README_REPORT_DEMO.md`

## Implementation plan

1. Rewrite the README around the actual pipeline, eval results, demo UI, API, and reproducibility steps.
2. Write a concise technical report grounded in the implemented phases and generated artifacts.
3. Create architecture diagram source plus an explanatory markdown companion.
4. Produce a recruiter-friendly demo video script and a final project handoff with real metrics, limitations, and manual publishing checks.

## Test plan

- final repo verification commands from the project brief

## Audit plan

- Cross-check every published metric against generated reports or experiment artifacts.
- Ensure limitations mention deterministic evaluation mode and the local Docker-daemon blocker.
- Run secret scans before final completion.

## Expected commands

```bash
python -m compileall app rag evals frontend scripts tests
pytest -q
python scripts/validate_chunks.py --chunks-dir data/chunks
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5
docker compose config
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

## Risk list

- README drift is easy now that the project has multiple benchmark artifacts across phases.
- The final handoff must separate verified capabilities from future improvements very clearly.
- Docker build readiness remains partially blocked by local environment, not repo code.

## Manual checks recommended

- Read the README start to finish as if you were a recruiter landing on the repo for the first time.
- Walk through the demo script while the Streamlit app is open.
- Confirm every CV bullet in the handoff is backed by a real artifact or explicitly marked as a placeholder.
