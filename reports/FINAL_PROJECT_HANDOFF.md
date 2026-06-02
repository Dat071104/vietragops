# Final Project Handoff

## Phase-by-phase completion summary

- Phase 4: implemented BM25, dense fallback, hybrid retrieval, retrieval metrics, dev QA set, and baseline benchmark report
- Phase 5: added reranker abstraction, source-priority scoring, advanced hybrid retrieval, optional Qdrant surface, and ablation report
- Phase 6: added grounded generation, prompt builder, citation verifier, guardrails, Groq client, and deterministic offline fallback
- Phase 7: added golden QA builder, generation and abstention metrics, pipeline comparison harness, benchmark report, and failure analysis
- Phase 8: exposed the system through FastAPI with typed schemas and offline-safe ask and retrieve routes
- Phase 9: built a Streamlit demo with Ask, Evidence, Evaluation, and Documents tabs plus local demo fallback
- Phase 10: added `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `.env.example`, and GitHub Actions CI
- Phase 11: rewrote README, added technical report, architecture assets, demo script, and final handoff

## Final project structure

```text
app/        FastAPI backend
rag/        retrieval, generation, chunking, loaders, preprocessing
evals/      datasets, metrics, experiment runners
frontend/   Streamlit demo UI
scripts/    data collection, validation, and dataset building
tests/      unit and API tests
reports/    benchmarks, failure analysis, phase reports, handoff docs
data/       raw docs, manifests, processed docs, chunk artifacts
assets/     architecture diagram and notes
```

## How to run locally

```powershell
pip install -r requirements.txt
pytest -q
python -m compileall app rag evals frontend scripts tests
```

Optional Groq setup:

```powershell
$env:GROQ_API_KEY="PASTE_REAL_KEY_HERE"
$env:GROQ_MODEL="llama-3.3-70b-versatile"
```

## How to run the API

```powershell
uvicorn app.main:app --reload
```

Docs:

- `http://127.0.0.1:8000/docs`

## How to run the frontend

```powershell
streamlit run frontend/streamlit_app.py
```

Optional API base URL override:

```powershell
$env:VIETRAGOPS_API_BASE_URL="http://127.0.0.1:8000"
```

## How to run retrieval evaluation

```powershell
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5
```

## How to run generation evaluation

```powershell
python -m evals.experiments.run_generation_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/validation_qa.jsonl --retriever hybrid --top_k 5 --guardrails
```

## How to reproduce the benchmark

```powershell
python scripts/build_golden_qa.py
python -m evals.experiments.compare_pipelines
python -m evals.experiments.export_report --input dist/experiments/pipelines/compare_pipelines_20260602_004911.json
```

## Known limitations

- Published generation metrics are deterministic or mock-only because no local Groq key was used during benchmark execution.
- The validation split is intentionally small for runtime reasons.
- The lexical fallback reranker is useful on some procedural questions but not strong enough to replace plain hybrid retrieval as the default.
- Docker packaging is present and Compose config validates, but a full image build was blocked locally because the Docker daemon was unavailable.

## Remaining TODOs

- Re-run generation benchmarks with a real Groq-backed model.
- Expand the QA dataset and increase the validation split.
- Add stronger reranking and revisit advanced retrieval defaults.
- Re-run Docker build and container smoke tests once the local daemon is available.

## Manual checks before publishing

- Start the API and open `/docs`.
- Run the Streamlit app and click through all four tabs.
- Re-run `docker build -t vietragops:release .` after Docker Desktop is running.
- Re-run secret scans:
  - `rg -n "gsk_[A-Za-z0-9]{20,}" .`
  - `rg -n "GROQ_API_KEY\s*=\s*gsk_" .`
- If a real Groq key is available, run one live generation smoke test before public demo use.

## CV-ready bullets

- Built a Vietnamese RAG system over 37 public academic-policy documents, parsing 37/37 successfully into 481 sections and 695 default runtime chunks.
- Implemented offline-capable BM25, dense fallback, and hybrid retrieval; hybrid achieved Recall@3 `0.8333`, Recall@5 `0.8889`, and MRR `0.5972` on the dev retrieval benchmark.
- Built a reproducible 120-question evaluation harness with citation support, refusal metrics, and failure labeling; the latest offline matrix validation reached token F1 `0.2807`, citation support `1.0000`, and refusal accuracy `1.0000`.
- Shipped the system behind FastAPI and a Streamlit debug UI with evidence inspection, experiment browsing, and local demo fallback, backed by `38` passing pytest checks in the latest validation run.
