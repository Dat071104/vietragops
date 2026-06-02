# Phase 1 - Data acquisition

## Phase goal

Collect public Vietnamese academic/policy documents with source metadata.

## Required inputs

- Current project context.
- Implementation log.
- Relevant previous phase outputs.

## Expected outputs

data/raw, data/manifests/documents_manifest.csv, reports/data_collection_summary.md

## Quality gate

At least 30 public docs, each with source URL, checksum, authority level, and status.

## Do not do

- Do not skip logging.
- Do not fake metrics.
- Do not expand scope without recording a decision.
- Do not read unrelated code files unless zone-brain identifies them.

## Current status

done

## Handoff notes

- Completed files:
  - `data/raw/`
  - `data/manifests/documents_manifest.csv`
  - `reports/data_collection_summary.md`
  - `reports/phase_01_plan.md`
  - `reports/phase_01_audit.md`
  - `reports/phase_01_completion_report.md`
  - `scripts/phase1_sources.py`
  - `scripts/collect_phase1_docs.py`
  - `scripts/verify_manifest.py`
- Commands run:
  - `python -m compileall scripts`
  - `python scripts/collect_phase1_docs.py`
  - `python scripts/verify_manifest.py data/manifests/documents_manifest.csv`
  - `rg -n "gsk_|GROQ_API_KEY" .`
- Blockers:
  - None for Phase 1 completion.
- Next phase risks:
  - HTML pages contain navigation and promotional boilerplate that must be removed safely.
  - Most pages do not expose reliable `published_at` metadata.
  - PDF parsing will need page-aware extraction and careful table handling.
