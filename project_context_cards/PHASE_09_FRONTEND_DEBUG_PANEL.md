# Phase 9 - Frontend and debug panel

## Phase goal

Build demo UI with ask, evidence, evaluation, and documents tabs.

## Required inputs

- Current project context.
- Implementation log.
- Relevant previous phase outputs.

## Expected outputs

frontend/streamlit_app.py, frontend/components

## Quality gate

Viewer can understand answer, evidence, and metrics in 30 seconds.

## Do not do

- Do not skip logging.
- Do not fake metrics.
- Do not expand scope without recording a decision.
- Do not read unrelated code files unless zone-brain identifies them.

## Current status

done

## Handoff notes

- Completed files:
  - `frontend/streamlit_app.py`
  - `frontend/components/answer_view.py`
  - `frontend/components/evidence_table.py`
  - `frontend/components/eval_dashboard.py`
  - `frontend/components/document_table.py`
- Commands run:
  - `python -m compileall frontend app rag evals tests`
  - `pytest -q`
  - `python -c "import frontend.components.answer_view, frontend.components.evidence_table, frontend.components.eval_dashboard, frontend.components.document_table; print('frontend_component_imports_ok')"`
  - `python -m streamlit run frontend/streamlit_app.py --server.headless true --server.port 8510`
  - `rg -n "gsk_[A-Za-z0-9]{20,}" .`
  - `rg -n "GROQ_API_KEY\s*=\s*gsk_" .`
- Result:
  - Streamlit demo boots successfully, supports four required tabs, and falls back to local pipeline plus artifact mode when the API is unavailable.
- Blockers:
  - none
- Next phase risks:
  - Docker images must stay lightweight enough for reproducible local startup
  - CI should avoid long-running benchmark matrices while still checking retrieval behavior
