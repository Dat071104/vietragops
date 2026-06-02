# Phase 2 - Parsing, cleaning, normalization

## Phase goal

Convert raw files into readable structured text while preserving headings, pages, sections, and tables.

## Required inputs

- Current project context.
- Implementation log.
- Relevant previous phase outputs.

## Expected outputs

data/processed/processed_docs.jsonl, reports/parsing_quality_report.md

## Quality gate

90 percent plus documents parse into readable text with headings and page numbers where available.

## Do not do

- Do not skip logging.
- Do not fake metrics.
- Do not expand scope without recording a decision.
- Do not read unrelated code files unless zone-brain identifies them.

## Current status

done

## Handoff notes

- Completed files:
  - `rag/loaders/html_loader.py`
  - `rag/loaders/pdf_loader.py`
  - `rag/loaders/docx_loader.py`
  - `rag/loaders/markdown_loader.py`
  - `rag/preprocessing/cleaner.py`
  - `rag/preprocessing/normalizer.py`
  - `rag/preprocessing/section_detector.py`
  - `data/processed/processed_docs.jsonl`
  - `reports/parsing_quality_report.md`
  - `reports/phase_02_plan.md`
  - `reports/phase_02_audit.md`
  - `reports/phase_02_completion_report.md`
  - `scripts/run_phase2_processing.py`
  - `scripts/validate_processed_docs.py`
  - `tests/test_cleaner.py`
  - `tests/test_section_detector.py`
- Commands run:
  - `python -m pip install pypdf python-docx`
  - `python -m compileall rag scripts tests`
  - `pytest -q`
  - `python scripts/run_phase2_processing.py`
  - `python scripts/validate_processed_docs.py data/processed/processed_docs.jsonl`
- Blockers:
  - None for Phase 2 completion.
- Next phase risks:
  - Curriculum tables are preserved as readable text but not always as compact markdown tables.
  - PDF table extraction remains approximate and is flagged with warnings.
  - Link-heavy hub pages may require conservative chunking choices in Phase 3.
