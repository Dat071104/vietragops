# Phase 02 Plan - Parsing, Cleaning, Normalization

## Phase objectives

- Parse the 37 collected raw documents into readable structured text.
- Preserve document title, source URL, heading hierarchy, section labels, and PDF page references where available.
- Normalize whitespace, bullets, and line breaks without damaging Vietnamese diacritics.
- Produce `data/processed/processed_docs.jsonl` and a specific parsing quality report.

## Required inputs found

- `data/raw/`
- `data/manifests/documents_manifest.csv`
- `reports/data_collection_summary.md`
- `project_context_cards/PHASE_02_PARSING_CLEANING.md`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`

## Outputs to create

- `rag/loaders/`
- `rag/preprocessing/`
- `data/processed/processed_docs.jsonl`
- `reports/parsing_quality_report.md`
- `reports/phase_02_audit.md`
- `reports/phase_02_completion_report.md`

## Implementation steps

1. Implement format-aware loaders for HTML and PDF, with DOCX/TXT/Markdown hooks for later phases.
2. Implement cleaning and normalization utilities for whitespace, bullets, and boilerplate removal.
3. Implement section detection for heading hierarchy and Vietnamese legal markers.
4. Build a processing pipeline that reads the manifest and writes `processed_docs.jsonl`.
5. Add smoke tests and review parsed output samples before finalizing the report and audit.

## Commands expected to run

```bash
python -m compileall rag scripts tests
pytest -q
python scripts/run_phase2_processing.py
python scripts/validate_processed_docs.py data/processed/processed_docs.jsonl
```

## Quality gates

- At least 90 percent of collected documents parse successfully.
- Output JSONL validates line by line.
- Section headings are preserved.
- PDF page numbers are preserved where possible.
- Important tables are not silently dropped without warnings.

## Audit checklist

- Confirm required output paths exist.
- Validate `processed_docs.jsonl` schema and line count.
- Check parse success rate and warnings.
- Spot-check section headings and page references on sample documents.
- Confirm implementation log and phase card updates are completed.

## Manual check list

- Spot-check 3 parsed documents against originals.
- Check one regulation document for `Chương` / `Điều` / `Khoản` preservation.
- Check one PDF for page number fidelity.
- Check one curriculum page for bullet and table readability.
