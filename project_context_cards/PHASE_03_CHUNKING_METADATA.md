# Phase 3 - Chunking and metadata

## Phase goal

Create section-aware chunks with rich metadata and multiple chunk-size configs.

## Required inputs

- Current project context.
- Implementation log.
- Relevant previous phase outputs.

## Expected outputs

data/chunks/chunks_300.jsonl, chunks_500.jsonl, chunks_800.jsonl, reports/chunking_report.md

## Quality gate

No empty chunks, metadata complete, chunk stats reported, duplicate rate checked.

## Do not do

- Do not skip logging.
- Do not fake metrics.
- Do not expand scope without recording a decision.
- Do not read unrelated code files unless zone-brain identifies them.

## Current status

done

## Handoff notes

- Completed files:
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
  - `reports/phase_03_plan.md`
  - `reports/phase_03_audit.md`
  - `reports/phase_03_completion_report.md`
  - `tests/test_chunker.py`
  - `tests/test_chunk_validation.py`
- Commands run:
  - `python -m compileall rag scripts tests`
  - `pytest -q`
  - `python scripts/chunk_documents.py --input data/processed/processed_docs.jsonl --manifest data/manifests/documents_manifest.csv --config all --output-dir data/chunks`
  - `python scripts/validate_chunks.py --chunks-dir data/chunks`
  - `rg -n "gsk_[A-Za-z0-9]{20,}" .`
- Blockers:
  - None for Phase 3 completion.
- Next phase risks:
  - List-heavy curriculum and catalog pages may produce weaker retrieval signals than regulation chunks.
  - Table-heavy curriculum chunks remain readable but not fully structured.
  - Phase 4 should validate the `medium` config recommendation against retrieval metrics instead of assuming it.
