# Project Context: VietRAGOps

## Product

VietRAGOps is a production-style Vietnamese document intelligence and RAG evaluation platform for public academic/policy documents.

## Core promise

Answer Vietnamese questions using indexed public documents, show evidence, verify citations, refuse unsupported questions, and measure the pipeline with repeatable evaluation.

## Main capabilities

- Public document ingestion: html, pdf, docx, markdown, text.
- Cleaning and section-aware parsing.
- Section-aware chunking with metadata.
- Hybrid retrieval: lexical plus dense retrieval.
- Reranking.
- Source authority and recency scoring.
- Citation-grounded generation.
- Citation verifier and refusal guardrail.
- Golden QA dataset.
- Retrieval and generation benchmark reports.
- FastAPI backend, Swagger docs, Docker Compose, tests, CI, and debug UI.

## Success metrics

- Retrieval: Recall@3, Recall@5, Recall@10, MRR, Precision@k, nDCG@k.
- Generation: faithfulness, answer relevancy, answer correctness, context precision, context recall.
- Guardrail: refusal accuracy, unsupported-answer rate, citation support rate.
- System: latency p50/p95, error rate, indexing time, token/cost when available.

## Important constraint

Do not fake metrics. Use `x.xx` placeholders until a script produces real results.
