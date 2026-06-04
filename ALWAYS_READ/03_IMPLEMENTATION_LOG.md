# Implementation Log

Purpose: preserve loop memory so the next AI session knows what was done, what failed, what was fixed, and what remains.

## Log rules

- Append, do not rewrite history.
- Every meaningful code/doc/eval task must add an entry.
- Every bug fix must include symptom, root cause, affected files, exact fix, verification, and remaining risk.
- Every failed attempt must be logged, not hidden.
- Keep newest entries at the top.

## Entry template

```md
## YYYY-MM-DD HH:MM - [phase/task] short title

### Goal
- ...

### Files changed
- `path`: what changed and why

### Bug or issue fixed
- Symptom:
- Root cause:
- Fix:
- Why this fix is safe:

### Commands run
```bash
...
```

### Verification
- Tests/evals run:
- Result:
- Evidence/log path:

### Decisions
- ...

### Remaining risks / next step
- ...
```

## Entries

<!-- newest first -->
## 2026-06-02 01:05 - [release_validation] run full pre-push validation sprint and fix release blockers

### Goal
- Execute the requested pre-push validation sprint, fix any release-blocking issues surfaced by real local checks, and leave behind a truthful validation report plus fix log.

### Files changed
- `evals/experiments/defaults.py`, `evals/experiments/compare_retrievers.py`, `evals/experiments/run_generation_eval.py`, `evals/experiments/compare_pipelines.py`: added repo-default CLI paths, fixed `top_k` propagation, and aligned generation-eval defaults with the release checklist.
- `tests/test_eval_cli_defaults.py`: added regression coverage for the CLI defaults and `top_k` forwarding bug.
- `skills/zone-brain/scripts/scan_deps.py`: made the helper console-safe on Windows by removing Unicode-only banners.
- `app/schemas/query.py`, `app/api/routes_retrieval.py`, `app/api/routes_query.py`: updated the API contract to accept the release smoke payload fields and honor `use_reranker` plus `return_debug`.
- `tests/test_api_retrieve.py`, `tests/test_api_ask.py`: added regression coverage for the release smoke payloads and the explicit guardrail-disable rejection.
- `frontend/components/document_table.py`, `frontend/components/evidence_table.py`, `frontend/components/eval_dashboard.py`: replaced deprecated Streamlit dataframe sizing arguments.
- `.gitignore`: ignored generated `.zone_context.md` and `tmp_*.json` scratch artifacts.
- `README.md`, `reports/benchmark_report.md`, `reports/failure_analysis.md`, `reports/technical_report.md`, `reports/FINAL_PROJECT_HANDOFF.md`: synchronized published metrics and handoff claims with the fresh validation artifacts.
- `reports/PRE_PUSH_FIX_LOG.md`, `reports/PRE_PUSH_VALIDATION_REPORT.md`: added the requested release fix log and pre-push validation report.

### Bug or issue fixed
- Symptom: the release checklist exposed broken no-arg experiment CLIs, a generation benchmark that was not actually varying `top_k`, a Windows-only zone-brain crash, API smoke payload fields that were ignored instead of supported, and Streamlit deprecation warnings.
- Root cause: multiple small contract drifts had accumulated between the repo docs, helper tooling, and the real validation commands used during pre-push verification.
- Fix: repaired the experiment CLI defaults, forwarded `top_k` into generation evaluation, made zone-brain ASCII-safe, aligned the API schemas/routes with the smoke payloads while preserving guardrail safety, removed deprecated Streamlit args, and refreshed stale benchmark documentation from the new artifacts.
- Why this fix is safe: the changes stay within the existing architecture, are covered by new regression tests, and were immediately revalidated with the same compile/test/eval/API/frontend commands that originally exposed the problems.

### Commands run
```bash
python --version
pip --version
git status --short
git branch --show-current
python -m compileall app rag evals frontend scripts tests
pytest -q
python scripts/validate_chunks.py --chunks-dir data/chunks
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever dense --top_k 5
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5
python -m evals.experiments.compare_retrievers
python -m evals.experiments.run_generation_eval
python -m evals.experiments.compare_pipelines
python skills/zone-brain/scripts/scan_deps.py --root . --seed "eval,metric,experiment" --hops 2 --output files
docker --version
docker compose version
docker compose config
docker info
```

### Verification
- Tests/evals run:
  - `pytest -q`
  - targeted API and CLI regression tests
  - retrieval evals, compare-retrievers, generation eval, compare-pipelines
  - API smoke
  - frontend smoke
- Result:
  - `38` passing pytest tests
  - chunk validation passed for all three chunk artifacts
  - retrieval and generation reports regenerated successfully
  - API and frontend smoke checks passed
  - Docker compose config passed, but Docker daemon access remained blocked
- Evidence/log path:
  - `reports/PRE_PUSH_FIX_LOG.md`
  - `reports/PRE_PUSH_VALIDATION_REPORT.md`
  - `dist/experiments/retrieval/compare_retrievers_20260602_004255.json`
  - `dist/experiments/generation/generation_eval_20260602_004248.json`
  - `dist/experiments/pipelines/compare_pipelines_20260602_004911.json`

### Decisions
- Used zone-brain for the evaluation/API bug cluster and kept the affected zone small: `33` files from `101` total Python files.
- Kept `/ask` guardrails mandatory on the public API even while accepting the checklist field, because disabling them would conflict with the project safety rules.
- Treated the all-untracked git state as a release-process blocker to document, not as a reason to rewrite repository structure or fake a push-ready result.

### Remaining risks / next step
- Docker image build and container smoke tests still need a live daemon on this machine.
- A real Groq-backed smoke test is still skipped until `GROQ_API_KEY` is available in the environment.
- Git history now exists on `main`; continue using explicit staging and validation before any push.

## 2026-06-01 21:28 - [phase_07_evaluation_harness] build reproducible QA corpus and pipeline benchmarks

### Goal
- Expand the QA corpus, add generation and abstention metrics, run the pipeline matrix, and export benchmark plus failure-analysis reports from real artifacts.

### Files changed
- `ALWAYS_READ/02_CURRENT_PHASE.md`: moved the project into Phase 7.
- `project_context_cards/PHASE_07_EVALUATION_HARNESS.md`: recorded completed outputs, commands, and the runtime trade-off for the validation split.
- `reports/phase_07_plan.md`: added the Phase 7 execution plan.
- `reports/benchmark_report.md`: summarized the deterministic benchmark mode, dataset sizes, best config, and key metrics.
- `reports/failure_analysis.md`: summarized failure-label counts and next-step recommendations.
- `reports/phase_07_audit.md`: captured the QA-count, experiment, and secret-scan evidence.
- `reports/phase_07_completion_report.md`: documented deliverables, experiment outcomes, and remaining risks.
- `scripts/build_golden_qa.py`: added the reproducible QA-dataset builder and split writer.
- `evals/datasets/*.jsonl`: generated the Phase 7 evaluation datasets.
- `evals/metrics/generation_metrics.py`: added token-level and citation-support metrics.
- `evals/metrics/abstention_metrics.py`: added refusal and unsupported-answer metrics.
- `evals/metrics/system_metrics.py`: added latency and error-rate helpers.
- `evals/experiments/run_generation_eval.py`: added the single-config generation-eval runner with failure labels.
- `evals/experiments/compare_pipelines.py`: added the pipeline matrix runner with config deduping.
- `evals/experiments/export_report.py`: added markdown export for the benchmark and failure-analysis reports.
- `tests/test_generation_metrics.py`: added generation-metric tests.
- `tests/test_abstention_metrics.py`: added abstention-metric tests.
- `tests/test_compare_pipelines.py`: added config-surface smoke tests.

### Bug or issue fixed
- Symptom: the first full config matrix timed out before finishing on a larger validation split.
- Root cause: 216 configs over the deterministic answer stack exceeded the local runtime budget.
- Fix: reduced the validation split to a documented small tuning set and cached operationally identical configs inside `compare_pipelines.py`.
- Why this fix is safe: the golden pool still satisfies the minimum-size requirement, and the runtime trade-off is explicit in the benchmark report.

### Commands run
```bash
python -m compileall rag evals scripts tests
pytest -q
python scripts/build_golden_qa.py
python -m evals.experiments.run_generation_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/validation_qa.jsonl --retriever hybrid --top_k 5 --guardrails
python -m evals.experiments.compare_pipelines
python -m evals.experiments.export_report --input dist/experiments/pipelines/compare_pipelines_20260601_212747.json
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

### Verification
- Tests/evals run:
  - compile check
  - full pytest suite
  - dataset builder
  - single-config generation eval
  - full pipeline matrix
  - report export
- Result:
  - `pytest -q`: `27 passed`
  - `golden_qa.jsonl`: 120 rows
  - full matrix recorded 216 configs successfully
  - best config on the small validation split: `chunks_300 + bm25 + top_k 3`
  - secret scans: no matches
- Evidence/log path:
  - `dist/experiments/generation/generation_eval_20260601_211948.json`
  - `dist/experiments/pipelines/compare_pipelines_20260601_212747.json`
  - `reports/benchmark_report.md`
  - `reports/failure_analysis.md`

### Decisions
- Kept deterministic or mock evaluation mode explicit because no Groq key was available locally.
- Preserved the larger golden QA pool while shrinking the validation split for runtime feasibility.
- Counted failure labels directly from experiment records instead of writing narrative-only failure notes.

### Remaining risks / next step
- Phase 8 should surface experiment metadata through the API so the frontend can browse results without rerunning the matrix.
- The benchmark remains useful for reproducibility but is not yet a substitute for a true LLM-judged evaluation.

## 2026-06-01 21:01 - [phase_06_generation_guardrails] ship grounded answer generation with offline fallback

### Goal
- Build grounded Vietnamese answer generation with citations, citation verification, refusal guardrails, and optional Groq support that still works fully offline.

### Files changed
- `ALWAYS_READ/02_CURRENT_PHASE.md`: moved the project into Phase 6 and marked it done after the quality gate.
- `project_context_cards/PHASE_06_GENERATION_GUARDRAILS.md`: recorded completed generation outputs, commands, and Phase 7 risks.
- `reports/phase_06_plan.md`: added the Phase 6 execution plan.
- `reports/generation_behavior_report.md`: documented direct, procedural, multi-hop, unanswerable, private-data, and citation-mismatch behavior.
- `reports/phase_06_audit.md`: captured the Phase 6 quality-gate evidence and sign-off.
- `reports/phase_06_completion_report.md`: documented deliverables, offline behavior, fixes, and remaining risks.
- `rag/generation/__init__.py`: exported the generation package surface.
- `rag/generation/context_builder.py`: added context assembly, lexical augmentation over retrieval results, and support scoring.
- `rag/generation/prompt_builder.py`: added grounded prompt construction with the required JSON schema.
- `rag/generation/groq_client.py`: added the environment-driven Groq client reading only `GROQ_API_KEY` and `GROQ_MODEL`.
- `rag/generation/citation_verifier.py`: added citation membership and quote-support checks.
- `rag/generation/guardrails.py`: added refusal rules for private data, weak context, citation failure, and low-signal retrieval.
- `rag/generation/answer_generator.py`: added the orchestrator, deterministic fallback answerer, and refusal handling.
- `tests/test_prompt_builder.py`: added prompt-shape checks.
- `tests/test_citation_verifier.py`: added citation validation tests.
- `tests/test_guardrails.py`: added refusal guardrail tests.
- `tests/test_answer_generator.py`: added deterministic answer and refusal tests.

### Bug or issue fixed
- Symptom: early sample runs over-selected noisy or tangential chunks, and shell-entered Vietnamese literals were unreliable during manual checks.
- Root cause: the initial context builder trusted raw retriever ordering too much, while Windows shell input could mangle ad hoc Unicode literals.
- Fix: augmented context building with full-corpus lexical candidates, tightened evidence filtering, added numeric and monetary refusal checks, and rewrote core Vietnamese literals with explicit Unicode escapes.
- Why this fix is safe: retrieval artifacts remain unchanged, and the generation layer now behaves more predictably without depending on shell-entered Unicode correctness.

### Commands run
```bash
python -m compileall rag evals tests
pytest -q
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

### Verification
- Tests/evals run:
  - compile check
  - full pytest suite including generation tests
  - deterministic sample runs against `dev_q003`, `dev_q007`, `dev_q019`, and `dev_q020`
- Result:
  - `pytest -q`: `23 passed`
  - direct answer, procedural answer, multi-hop answer, unanswerable refusal, and private-data refusal all exercised successfully
  - `GROQ_API_KEY` not present locally, so no real Groq smoke test was run
  - secret scans: no matches
- Evidence/log path:
  - `reports/generation_behavior_report.md`
  - `reports/phase_06_audit.md`

### Decisions
- Kept the default context source aligned with Phase 5: hybrid retrieval, then augmented locally inside the context builder for generation use.
- Treated Groq as optional so the pipeline remains testable and reproducible without external credentials.
- Preferred refusal over speculation for numeric or monetary questions when the context lacks a concrete amount.

### Remaining risks / next step
- Phase 7 should quantify citation support rate, refusal accuracy, and generation behavior across a much larger dataset.
- The deterministic fallback remains more extractive than a polished LLM answerer and may include extra low-value evidence lines.

## 2026-06-01 20:41 - [phase_05_advanced_retrieval] add reranking, source scoring, and ablation benchmarks

### Goal
- Add a more production-like advanced retrieval layer with reranking, source priority, recency scoring, optional Qdrant integration, and measured ablations against the Phase 4 baseline.

### Files changed
- `ALWAYS_READ/02_CURRENT_PHASE.md`: moved the project into Phase 5 after Phase 4 handoff.
- `project_context_cards/PHASE_05_ADVANCED_RETRIEVAL.md`: recorded completed outputs, commands, and Phase 6 retrieval recommendation.
- `reports/phase_05_plan.md`: added the Phase 5 execution plan.
- `reports/advanced_retrieval_benchmark.md`: summarized the ablation results, latency, improved cases, worsened cases, and the Phase 6 recommendation.
- `reports/phase_05_audit.md`: captured the Phase 5 quality-gate evidence and sign-off.
- `reports/phase_05_completion_report.md`: documented deliverables, metrics, bug fixes, and remaining risks.
- `rag/retrieval/__init__.py`: exported advanced retrieval and reranker surfaces.
- `rag/retrieval/dense_retriever.py`: silenced noisy local sentence-transformer probing while preserving deterministic fallback behavior.
- `rag/retrieval/hybrid_retriever.py`: refactored hybrid fusion to use shared RRF utilities.
- `rag/retrieval/rrf.py`: added reusable reciprocal-rank fusion logic.
- `rag/retrieval/reranker.py`: added the reranker abstraction, deterministic lexical fallback, and optional BGE reranker hook.
- `rag/retrieval/source_priority.py`: added source-authority and recency scoring helpers using chunk plus manifest metadata.
- `rag/retrieval/qdrant_indexer.py`: added optional Qdrant indexing and search helpers.
- `rag/retrieval/advanced_hybrid_retriever.py`: added advanced hybrid scoring over rerank, hybrid, source authority, and recency signals.
- `evals/experiments/compare_retrievers.py`: added the Phase 5 ablation runner.
- `tests/test_reranker.py`: added lexical reranker behavior tests.
- `tests/test_source_priority.py`: added source-priority and recency tests.
- `tests/test_rrf.py`: added reciprocal-rank fusion tests.
- `dist/experiments/retrieval/compare_retrievers_20260601_204043.json`: wrote the advanced retrieval ablation artifact.

### Bug or issue fixed
- Symptom: the first advanced reranker configuration improved a few guide questions but pushed some regulation chunks out of the top 5 entirely.
- Root cause: rerank scores were applied too independently from the stronger baseline hybrid signal.
- Fix: blended rerank scores with normalized hybrid scores before the final advanced scoring formula was applied.
- Why this fix is safe: the advanced stack still exposes rerank, source priority, and recency signals, but it now preserves more of the baseline ranking structure.

### Commands run
```bash
python -m compileall rag evals tests
pytest -q
python -m evals.experiments.compare_retrievers --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --top_k 5
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

### Verification
- Tests/evals run:
  - compile check
  - full pytest suite including new RRF, reranker, and source-priority tests
  - advanced retrieval ablations
- Result:
  - `pytest -q`: `16 passed`
  - best config remained `hybrid`
  - advanced reranker variants slightly improved `MRR` but reduced recall and doubled latency relative to the hybrid baseline
  - secret scans: no matches
- Evidence/log path:
  - `dist/experiments/retrieval/compare_retrievers_20260601_204043.json`
  - `reports/advanced_retrieval_benchmark.md`
  - `reports/phase_05_audit.md`

### Decisions
- Kept Qdrant integration optional so local offline benchmarking remains reproducible without extra infrastructure.
- Preserved the reranker abstraction even though the current lexical fallback is not strong enough to become the default.
- Recommended the baseline hybrid retriever as the Phase 6 context-builder default.

### Remaining risks / next step
- Phase 6 should treat reranking as optional debug or experiment functionality until a stronger local reranker model is available.
- The larger Phase 7 benchmark should re-check whether reranking behaves differently once the QA set expands beyond the small dev split.

## 2026-06-01 20:30 - [phase_04_baseline_retrieval] ship offline retrieval baselines and benchmark them

### Goal
- Implement deterministic BM25, dense, and hybrid retrieval over the chunk corpus, create a grounded dev QA dataset, and publish real baseline metrics.

### Files changed
- `ALWAYS_READ/02_CURRENT_PHASE.md`: moved Phase 4 into progress and then into done after the quality gate.
- `.gitignore`: added `.env` protection rules required before later Groq and Docker work.
- `project_context_cards/PHASE_04_BASELINE_RETRIEVAL.md`: recorded completed outputs, benchmark commands, and handoff risks.
- `reports/phase_04_plan.md`: added the Phase 4 execution plan.
- `reports/retrieval_baseline.md`: summarized baseline metrics and retrieval gaps using script-generated experiment results.
- `reports/phase_04_audit.md`: captured the quality-gate evidence and audit sign-off.
- `reports/phase_04_completion_report.md`: documented deliverables, metrics, fixes, and Phase 5 readiness.
- `rag/retrieval/__init__.py`: exported the retrieval package surface.
- `rag/retrieval/base.py`: added shared retrieval types plus normalization, tokenization, and n-gram helpers.
- `rag/retrieval/index_store.py`: added JSONL-backed chunk loading and record validation.
- `rag/retrieval/bm25_retriever.py`: added a fully offline BM25 retriever.
- `rag/retrieval/dense_retriever.py`: added optional `sentence-transformers` support with a deterministic sparse semantic fallback.
- `rag/retrieval/hybrid_retriever.py`: added reciprocal-rank fusion over BM25 and dense retrieval.
- `evals/datasets/dev_qa.jsonl`: added a 20-question grounded development QA set.
- `evals/metrics/retrieval_metrics.py`: added recall, precision, MRR, and latency aggregation.
- `evals/experiments/run_retrieval_eval.py`: added the baseline retrieval benchmark CLI and experiment artifact export.
- `tests/test_retrieval_metrics.py`: added retrieval-metric unit tests.
- `tests/test_retriever.py`: added BM25, dense fallback, and hybrid retriever tests.
- `dist/experiments/retrieval/*.json`: wrote the baseline benchmark artifacts for BM25, dense, and hybrid runs.

### Bug or issue fixed
- Symptom: Windows console inspection of Vietnamese chunk text raised encoding errors while curating the dev QA set.
- Root cause: ad hoc Python inspection commands were writing through the default non-UTF-8 console encoding.
- Fix: reran QA-mining commands with `PYTHONIOENCODING=utf-8`.
- Why this fix is safe: repository artifacts were unchanged; only the shell display path was corrected for manual review.

### Commands run
```bash
python -m compileall rag evals tests
pytest -q
python scripts/validate_chunks.py --chunks-dir data/chunks
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever dense --top_k 5
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

### Verification
- Tests/evals run:
  - retrieval metric unit tests
  - retriever unit tests
  - compile check
  - chunk validation
  - BM25 retrieval eval
  - dense fallback retrieval eval
  - hybrid retrieval eval
- Result:
  - `pytest -q`: `12 passed`
  - BM25: `Recall@3 0.7222`, `Recall@5 0.8889`, `MRR 0.5917`, `Latency 2.62 ms`
  - Dense fallback: `Recall@3 0.6667`, `Recall@5 0.7778`, `MRR 0.4694`, `Latency 14.47 ms`
  - Hybrid: `Recall@3 0.8333`, `Recall@5 0.8889`, `MRR 0.5972`, `Latency 18.52 ms`
  - Secret scans: no matches
- Evidence/log path:
  - `dist/experiments/retrieval/retrieval_bm25_chunks_500_20260601_202848.json`
  - `dist/experiments/retrieval/retrieval_dense_chunks_500_20260601_202909.json`
  - `dist/experiments/retrieval/retrieval_hybrid_chunks_500_20260601_202910.json`
  - `reports/retrieval_baseline.md`
  - `reports/phase_04_audit.md`

### Decisions
- Kept the dense baseline dependency-light by preferring a local cached sentence-transformer only when available and otherwise falling back to a deterministic sparse semantic index.
- Used reciprocal-rank fusion for the baseline hybrid because it is robust to different score scales and easy to audit.
- Curated a small but grounded dev QA set now, with a documented plan to expand it substantially in Phase 7.

### Remaining risks / next step
- Phase 5 should improve the top-rank ordering for schedule and overload-registration questions that currently drift toward generic regulation chunks.
- Source authority must be introduced carefully so it supports precision without overwhelming semantic relevance.

## 2026-06-01 20:02 - [phase_03_chunking_metadata] build deterministic chunking pipeline and validated chunk corpus

### Goal
- Create section-aware chunk files with rich metadata, multiple chunk-size configs, validation scripts, and chunking tests.

### Files changed
- `ALWAYS_READ/02_CURRENT_PHASE.md`: moved into Phase 3 and then handed off to Phase 4 as ready-for-next-phase.
- `project_context_cards/PHASE_03_CHUNKING_METADATA.md`: recorded completed chunking outputs, commands, and Phase 4 risks.
- `reports/phase_03_plan.md`: added the Phase 3 execution plan.
- `reports/chunking_report.md`: summarized chunk counts, token distributions, duplicate rates, page preservation, and the default config recommendation.
- `reports/phase_03_audit.md`: recorded Phase 3 audit evidence and pass status.
- `reports/phase_03_completion_report.md`: documented deliverables, verification, bug fixes, and Phase 4 readiness.
- `rag/chunking/__init__.py`: added the chunking package surface.
- `rag/chunking/metadata_builder.py`: added config definitions and metadata helpers.
- `rag/chunking/recursive_chunker.py`: added deterministic token counting and recursive span splitting.
- `rag/chunking/section_chunker.py`: added section-aware chunk construction with overlap.
- `scripts/chunk_documents.py`: added chunk generation CLI and report writer.
- `scripts/validate_chunks.py`: added chunk validation CLI.
- `tests/test_chunker.py`: added overlap, metadata, and deterministic-ID tests.
- `tests/test_chunk_validation.py`: added validation error tests.
- `data/chunks/chunks_300.jsonl`: wrote the small chunk corpus.
- `data/chunks/chunks_500.jsonl`: wrote the medium chunk corpus.
- `data/chunks/chunks_800.jsonl`: wrote the large chunk corpus.

### Bug or issue fixed
- Symptom: some generated chunks exceeded their configured size budget after heading-path context was prepended.
- Root cause: body text was grouped using the full chunk-size budget, and heading-path tokens were added afterward.
- Fix: reserved heading-token budget before grouping body spans and regenerated all chunk files.
- Why this fix is safe: the chunker remains deterministic, keeps the required heading context, and now respects the config size ceiling in final output.

### Commands run
```bash
python -m compileall rag scripts tests
pytest -q
python scripts/chunk_documents.py --input data/processed/processed_docs.jsonl --manifest data/manifests/documents_manifest.csv --config all --output-dir data/chunks
python scripts/validate_chunks.py --chunks-dir data/chunks
rg -n "gsk_[A-Za-z0-9]{20,}" .
```

### Verification
- Tests/evals run:
  - chunker tests
  - chunk validation tests
  - end-to-end chunk generation
  - chunk validation over all three JSONL outputs
- Result:
  - 37 documents and 481 sections chunked successfully
  - `chunks_300.jsonl`: 1036 chunks
  - `chunks_500.jsonl`: 695 chunks
  - `chunks_800.jsonl`: 572 chunks
  - duplicate rates stayed below 0.002 for all configs
  - PDF page metadata preserved for all PDF-origin chunks
- Evidence/log path:
  - `data/chunks/chunks_300.jsonl`
  - `data/chunks/chunks_500.jsonl`
  - `data/chunks/chunks_800.jsonl`
  - `reports/chunking_report.md`
  - `reports/phase_03_audit.md`

### Decisions
- Used a deterministic local token estimator instead of adding a heavy tokenizer dependency.
- Preferred line-aware chunking with recursive fallback because the parsed corpus already preserves many meaningful boundaries.
- Recommended the `medium` config as the Phase 4 default starting point, while preserving `small` and `large` outputs for ablation.

### Remaining risks / next step
- Phase 4 should confirm the `medium` default with retrieval metrics rather than assumption.
- List-heavy curriculum and catalog chunks may need careful treatment in retrieval error analysis.

## 2026-06-01 19:47 - [phase_02_parsing_cleaning] build parsing pipeline and processed corpus

### Goal
- Convert the Phase 1 raw corpus into cleaned, section-aware structured text with validation and smoke tests.

### Files changed
- `ALWAYS_READ/02_CURRENT_PHASE.md`: moved into Phase 2 and then into ready-for-review after validation.
- `project_context_cards/PHASE_02_PARSING_CLEANING.md`: recorded completed outputs, commands, and next-phase risks.
- `reports/phase_02_plan.md`: added the Phase 2 execution plan.
- `reports/parsing_quality_report.md`: summarized parse success, table handling, and manual review targets.
- `reports/phase_02_audit.md`: recorded the Phase 2 quality-gate evidence.
- `reports/phase_02_completion_report.md`: documented deliverables, fixes, risks, and next-phase readiness.
- `rag/loaders/html_loader.py`: added HTML extraction with content-container selection and table handling.
- `rag/loaders/pdf_loader.py`: added page-aware PDF extraction.
- `rag/loaders/docx_loader.py`: added DOCX loader support for future documents.
- `rag/loaders/markdown_loader.py`: added text/markdown loader support for future documents.
- `rag/preprocessing/normalizer.py`: added Unicode, bullet, and whitespace normalization.
- `rag/preprocessing/cleaner.py`: added boilerplate removal and deduplication helpers.
- `rag/preprocessing/section_detector.py`: added heading inference and section construction.
- `scripts/run_phase2_processing.py`: added the end-to-end Phase 2 processing pipeline.
- `scripts/validate_processed_docs.py`: added processed JSONL validation.
- `tests/conftest.py`: added test bootstrap path handling.
- `tests/test_cleaner.py`: added cleaner smoke tests.
- `tests/test_section_detector.py`: added section-detection smoke tests.
- `data/processed/processed_docs.jsonl`: wrote the parsed corpus artifact.

### Bug or issue fixed
- Symptom: `pytest` and direct Phase 2 scripts could not import the `rag` package.
- Root cause: the repo root was not on `sys.path` during test collection or direct script execution.
- Fix: added a path bootstrap in `tests/conftest.py` and the Phase 2 scripts.
- Why this fix is safe: it only affects local import resolution and does not change parsing logic.

### Commands run
```bash
python -m pip install pypdf python-docx
python -m compileall rag scripts tests
pytest -q
python scripts/run_phase2_processing.py
python scripts/validate_processed_docs.py data/processed/processed_docs.jsonl
```

### Verification
- Tests/evals run:
  - smoke tests for cleaning and section detection
  - end-to-end processing run
  - processed JSONL validation
- Result:
  - 37 / 37 documents parsed successfully
  - 481 sections generated
  - all 5 PDFs preserved page numbers
- Evidence/log path:
  - `data/processed/processed_docs.jsonl`
  - `reports/parsing_quality_report.md`
  - `reports/phase_02_audit.md`

### Decisions
- Added DOCX and Markdown loaders now even though the current corpus only contains HTML and PDF, to keep the Phase 2 loader surface aligned with later phases.
- Preserved complex table content as readable text when faithful markdown reconstruction was not trustworthy.
- Kept PDF table extraction limitations explicit through warnings rather than overstating structure fidelity.

### Remaining risks / next step
- Phase 3 should chunk legal and handbook sections conservatively to preserve citation usefulness.
- Curriculum tables may need special chunking treatment because they flatten into line-oriented text.

## 2026-06-01 19:38 - [phase_01_data_acquisition] collect and audit Phase 1 public corpus

### Goal
- Build the Phase 1 public Vietnamese academic/policy corpus with source metadata, raw files, checksums, and repeatable collection scripts.

### Files changed
- `ALWAYS_READ/02_CURRENT_PHASE.md`: moved Phase 1 into progress, then into ready-for-review with Phase 1 handoff risks.
- `project_context_cards/PHASE_01_DATA_ACQUISITION.md`: updated status, commands run, completed outputs, and next-phase risks.
- `reports/phase_01_plan.md`: added the Phase 1 execution plan.
- `reports/data_collection_summary.md`: summarized collected sources, counts, rejections, and Phase 2 risks.
- `reports/phase_01_audit.md`: recorded evidence for the Phase 1 quality gate.
- `reports/phase_01_completion_report.md`: documented deliverables, verification, bug fixes, and next-phase recommendation.
- `scripts/phase1_sources.py`: added the curated public source catalog.
- `scripts/collect_phase1_docs.py`: added repeatable download + manifest generation for Phase 1.
- `scripts/verify_manifest.py`: added manifest integrity checks.
- `data/raw/*`: saved 37 public raw source files.
- `data/manifests/documents_manifest.csv`: wrote the Phase 1 document manifest.

### Bug or issue fixed
- Symptom: `python scripts/verify_manifest.py data/manifests/documents_manifest.csv` initially reported checksum mismatches for every HTML file.
- Root cause: the collector hashed HTML text before the final on-disk byte representation was written.
- Fix: HTML snapshots are now written as UTF-8 bytes and hashed from the same byte payload; the manifest was regenerated.
- Why this fix is safe: checksums now reflect the exact stored bytes, and the verifier passes against the regenerated files.

### Commands run
```bash
python -m compileall scripts
python scripts/collect_phase1_docs.py
python scripts/verify_manifest.py data/manifests/documents_manifest.csv
rg -n "gsk_|GROQ_API_KEY" .
```

### Verification
- Tests/evals run:
  - script compilation
  - manifest validation
  - duplicate checksum scan
  - secret scan for Groq key patterns
- Result:
  - 37 documents collected
  - 37 unique checksums
  - manifest validation passed
  - no secret matches in workspace files
- Evidence/log path:
  - `data/manifests/documents_manifest.csv`
  - `reports/data_collection_summary.md`
  - `reports/phase_01_audit.md`

### Decisions
- Kept the corpus restricted to public TDTU-controlled domains for Phase 1 rather than broadening to external universities.
- Preserved 7 outdated documents because version-aware QA and source-priority logic will need them later.
- Left most `published_at` fields blank when the source did not expose a reliable timestamp, instead of inventing dates.

### Remaining risks / next step
- Phase 2 must parse mixed HTML/PDF sources without losing headings, clause markers, or page context.
- Many HTML pages contain navigation boilerplate that will need careful cleaning.

## 2026-06-01 21:35 - [phase_08_fastapi_backend] expose retrieval and QA pipeline through FastAPI

### Goal
- Build a FastAPI service over the retrieval, grounded answering, document inventory, and experiment artifact workflows while preserving offline behavior without any Groq key.

### Files changed
- `ALWAYS_READ/02_CURRENT_PHASE.md`: moved Phase 8 into progress, then advanced the tracker to Phase 9 after completion.
- `project_context_cards/PHASE_08_FASTAPI_BACKEND.md`: updated status, commands run, completed outputs, and next-phase risks.
- `reports/phase_08_plan.md`: added the Phase 8 execution plan.
- `reports/phase_08_audit.md`: recorded the Phase 8 quality gate and secret-scan evidence.
- `reports/phase_08_completion_report.md`: documented deliverables, verification, bug fix, and handoff notes.
- `app/main.py`: created the FastAPI application and router registration.
- `app/api/routes_documents.py`: added document inventory and upload/index placeholder routes.
- `app/api/routes_query.py`: added the `/ask` grounded-answer route.
- `app/api/routes_retrieval.py`: added the `/retrieve` retrieval-only route.
- `app/api/routes_eval.py`: added retrieval/generation eval routes, experiment listing, and proper missing-artifact errors.
- `app/api/routes_health.py`: added the `/health` route.
- `app/core/config.py`: added app settings, cached stores, and shared path defaults.
- `app/core/logging.py`: added structured logging bootstrap.
- `app/core/errors.py`: added application error wrappers and the generic exception handler.
- `app/schemas/document.py`: added Pydantic schemas for document responses.
- `app/schemas/query.py`: added Pydantic schemas for retrieve and ask request/response payloads.
- `app/schemas/eval.py`: added Pydantic schemas for eval and experiment payloads.
- `tests/test_api_health.py`: added OpenAPI and missing-experiment regression coverage.
- `tests/test_api_retrieve.py`: added retrieval endpoint smoke coverage.
- `tests/test_api_ask.py`: added ask-endpoint refusal coverage.

### Bug or issue fixed
- Symptom: `/experiments/{experiment_id}` returned a normal JSON body even when the requested artifact did not exist.
- Root cause: the route returned a dictionary instead of raising an API-layer error.
- Fix: raised `AppError("Experiment not found.", status_code=404)` and added a FastAPI regression test.
- Why this fix is safe: it only changes the failure path to match HTTP semantics and does not affect successful artifact reads.

### Commands run
```bash
python -m compileall app rag evals tests
pytest -q
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

### Verification
- Tests/evals run:
  - API compile check
  - FastAPI TestClient suite
  - OpenAPI smoke verification
  - secret scans for real Groq key patterns
- Result:
  - `32 passed`
  - `/health`, `/retrieve`, `/ask`, and `/openapi.json` verified
  - missing experiment lookup now returns `404`
  - no secret matches in repository files
- Evidence/log path:
  - `reports/phase_08_audit.md`
  - `reports/phase_08_completion_report.md`

### Decisions
- Kept the API surface thin over the existing retrieval and generation modules instead of introducing another orchestration layer.
- Preserved deterministic generation fallback as the default no-key behavior so the backend remains demoable offline.
- Left document upload and index routes intentionally lightweight because the project's ingestion pipeline is file-driven today.

### Remaining risks / next step
- Phase 9 should surface real experiment artifacts clearly and separate them from any API-unavailable demo placeholders.
- Frontend evidence tables need to expose multiple retrieval scores without overwhelming the user.

## 2026-06-01 21:42 - [phase_09_frontend_debug_panel] build recruiter-facing Streamlit demo

### Goal
- Build a recruiter-friendly frontend that exposes grounded answers, evidence inspection, benchmark artifacts, and document inventory with a clean local-demo fallback when the API is unavailable.

### Files changed
- `ALWAYS_READ/02_CURRENT_PHASE.md`: advanced the tracker from Phase 9 to Phase 10 after frontend completion.
- `project_context_cards/PHASE_09_FRONTEND_DEBUG_PANEL.md`: updated status, commands run, completed outputs, and next-phase risks.
- `reports/phase_09_plan.md`: added the Phase 9 execution plan.
- `reports/phase_09_audit.md`: recorded frontend verification and secret-scan evidence.
- `reports/phase_09_completion_report.md`: documented deliverables, verification, the `top_k` bug fix, and handoff notes.
- `frontend/__init__.py`: created the frontend package entry point.
- `frontend/components/__init__.py`: created the frontend components package.
- `frontend/components/answer_view.py`: added answer, citation-card, and debug rendering.
- `frontend/components/evidence_table.py`: added the evidence inspector table and chunk previews.
- `frontend/components/eval_dashboard.py`: added experiment-matrix, metrics, latency, and failure-case rendering.
- `frontend/components/document_table.py`: added document inventory and detail rendering.
- `frontend/streamlit_app.py`: added the full four-tab Streamlit demo, dual live-or-local data access, and visual styling.
- `rag/generation/answer_generator.py`: added a request-level `top_k` override for answer generation.
- `app/api/routes_query.py`: forwarded `top_k` from `/ask` requests into the answer generator.

### Bug or issue fixed
- Symptom: the Ask UI exposed a `top_k` selector, but the backend answer path always used the default retrieval depth.
- Root cause: `AnswerGenerator.answer()` ignored request-level retrieval depth overrides.
- Fix: added an optional `top_k` argument to the generator and forwarded it from both the API route and the frontend local fallback path.
- Why this fix is safe: callers that do not pass `top_k` still use the existing default configuration.

### Commands run
```bash
python -m compileall frontend app rag evals tests
pytest -q
python -c "import frontend.components.answer_view, frontend.components.evidence_table, frontend.components.eval_dashboard, frontend.components.document_table; print('frontend_component_imports_ok')"
python -m streamlit run frontend/streamlit_app.py --server.headless true --server.port 8510
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

### Verification
- Tests/evals run:
  - frontend compile check
  - full pytest suite
  - frontend component import smoke
  - headless Streamlit startup probe
  - secret scans for real Groq key patterns
- Result:
  - `32 passed`
  - Streamlit app returned HTTP `200` during headless startup
  - all four tabs are wired to either live API or local fallback data sources
  - no secret matches in repository files
- Evidence/log path:
  - `reports/phase_09_audit.md`
  - `reports/phase_09_completion_report.md`

### Decisions
- Used the local advanced retriever for the Evidence tab so rerank and authority scores are always visible.
- Styled the Streamlit demo with a warmer editorial look rather than default gray utility visuals.
- Kept benchmark display artifact-backed only; no placeholder metrics were introduced.

### Remaining risks / next step
- Phase 10 should package both the API and frontend cleanly without forcing a Groq key at build time.
- CI must keep benchmark coverage meaningful while remaining fast enough for repeatable runs.

## 2026-06-01 21:47 - [phase_10_docker_tests_ci] package project for reproducible local runs

### Goal
- Add Docker, Compose, environment examples, and CI so the API, frontend, and retrieval smoke path can be reproduced without committing secrets.

### Files changed
- `ALWAYS_READ/02_CURRENT_PHASE.md`: advanced the tracker from Phase 10 to Phase 11 after packaging completion.
- `project_context_cards/PHASE_10_DOCKER_TESTS_CI.md`: updated status, commands run, completed outputs, and the Docker-daemon blocker.
- `reports/phase_10_plan.md`: added the Phase 10 execution plan.
- `reports/phase_10_audit.md`: recorded packaging verification and secret-scan evidence.
- `reports/phase_10_completion_report.md`: documented deliverables, validation results, and the Docker build blocker.
- `requirements.txt`: added the shared Python dependency list for Docker and CI.
- `.dockerignore`: excluded caches and environment files from image build context.
- `.env.example`: added the safe Groq placeholder env file.
- `Dockerfile`: added the shared Python image definition for the API and frontend.
- `docker-compose.yml`: added `api`, `frontend`, `qdrant`, and optional `postgres` services.
- `.github/workflows/ci.yml`: added compile, pytest, chunk-validation, retrieval-smoke, and Compose-config checks.

### Bug or issue fixed
- No repository-code bug fix was required in this phase.
- Environment blocker documented:
  - Symptom: `docker build -t vietragops:phase10 .` failed immediately.
  - Root cause: the local Docker daemon `dockerDesktopLinuxEngine` was not running or reachable.
  - Fix: no repository-side fix available; validated `docker compose config` successfully and documented the build as a local-environment blocker.
  - Why this is safe: the repository artifacts still parse correctly, and the limitation is clearly called out for follow-up verification.

### Commands run
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

### Verification
- Tests/evals run:
  - compile check
  - full pytest suite
  - chunk validation
  - retrieval smoke eval
  - Docker Compose config parse
  - secret scans for real Groq key patterns
- Result:
  - `32 passed`
  - chunk validation passed for all three chunk sets
  - retrieval smoke eval produced `dist/experiments/retrieval/retrieval_hybrid_chunks_500_20260601_214725.json`
  - `docker compose config` passed
  - Docker image build blocked only by missing local daemon
  - no secret matches in repository files
- Evidence/log path:
  - `reports/phase_10_audit.md`
  - `reports/phase_10_completion_report.md`

### Decisions
- Added a single shared image definition so Compose can run either the API or the frontend with different commands.
- Kept `.env.example` minimal to comply with the Groq-key safety rule.
- Included `qdrant` and optional `postgres` in Compose without making either a hard prerequisite for offline demo flows.

### Remaining risks / next step
- Phase 11 must keep README and demo claims aligned with the documented Docker-daemon blocker.
- Final publishing docs should clearly mark current benchmark numbers as deterministic offline results unless a real Groq run is added later.

## 2026-06-01 21:53 - [phase_11_readme_report_demo] finalize recruiter-facing docs and project handoff

### Goal
- Replace placeholder project documentation with recruiter-ready deliverables backed by real metrics, real commands, and honest limitations.

### Files changed
- `ALWAYS_READ/02_CURRENT_PHASE.md`: marked Phase 11 complete after final verification.
- `project_context_cards/PHASE_11_README_REPORT_DEMO.md`: updated status, completed outputs, commands run, and closing notes.
- `reports/phase_11_plan.md`: added the Phase 11 execution plan.
- `reports/phase_11_audit.md`: recorded final documentation audit and final secret-scan evidence.
- `reports/phase_11_completion_report.md`: documented deliverables, final verification, and remaining risks.
- `README.md`: replaced the old workspace-kit README with the actual VietRAGOps project README.
- `reports/technical_report.md`: added the project technical report.
- `reports/benchmark_report.md`: added an operational note to distinguish benchmark-best config from runtime default.
- `reports/failure_analysis.md`: added a release note to keep public claims aligned with deterministic offline evidence.
- `assets/architecture.md`: added architecture notes.
- `assets/architecture.mmd`: added the mermaid architecture source.
- `demo_video_script.md`: added the demo walkthrough script.
- `reports/FINAL_PROJECT_HANDOFF.md`: added the final runbook, limitations, TODOs, and CV bullets.

### Bug or issue fixed
- Symptom: the repository README still described the workspace kit instead of the finished VietRAGOps project.
- Root cause: the initial README predated implementation of the actual system.
- Fix: rewrote the README around the implemented pipeline, benchmark evidence, quickstart, API docs, limitations, and future work.
- Why this fix is safe: it changes documentation only and brings public-facing messaging into alignment with the shipped artifacts.

### Commands run
```bash
python -m compileall app rag evals frontend scripts tests
pytest -q
python scripts/validate_chunks.py --chunks-dir data/chunks
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5
docker compose config
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

### Verification
- Tests/evals run:
  - project-wide compile check
  - full pytest suite
  - chunk validation
  - retrieval smoke eval
  - Compose config parse
  - secret scans for real Groq key patterns
- Result:
  - `32 passed`
  - final retrieval smoke artifact written to `dist/experiments/retrieval/retrieval_hybrid_chunks_500_20260601_215307.json`
  - final retrieval smoke metrics matched the established hybrid baseline
  - no secret matches in repository files
- Evidence/log path:
  - `reports/phase_11_audit.md`
  - `reports/phase_11_completion_report.md`
  - `reports/FINAL_PROJECT_HANDOFF.md`

### Decisions
- Kept the README explicit that generation benchmark numbers are deterministic or mock-only.
- Preserved the documented Docker-daemon blocker in the README and handoff instead of overstating Docker readiness.
- Published CV-ready bullets only where a real artifact-backed metric was available.

### Remaining risks / next step
- Final publishing should include a Docker image build rerun once Docker Desktop is available.
- A future live Groq benchmark should replace or supplement the current deterministic generation evidence.
