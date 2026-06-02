# Phase 10 Completion Report

## Summary

Phase 10 made the project reproducible with a shared Python dependency file, a Docker image definition, a Compose stack, a safe `.env.example`, and a CI workflow that exercises compilation, tests, chunk validation, retrieval smoke eval, and Compose parsing.

## Deliverables completed

- `requirements.txt`
- `.dockerignore`
- `.env.example`
- `Dockerfile`
- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `reports/phase_10_plan.md`
- `reports/phase_10_audit.md`
- `reports/phase_10_completion_report.md`

## Commands run

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

## Test and validation results

- `pytest -q`: `32 passed`
- Chunk validation:
  - `chunks_300.jsonl`: `1036` rows, duplicate rate `0.0010`
  - `chunks_500.jsonl`: `695` rows, duplicate rate `0.0014`
  - `chunks_800.jsonl`: `572` rows, duplicate rate `0.0017`
- Retrieval smoke eval artifact: `dist/experiments/retrieval/retrieval_hybrid_chunks_500_20260601_214725.json`
- Retrieval smoke metrics:
  - Recall@5: `0.8889`
  - MRR: `0.5972`
  - Precision@5: `0.1889`
  - Latency ms: `10.7`
- `docker compose config`: passed

## Bugs found and fixed

- No repository-code bugs were found during Phase 10 validation.
- Environmental blocker documented:
  - Symptom: `docker build -t vietragops:phase10 .` failed before image construction.
  - Root cause: the local Docker daemon socket `dockerDesktopLinuxEngine` was unavailable.
  - Fix: none inside the repository; documented the issue and relied on successful Compose config parsing for static verification.
  - Regression risk: low for repository code, medium for local run readiness until Docker Desktop or an equivalent daemon is started.

## Remaining risks

- A full Docker image build and container startup still need to be rerun once the local Docker daemon is available.
- Dependencies are specified in `requirements.txt` without lockfile pinning, which is simpler but less deterministic than a fully locked environment.

## Manual checks recommended

- Start Docker Desktop or another Docker daemon and rerun `docker build -t vietragops:phase10 .`.
- After the build succeeds, run `docker compose up api frontend`.
- Open the frontend on port `8501` and confirm it can reach the API on port `8000`.

## Readiness for next phase

- Status: `ready_with_documented_risks`
- Next phase: `Phase 11 - README + Technical Report + Demo Assets`
