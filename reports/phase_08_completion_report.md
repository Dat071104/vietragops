# Phase 08 Completion Report

## Summary

Phase 8 exposed the retrieval and grounded-answer pipeline through FastAPI, added typed request and response schemas, wrapped errors cleanly, and verified the service can run without a Groq key.

## Deliverables completed

- `app/main.py`
- `app/api/routes_documents.py`
- `app/api/routes_query.py`
- `app/api/routes_retrieval.py`
- `app/api/routes_eval.py`
- `app/api/routes_health.py`
- `app/core/config.py`
- `app/core/logging.py`
- `app/core/errors.py`
- `app/schemas/document.py`
- `app/schemas/query.py`
- `app/schemas/eval.py`
- `reports/phase_08_plan.md`
- `reports/phase_08_audit.md`
- `reports/phase_08_completion_report.md`
- `tests/test_api_health.py`
- `tests/test_api_retrieve.py`
- `tests/test_api_ask.py`

## Commands run

```bash
python -m compileall app rag evals tests
pytest -q
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

## Test results

- `pytest -q`: `32 passed`
- OpenAPI check: passed
- Health endpoint: passed
- Retrieve endpoint: passed
- Ask endpoint refusal case: passed
- Missing experiment lookup: passed with `404`

## Bugs found and fixed

- Symptom: `/experiments/{experiment_id}` returned a success-shaped JSON payload for missing artifacts.
- Root cause: the route returned a plain dictionary instead of raising an HTTP-layer error.
- Fix: raised `AppError("Experiment not found.", status_code=404)` and added a regression test.
- Files changed: `app/api/routes_eval.py`, `tests/test_api_health.py`
- Verification: reran `pytest -q` and `python -m compileall app rag evals tests`
- Regression risk: low, because the change only tightens failure-path behavior.

## Remaining risks

- The API layer currently reads experiment JSON straight from disk on demand; this is fine for the local artifact volume but may need caching later.
- The deterministic generation fallback is useful for offline reliability, but its answers remain more extractive than a tuned real-LLM path.
- Upload and index routes are lightweight placeholders over the current local workflow rather than a full ingestion pipeline.

## Manual checks recommended

- Start the API with Uvicorn and open `/docs`.
- Call `/ask` with one answerable question and one out-of-scope question.
- Call `/eval/retrieval` and `/experiments` after generating a fresh benchmark artifact.

## Readiness for next phase

- Status: `ready_for_next_phase`
- Next phase: `Phase 9 - Frontend + Debug Panel`
