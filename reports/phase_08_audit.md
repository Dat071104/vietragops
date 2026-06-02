# Phase 08 Audit

## Audit scope

Validate the FastAPI service surface, schema behavior, offline fallback path, and secret hygiene before Phase 9.

## Required outputs

- Present: `app/main.py`
- Present: `app/api/routes_documents.py`
- Present: `app/api/routes_query.py`
- Present: `app/api/routes_retrieval.py`
- Present: `app/api/routes_eval.py`
- Present: `app/api/routes_health.py`
- Present: `app/core/config.py`
- Present: `app/core/logging.py`
- Present: `app/core/errors.py`
- Present: `app/schemas/document.py`
- Present: `app/schemas/query.py`
- Present: `app/schemas/eval.py`
- Present: `tests/test_api_health.py`
- Present: `tests/test_api_retrieve.py`
- Present: `tests/test_api_ask.py`

## Verification commands

```bash
python -m compileall app rag evals tests
pytest -q
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

## Results

- Compile check: passed
- Tests: `32 passed`
- OpenAPI surface: verified through `/openapi.json`
- `/ask` offline fallback: verified through FastAPI TestClient without a Groq key
- Secret scans: no matches in repository files

## Reviewer notes

- The API exposes health, documents, retrieval, ask, retrieval eval, generation eval, and experiment artifact listing endpoints behind Pydantic schemas.
- `/retrieve` works without any LLM dependency because it only uses the retrieval stack.
- `/ask` remains available without `GROQ_API_KEY` by flowing through the deterministic generation path from Phase 6.
- Missing experiment lookup now returns a proper `404` API error instead of a success-shaped JSON payload.

## Sign-off

- Reviewer: pass
- Security/Release Auditor: pass
- Phase status: `ready_for_next_phase`
