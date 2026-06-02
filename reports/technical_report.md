# VietRAGOps Technical Report

## Abstract

VietRAGOps is a Vietnamese academic-policy RAG system built around grounded retrieval, citation verification, refusal guardrails, reproducible evaluation, and a recruiter-friendly demo surface. The project uses only public university documents, supports offline fallback behavior for both retrieval and answer generation, and ships with benchmark artifacts, API and UI layers, and packaging infrastructure.

## Motivation

University policy content is high-stakes for students because incorrect answers can affect course registration, graduation eligibility, fee expectations, and academic planning. A useful assistant for this domain must do more than retrieve roughly related text. It must:

- cite the governing document or guide
- refuse when the corpus does not support the answer
- reveal evidence and scoring signals for debugging
- be benchmarkable and reproducible without depending on a single hosted model

VietRAGOps was designed around those constraints.

## Dataset Construction

The corpus was built from public Ton Duc Thang University pages and documents. The final collected set contains:

- 37 public documents
- 37 / 37 parsed successfully
- 481 sections after parsing and normalization

The evaluation pool includes:

- `golden_qa.jsonl`: 120 rows
- `dev_qa.jsonl`: 20 rows
- `validation_qa.jsonl`: 6 rows
- `test_qa.jsonl`: 20 rows

The QA data includes answerable, unanswerable, and private-data-refusal examples across multiple academic-policy categories.

## System Architecture

The system has six layers:

1. Data acquisition and manifest tracking
2. Parsing, cleaning, and normalization
3. Section-aware chunking with metadata
4. Retrieval and reranking
5. Grounded answer generation with citation verification and guardrails
6. Evaluation, API, frontend, and reproducibility packaging

The runtime service path uses FastAPI for the backend and Streamlit for the demo UI. Architecture sources are included in `assets/architecture.mmd` and `assets/architecture.md`.

## Document Parsing and Chunking

The pipeline preserves document identity, source metadata, and section structure so later retrieval and citation verification remain traceable. Chunk variants were generated at three target sizes:

- `chunks_300.jsonl`: 1036 chunks
- `chunks_500.jsonl`: 695 chunks
- `chunks_800.jsonl`: 572 chunks

`chunks_500.jsonl` is the recommended default runtime chunk set because it balances context density and retrieval precision for the interactive demo.

## Retrieval Methods

The retrieval layer includes:

- an offline BM25 lexical retriever
- a dense retriever with deterministic sparse-semantic fallback when local sentence-transformer models are unavailable
- a hybrid retriever using reciprocal-rank fusion
- an advanced hybrid retriever with optional reranking, source-priority, and recency scoring

On the dev retrieval benchmark over `chunks_500.jsonl`, the baseline results were:

- BM25: Recall@3 `0.7222`, Recall@5 `0.8889`, MRR `0.5917`
- Dense fallback: Recall@3 `0.6667`, Recall@5 `0.7778`, MRR `0.4694`
- Hybrid: Recall@3 `0.8333`, Recall@5 `0.8889`, MRR `0.5972`

Hybrid was retained as the recommended runtime default because it improved early precision without sacrificing Recall@5.

## Reranking

Phase 5 introduced a lexical fallback reranker plus the abstraction needed for an optional stronger reranker model later. The advanced retrieval scoring function blended:

- rerank score
- hybrid score
- source authority score
- recency score

The lexical fallback reranker helped a few short procedural guide questions, but the benchmark showed that it reduced recall on several regulation-heavy prompts. As a result, the project kept plain hybrid retrieval as the operational default for Phase 6 and the demo pipeline.

## Answer Generation and Citation Verification

The generation layer builds a grounded prompt, answers from retrieved context, and validates citations against the retrieved chunks. The output schema includes:

- answer text
- structured citations
- confidence
- refusal flag and refusal reason
- retrieval debug payload

If `GROQ_API_KEY` is unavailable, the system falls back to a deterministic offline answer generator. This fallback is intentionally conservative and citation-bound. It is less concise than a tuned LLM path, but it preserves grounded behavior and keeps tests reproducible.

The guardrails refuse:

- insufficient-context questions
- low-support retrieval cases
- personal or private-data questions
- numeric or monetary questions when concrete figures are absent
- outputs that fail citation verification twice

## Evaluation Methodology

The project measures retrieval, generation, abstention, and system latency. Core reported metrics include:

- Recall@3, Recall@5, Recall@10
- MRR
- Precision@5
- token F1
- citation support rate
- refusal accuracy
- latency p50 and p95

The full pipeline experiment matrix evaluated:

- chunk sizes `300`, `500`, and `800`
- BM25, dense fallback, and hybrid retrieval
- reranker off and on
- top-k values `3`, `5`, and `8`
- guardrails off and on
- source-priority off and on

The current published benchmark is deterministic or mock generation only. No local Groq-backed benchmark was executed because the key was not present during evaluation.

## Experiments and Results

The strongest retrieval baseline on the dev set was hybrid retrieval with:

- Recall@3 `0.8333`
- Recall@5 `0.8889`
- MRR `0.5972`

The best config in the reproducible generation matrix was:

- `chunks_500`
- `bm25`
- `top_k=3`
- reranker off
- guardrails off
- source-priority off

Its reported metrics were:

- Token F1 `0.2807`
- Citation support rate `1.0000`
- Refusal accuracy `1.0000`
- Latency p50 `226.17 ms`
- Latency p95 `236.48 ms`

For the runtime-oriented reference configuration `chunks_500 + hybrid + top_k 5 + guardrails on`, the generation benchmark reported:

- Token F1 `0.2047`
- Citation support rate `1.0000`
- Refusal accuracy `1.0000`
- Latency p50 `250.27 ms`

These numbers should be interpreted as reproducible offline engineering benchmarks, not final production-quality answer metrics.

## Failure Analysis

The current matrix’s leading failure labels were:

- `retrieval_miss`: 222
- `stale_source`: 84

The dominant failure pattern remains regulation-heavy retrieval misses, followed by source-conflict questions that mix old and new policy artifacts. Procedural questions usually retrieve relevant guidance, but the deterministic answerer can still carry along extra evidence lines.

## Limitations

- Generation evaluation is deterministic or mock-only at the moment.
- The validation split is intentionally small to keep the matrix runtime practical locally.
- The lexical fallback reranker is not strong enough to become the default on regulation-heavy prompts.
- Docker configuration validates successfully, but a local image build was blocked at handoff time because the Docker daemon was unavailable.

## Future Work

- Run a full benchmark with a real Groq-backed generator.
- Add a stronger local reranker model and revisit advanced retrieval as a runtime default.
- Expand the QA dataset with more human-authored paraphrases and source-conflict cases.
- Add container-level smoke tests once Docker build execution is available locally.
