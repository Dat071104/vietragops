# Phase 10 Audit

## Audit scope

Validate the Docker, Compose, env-example, CI, and core reproducibility surfaces before Phase 11.

## Required outputs

- Present: `Dockerfile`
- Present: `docker-compose.yml`
- Present: `.env.example`
- Present: `.github/workflows/ci.yml`
- Present: `requirements.txt`

## Verification commands

```bash
python -m compileall app rag evals frontend scripts tests
pytest -q
python scripts/validate_chunks.py --chunks-dir data/chunks
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5
docker compose config
docker build -t vietragops:phase10 .
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

## Results

- Compile check: passed
- Tests: `32 passed`
- Chunk validation: passed
- Retrieval smoke eval: passed
- Compose config: passed
- Docker image build: blocked because the local Docker daemon was not running
- Secret scans: no matches in repository files

## Reviewer notes

- `.env.example` contains only safe placeholder values for `GROQ_API_KEY` and `GROQ_MODEL`.
- Compose exposes `api`, `frontend`, and `qdrant`, plus an optional `postgres` profile.
- CI covers compile checks, pytest, chunk validation, retrieval smoke eval, and Compose parsing without requiring any real Groq key.
- The Docker build blocker is environmental rather than repository-caused because `docker compose config` succeeded while the daemon socket was unavailable.

## Sign-off

- Reviewer: pass with documented Docker-daemon blocker
- Security/Release Auditor: pass
- Phase status: `ready_with_documented_risks`
