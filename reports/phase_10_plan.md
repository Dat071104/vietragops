# Phase 10 Plan

## Objective

Make the project reproducible with Docker, Docker Compose, `.env.example`, and CI while keeping offline fallback support intact and avoiding any committed secrets.

## Inputs found

- `app/main.py`
- `frontend/streamlit_app.py`
- `tests`
- `data/chunks`
- `dist/experiments`

## Files to create or modify

- `ALWAYS_READ/02_CURRENT_PHASE.md`
- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `.github/workflows/ci.yml`
- `reports/phase_10_audit.md`
- `reports/phase_10_completion_report.md`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `project_context_cards/PHASE_10_DOCKER_TESTS_CI.md`

## Implementation plan

1. Create a single Docker image that can serve either the FastAPI backend or the Streamlit frontend by switching commands.
2. Add a Compose stack for `api`, `frontend`, `qdrant`, and optional `postgres` with safe defaults and no real secrets.
3. Add `.env.example` with only placeholder `GROQ_API_KEY` and model settings.
4. Add CI steps for compilation, pytest, retrieval smoke eval, and `docker compose config`.

## Test plan

- `python -m compileall frontend app rag evals tests`
- `pytest -q`
- `python scripts/validate_chunks.py --chunks-dir data/chunks`
- `python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5`
- `docker compose config`

## Audit plan

- Verify `.env.example` contains only safe placeholders.
- Verify Compose does not require a real Groq key to parse.
- Verify CI avoids long-running matrix jobs while still testing a real retrieval path.
- Run secret scans before phase completion.

## Expected commands

```bash
python -m compileall frontend app rag evals tests
pytest -q
python scripts/validate_chunks.py --chunks-dir data/chunks
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5
docker compose config
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

## Risk list

- Docker may be unavailable locally, which would limit verification to config validation.
- A single-image approach must keep both API and frontend startup commands straightforward.
- Retrieval smoke evals need to stay fast enough for CI while still being meaningful.

## Manual checks recommended

- Run `docker compose up api frontend` locally after config validation.
- Open the frontend container in a browser and verify it can reach the API service.
- Confirm `.env.example` is the only environment file intended for version control.
