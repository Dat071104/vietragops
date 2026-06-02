# Phase 09 Audit

## Audit scope

Validate the Streamlit demo surface, local fallback behavior, frontend smoke startup, and secret hygiene before Phase 10.

## Required outputs

- Present: `frontend/streamlit_app.py`
- Present: `frontend/components/answer_view.py`
- Present: `frontend/components/evidence_table.py`
- Present: `frontend/components/eval_dashboard.py`
- Present: `frontend/components/document_table.py`

## Verification commands

```bash
python -m compileall frontend app rag evals tests
pytest -q
python -c "import frontend.components.answer_view, frontend.components.evidence_table, frontend.components.eval_dashboard, frontend.components.document_table; print('frontend_component_imports_ok')"
python -m streamlit run frontend/streamlit_app.py --server.headless true --server.port 8510
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

## Results

- Compile check: passed
- Tests: `32 passed`
- Frontend component imports: passed
- Headless Streamlit smoke boot: passed with HTTP `200`
- Secret scans: no matches in repository files

## Reviewer notes

- The app exposes the required Ask, Evidence, Evaluation, and Documents tabs.
- The sidebar makes API base URL configurable and explains how to force local demo mode.
- Demo mode does not invent benchmark numbers; it reads saved experiment artifacts and local corpus metadata from this workspace.
- The Evidence tab intentionally uses the local advanced retriever so rerank and authority columns are always available, even if the API surface remains slimmer.

## Sign-off

- Reviewer: pass
- Security/Release Auditor: pass
- Phase status: `ready_for_next_phase`
