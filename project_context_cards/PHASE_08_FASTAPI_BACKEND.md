# Phase 8 - FastAPI backend

## Phase goal

Expose ingestion, retrieval, ask, eval, experiment, and health endpoints.

## Required inputs

- Current project context.
- Implementation log.
- Relevant previous phase outputs.

## Expected outputs

app/main.py, app/api, app/schemas

## Quality gate

Swagger works, /health OK, /ask returns answer+citation+debug, validation/errors are clean.

## Do not do

- Do not skip logging.
- Do not fake metrics.
- Do not expand scope without recording a decision.
- Do not read unrelated code files unless zone-brain identifies them.

## Current status

done

## Handoff notes

- Completed files:
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
  - `tests/test_api_health.py`
  - `tests/test_api_retrieve.py`
  - `tests/test_api_ask.py`
- Commands run:
  - `python -m compileall app rag evals tests`
  - `pytest -q`
  - `rg -n "gsk_[A-Za-z0-9]{20,}" .`
  - `rg -n "GROQ_API_KEY\s*=\s*gsk_" .`
- Result:
  - FastAPI service is available with OpenAPI docs, typed schemas, health/document/retrieval/query/eval routes, and offline deterministic generation fallback.
- Blockers:
  - none
- Next phase risks:
  - the frontend must handle API-unavailable demo mode cleanly
  - experiment tables should avoid presenting mock metrics as real benchmark data
