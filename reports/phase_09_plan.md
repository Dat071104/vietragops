# Phase 09 Plan

## Objective

Create a recruiter-friendly Streamlit interface over the FastAPI service with clear answer, evidence, evaluation, and document inventory views, while preserving a demo mode when the API is unavailable.

## Inputs found

- `app/main.py`
- `dist/experiments`
- `data/manifests/documents_manifest.csv`
- `reports/benchmark_report.md`
- `reports/failure_analysis.md`

## Files to create or modify

- `ALWAYS_READ/02_CURRENT_PHASE.md`
- `frontend/streamlit_app.py`
- `frontend/components/answer_view.py`
- `frontend/components/evidence_table.py`
- `frontend/components/eval_dashboard.py`
- `frontend/components/document_table.py`
- `reports/phase_09_audit.md`
- `reports/phase_09_completion_report.md`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `project_context_cards/PHASE_09_FRONTEND_DEBUG_PANEL.md`

## Implementation plan

1. Create a small frontend component package for answer cards, evidence tables, evaluation tables, and document tables.
2. Build a four-tab Streamlit app with configurable API base URL and automatic live-or-demo fallback.
3. Populate the demo mode from local experiment artifacts and manifest data without inventing benchmark numbers.
4. Make the Ask tab expose answer, confidence, refusal reason, citations, and a debug toggle.

## Test plan

- `python -m compileall frontend app rag evals tests`
- targeted import smoke checks for frontend modules

## Audit plan

- Verify all required tabs render from local data when the API is unavailable.
- Verify the UI labels demo data clearly.
- Run secret scans before phase completion.

## Expected commands

```bash
python -m compileall frontend app rag evals tests
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

## Risk list

- Streamlit may be unavailable locally, which would limit execution to import-level verification.
- The API may not expose every evidence-score field yet, so the UI needs graceful column fallback.
- Experiment artifacts from multiple phases need to be presented without confusing retrieval and generation metrics.

## Manual checks recommended

- Run the app locally and switch between live API mode and demo mode.
- Toggle debug output in the Ask tab after both an answerable and a refusal query.
- Review the Evaluation tab to confirm that real benchmark artifacts are clearly attributed.
