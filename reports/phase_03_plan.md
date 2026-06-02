# Phase 03 Plan - Chunking and Metadata

## Goal

Create deterministic, section-aware chunk files from `data/processed/processed_docs.jsonl` with rich metadata for retrieval, citation, and later evaluation ablations.

## Inputs found

- `rules.md`
- `ALWAYS_READ/01_PROJECT_CONTEXT.md`
- `ALWAYS_READ/02_CURRENT_PHASE.md`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `project_context_cards/PHASE_03_CHUNKING_METADATA.md`
- `data/manifests/documents_manifest.csv`
- `data/processed/processed_docs.jsonl`
- `reports/data_collection_summary.md`
- `reports/parsing_quality_report.md`
- `reports/phase_01_completion_report.md`
- `reports/phase_02_completion_report.md`
- `rag/loaders/`
- `rag/preprocessing/`

## Files to create

- `rag/chunking/__init__.py`
- `rag/chunking/section_chunker.py`
- `rag/chunking/recursive_chunker.py`
- `rag/chunking/metadata_builder.py`
- `scripts/chunk_documents.py`
- `scripts/validate_chunks.py`
- `data/chunks/chunks_300.jsonl`
- `data/chunks/chunks_500.jsonl`
- `data/chunks/chunks_800.jsonl`
- `reports/chunking_report.md`
- `reports/phase_03_audit.md`
- `reports/phase_03_completion_report.md`
- `tests/test_chunker.py`
- `tests/test_chunk_validation.py`

## Chunking strategy

- Load processed docs and Phase 1 manifest metadata together.
- Preserve each parsed section as the primary chunking boundary.
- Keep short sections intact as a single chunk.
- For long sections, use a recursive fallback that prefers legal and structured boundaries:
  - `Chương`
  - `Mục`
  - `Điều`
  - `Khoản`
  - numbered clauses
  - paragraph and sentence boundaries
- Prepend heading path into chunk text for retrieval context.
- Preserve `page_start` and `page_end` from source sections.
- Generate deterministic `chunk_id` values from `section_id` and chunk index.
- Use a deterministic local token estimator without heavy dependencies.

## Validation strategy

- Validate chunk JSONL schema and required metadata.
- Check for empty chunks, missing identifiers, missing source URLs, missing heading paths, and non-positive token counts.
- Enforce unique `chunk_id` values.
- Compute duplicate text rate and flag abnormal chunk lengths.
- Confirm PDF-origin chunks retain page metadata where available.

## Commands planned

```bash
python -m compileall rag scripts tests
pytest -q
python scripts/chunk_documents.py --input data/processed/processed_docs.jsonl --manifest data/manifests/documents_manifest.csv --config all --output-dir data/chunks
python scripts/validate_chunks.py --chunks-dir data/chunks
```

## Risks

- Flattened curriculum tables may inflate duplicate text or create weak chunk boundaries.
- Some hub pages are list-heavy and may produce low-information chunks unless handled conservatively.
- Overlap can accidentally create near-duplicates if segment boundaries are too small.

## Manual checks

- Inspect 10 random chunks from `chunks_500.jsonl`.
- Check one long regulation chunk sequence for clause-preserving boundaries.
- Check one PDF chunk sequence for page metadata continuity.
- Check one curriculum chunk for table readability after chunking.
