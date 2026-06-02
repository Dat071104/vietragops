# Pre-Push Validation Report

## Summary

- Status: `pass_with_risks`
- Security: `pass`
- No-Docker tests: `pass`
- API smoke: `pass`
- Frontend smoke: `pass`
- Docker: `blocked`
- Docs truth audit: `pass`
- Safe to push: `no`

The codebase passed the local compile, test, retrieval, generation, API, and frontend checks after fixing six release issues. The main remaining blockers are environmental or release-process related: Docker daemon access is unavailable on this machine, the real Groq smoke test was skipped because no key is set, and the git repository has no commits yet, so the project is not actually in a pushable state today.

## Environment

- Workspace: `D:\Project cua Dat\VietRAGOps\vietragops_ai_workspace_pack\vietragops_ai_workspace_pack`
- Python: `3.13.9`
- pip: `26.1.1`
- Git branch: `master`
- Git history state: `master` has no commits yet
- Required files: all required release files were present

## Security scan results

- `rg -n "gsk_[A-Za-z0-9]{20,}" .`: no matches
- `rg -n "GROQ_API_KEY\s*=\s*gsk_" .`: no matches
- Generic credential-pattern scan: no matches
- `.env.example` contains placeholders only
- `.gitignore` excludes `.env`, `.env.*`, caches, `dist/`, `.zone_context.md`, and `tmp_*.json`
- `GROQ_API_KEY` in environment: not set
- `GROQ_MODEL` in environment: empty

Notes:

- No real Groq key was found in the working tree.
- Git-history secret auditing is not meaningful yet because the repo has no commits.

## No-Docker test results

- `python -m compileall app rag evals frontend scripts tests`: pass
- `pytest -q`: `38 passed`
- `python scripts/validate_chunks.py --chunks-dir data/chunks`: pass
  - `chunks_300.jsonl`: `1036` rows, duplicate rate `0.0010`, abnormal `0`
  - `chunks_500.jsonl`: `695` rows, duplicate rate `0.0014`, abnormal `0`
  - `chunks_800.jsonl`: `572` rows, duplicate rate `0.0017`, abnormal `0`

## Retrieval eval results

- `python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5`
  - Recall@3 `0.7222`, Recall@5 `0.8889`, MRR `0.5917`, Precision@5 `0.1889`, latency `1.83 ms`
- `python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever dense --top_k 5`
  - Recall@3 `0.6667`, Recall@5 `0.7778`, MRR `0.4694`, Precision@5 `0.1667`, latency `8.55 ms`
- `python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5`
  - Recall@3 `0.8333`, Recall@5 `0.8889`, MRR `0.5972`, Precision@5 `0.1889`, latency `11.36 ms`
- `python -m evals.experiments.compare_retrievers`
  - Output: `dist/experiments/retrieval/compare_retrievers_20260602_004255.json`
  - Best config: `hybrid`

## Generation eval results

- `python -m evals.experiments.run_generation_eval`
  - Output: `dist/experiments/generation/generation_eval_20260602_004248.json`
  - Config: `chunks_500 + hybrid + top_k 5 + guardrails on`
  - Recall@5 `0.7500`, Token F1 `0.2047`, citation support `1.0000`, refusal accuracy `1.0000`, latency p50 `250.27 ms`, latency p95 `273.33 ms`
- `python -m evals.experiments.compare_pipelines`
  - Output: `dist/experiments/pipelines/compare_pipelines_20260602_004911.json`
  - Experiment count: `216`
  - Best config: `chunks_500 + bm25 + top_k 3 + reranker off + guardrails off + source_priority off`
  - Best metrics: Recall@3 `0.7500`, Recall@5 `0.7500`, MRR `0.4583`, Token F1 `0.2807`, citation support `1.0000`, refusal accuracy `1.0000`, latency p50 `226.17 ms`, latency p95 `236.48 ms`
- Real Groq smoke test
  - Skipped because `GROQ_API_KEY` is not set

## API smoke test results

- API start command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- `GET /health`: `200`, payload `{"status":"ok","groq_enabled":false}`
- `GET /docs`: `200`
- `POST /retrieve` with checklist payload:
  - Returned `5` ranked results
  - `retriever`: `advanced_hybrid`
  - Debug payload present
- `POST /ask` with checklist payload:
  - Returned grounded answer with `3` citations
  - `refusal`: `false`
  - `confidence`: `0.95`
  - `retrieval_debug.top_k`: `5`
  - No raw traceback detected in the JSON response

## Frontend smoke test results

- Streamlit start command: `python -m streamlit run frontend/streamlit_app.py --server.headless true --server.address 127.0.0.1 --server.port 8501`
- Root URL `http://127.0.0.1:8501`: `200`
- `streamlit.testing.v1.AppTest` rendered the app successfully
- Verified tab labels:
  - `Ask`
  - `Evidence`
  - `Evaluation`
  - `Documents`
- Verified sidebar control:
  - `API base URL` text input present
- Verified fallback messaging:
  - sidebar caption explains local demo mode
  - hero copy explains live API mode vs local demo mode

Notes:

- The in-session browser automation runtime was not callable, so tab verification used Streamlit's testing harness instead of an interactive browser session.
- The deprecated `use_container_width` warnings were removed during validation.

## Docker test results

- `docker --version`: pass
- `docker compose version`: pass
- `docker compose config`: pass
- `docker info`: blocked
  - Docker client is installed, but the daemon endpoint `//./pipe/dockerDesktopLinuxEngine` is unavailable on this machine

Result:

- Docker packaging syntax is valid.
- Full Docker build and container smoke tests remain blocked until Docker Desktop or another daemon is running.

## Documentation truth audit

Updated to match the fresh validation artifacts:

- `README.md`
- `reports/benchmark_report.md`
- `reports/failure_analysis.md`
- `reports/technical_report.md`
- `reports/FINAL_PROJECT_HANDOFF.md`

Key documentation corrections:

- fixed stale generation benchmark metrics after the `top_k` propagation bug
- updated the benchmark artifact paths to the latest validation outputs
- updated failure-count summaries from the rerun pipeline matrix
- updated the handoff test count from `32` to the final verified `38`

## Files changed during validation

- `.gitignore`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `app/api/routes_query.py`
- `app/api/routes_retrieval.py`
- `app/schemas/query.py`
- `evals/experiments/defaults.py`
- `evals/experiments/compare_pipelines.py`
- `evals/experiments/compare_retrievers.py`
- `evals/experiments/run_generation_eval.py`
- `frontend/components/document_table.py`
- `frontend/components/evidence_table.py`
- `frontend/components/eval_dashboard.py`
- `skills/zone-brain/scripts/scan_deps.py`
- `tests/test_api_ask.py`
- `tests/test_api_retrieve.py`
- `tests/test_eval_cli_defaults.py`
- `README.md`
- `reports/benchmark_report.md`
- `reports/failure_analysis.md`
- `reports/technical_report.md`
- `reports/FINAL_PROJECT_HANDOFF.md`
- `reports/PRE_PUSH_FIX_LOG.md`
- `reports/PRE_PUSH_VALIDATION_REPORT.md`

## Bugs fixed

- Added repo-default dataset paths so `compare_retrievers` and `run_generation_eval` now work with the release checklist commands.
- Fixed generation evaluation so `top_k` is actually applied during answer generation and pipeline-matrix benchmarking.
- Made the zone-brain dependency scanner Windows-console safe.
- Updated the API request models and routes so the release smoke payload fields are accepted and honored instead of ignored.
- Migrated deprecated Streamlit dataframe sizing usage to the supported `width="stretch"` API.
- Tightened ignore rules for generated local-only helper artifacts.

## Remaining blockers

- Docker daemon is unavailable, so image build, `docker compose up`, and container smoke tests are still manual blockers.
- `GROQ_API_KEY` is not set, so the real LLM smoke test was skipped.
- The git repository has no commits yet; everything is still untracked, so there is nothing pushable to GitHub until the initial add/commit happens.

## Safe to push?

`No`

Reason:

- The code and docs are in good release shape locally, but the repository itself has not been committed yet and Docker verification is still blocked on the machine environment.

## Exact commands user should run next

1. `git add .`
2. `git status --short`
3. `git commit -m "Pre-push validation fixes and report"`
4. Start Docker Desktop or another Docker daemon.
5. `docker build -t vietragops .`
6. `docker compose up -d`
7. `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
8. `python -m streamlit run frontend/streamlit_app.py --server.headless true --server.address 127.0.0.1 --server.port 8501`
9. If a real Groq key becomes available, set it only in the shell and rerun:
   `python -m evals.experiments.run_generation_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/validation_qa.jsonl --retriever hybrid --top_k 5 --guardrails`
10. After Docker and git are ready:
    `git push origin master`

## Docker Validation Addendum

Docker validation was rerun after Docker Desktop became available.

- `docker --version`: PASS
- `docker compose version`: PASS
- `docker info`: PASS
- `docker compose config`: PASS
- `docker compose build`: PASS
- `docker compose up -d`: PASS
- `docker compose ps`: PASS
- API container `/health`: PASS, returned `{"status":"ok","groq_enabled":false}`
- API container `/docs`: PASS, returned HTTP `200`
- Frontend container `http://127.0.0.1:8501`: PASS, returned HTTP `200`
- Qdrant container: PASS, service started on port `6333`

Updated release status:

- Docker: `pass`
- Safe to push: `yes_after_initial_commit_and_final_secret_scan`
