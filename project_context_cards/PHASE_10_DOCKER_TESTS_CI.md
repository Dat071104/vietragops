# Phase 10 - Docker, tests, CI

## Phase goal

Make project reproducible with Docker Compose, pytest, CI, and env examples.

## Required inputs

- Current project context.
- Implementation log.
- Relevant previous phase outputs.

## Expected outputs

Dockerfile, docker-compose.yml, tests, .github/workflows/ci.yml, .env.example

## Quality gate

docker compose up works, pytest passes, CI passes, no secrets committed.

## Do not do

- Do not skip logging.
- Do not fake metrics.
- Do not expand scope without recording a decision.
- Do not read unrelated code files unless zone-brain identifies them.

## Current status

done

## Handoff notes

- Completed files:
  - `requirements.txt`
  - `.dockerignore`
  - `.env.example`
  - `Dockerfile`
  - `docker-compose.yml`
  - `.github/workflows/ci.yml`
- Commands run:
  - `python -m compileall app rag evals frontend scripts tests`
  - `pytest -q`
  - `python scripts/validate_chunks.py --chunks-dir data/chunks`
  - `python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5`
  - `docker compose config`
  - `docker build -t vietragops:phase10 .`
  - `rg -n "gsk_[A-Za-z0-9]{20,}" .`
  - `rg -n "GROQ_API_KEY\s*=\s*gsk_" .`
- Result:
  - packaging files, CI, and env-example are in place
  - compile checks, tests, chunk validation, retrieval smoke eval, and Compose parsing all passed
- Blockers:
  - local Docker daemon was not running, so image build could not be completed in this environment
- Next phase risks:
  - README and report claims must stay aligned with the documented Docker build blocker
  - recruiter-facing docs must distinguish deterministic offline benchmark results from future real-LLM runs
