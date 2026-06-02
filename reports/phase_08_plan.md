# Phase 08 Plan

## Objective

Expose the current pipeline as a FastAPI service with health, document, retrieval, ask, eval, and experiment endpoints that remain functional without a Groq key.

## Inputs found

- `data/chunks/chunks_500.jsonl`
- `data/manifests/documents_manifest.csv`
- `evals/datasets/dev_qa.jsonl`
- `evals/datasets/validation_qa.jsonl`
- `dist/experiments/retrieval/*`
- `dist/experiments/generation/*`
- `dist/experiments/pipelines/*`

## Files to create or modify

- `ALWAYS_READ/02_CURRENT_PHASE.md`
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
- `reports/phase_08_audit.md`
- `reports/phase_08_completion_report.md`
- `tests/test_api_health.py`
- `tests/test_api_retrieve.py`
- `tests/test_api_ask.py`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `project_context_cards/PHASE_08_FASTAPI_BACKEND.md`

## Implementation plan

1. Add app config, logging, and error wrappers.
2. Add Pydantic request and response schemas for documents, retrieval, ask, and eval endpoints.
3. Add API routes over the current retrieval, answer generation, and experiment artifacts.
4. Make `/ask` and `/retrieve` work without Groq by using the deterministic answer path.
5. Add FastAPI TestClient tests for health, retrieval, and ask.

## Test plan

- `python -m compileall app rag evals tests`
- `pytest -q`

## Audit plan

- Verify Swagger/OpenAPI is available through the app surface.
- Verify raw exceptions are converted to API errors.
- Verify `/ask` returns refusal or grounded answer without any Groq key.
- Run secret scans before phase completion.

## Expected commands

```bash
python -m compileall app rag evals tests
pytest -q
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\\s*=\\s*gsk_" .
```

## Risk list

- If FastAPI is missing locally, we may need to install it before tests can run.
- Loading experiment JSON on every request could be slow if the route layer is too naive.
- Reusing the deterministic answer path through the API may surface its current verbosity more visibly.

## Manual checks recommended

- Open Swagger after the backend is wired.
- Hit `/ask` with one answerable and one refusal case.
- Check that `/experiments` lists the latest benchmark artifacts without recomputation.
