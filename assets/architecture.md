# Architecture Notes

## Overview

VietRAGOps is organized around a transparent RAG pipeline rather than a single opaque answer endpoint.

Main layers:

1. Corpus acquisition and manifesting
2. Parsing and normalization
3. Chunking and metadata enrichment
4. Retrieval and optional reranking
5. Grounded generation, citation verification, and guardrails
6. Evaluation, API serving, demo UI, and reproducibility tooling

## Runtime path

The default runtime path is:

1. Receive a question
2. Retrieve context with hybrid retrieval over `chunks_500.jsonl`
3. Build prompt or deterministic fallback context
4. Generate grounded answer
5. Verify citations against retrieved chunks
6. Refuse if evidence is weak, unsafe, or unsupported
7. Return structured answer JSON to the API and UI

## Retrieval notes

- BM25 is the fastest baseline.
- Dense retrieval remains available even without a downloaded embedding model because the project includes a deterministic sparse-semantic fallback.
- Hybrid was selected as the operational default because it outperformed the pure baselines on early recall and MRR in the dev retrieval benchmark.

## Generation notes

- The system does not require `GROQ_API_KEY` to function.
- When the key is absent, deterministic offline generation keeps tests and demos reproducible.
- Citation verification and guardrails are first-class components, not post-hoc decorations.

## Serving notes

- FastAPI exposes documents, retrieval, ask, evaluation, and experiment routes.
- Streamlit exposes a recruiter-friendly debug surface with Ask, Evidence, Evaluation, and Documents tabs.
- The frontend can fall back to local demo mode if the API is unavailable.

## Packaging notes

- `Dockerfile` and `docker-compose.yml` are included.
- `docker compose config` was validated successfully during handoff.
- A full local image build was blocked only because the Docker daemon was unavailable at verification time.
