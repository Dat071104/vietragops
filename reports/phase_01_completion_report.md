# Phase 01 Completion Report

## Phase summary

Phase 1 built the initial public corpus for VietRAGOps by collecting 37 Vietnamese academic and policy documents from official TDTU and TDTU faculty/admission sources. The phase also added a repeatable collection script, a manifest verifier, and a documented summary/audit trail.

## Completed deliverables

- `data/raw/` with 37 downloaded raw source files
- `data/manifests/documents_manifest.csv`
- `reports/data_collection_summary.md`
- `reports/phase_01_plan.md`
- `reports/phase_01_audit.md`
- `reports/phase_01_completion_report.md`
- `scripts/phase1_sources.py`
- `scripts/collect_phase1_docs.py`
- `scripts/verify_manifest.py`

## Files created or modified

- `ALWAYS_READ/02_CURRENT_PHASE.md`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `project_context_cards/PHASE_01_DATA_ACQUISITION.md`
- `reports/phase_01_plan.md`
- `reports/data_collection_summary.md`
- `reports/phase_01_audit.md`
- `reports/phase_01_completion_report.md`
- `scripts/phase1_sources.py`
- `scripts/collect_phase1_docs.py`
- `scripts/verify_manifest.py`
- `data/raw/*`
- `data/manifests/documents_manifest.csv`

## Scripts and commands run

```bash
python -m compileall scripts
python scripts/collect_phase1_docs.py
python scripts/verify_manifest.py data/manifests/documents_manifest.csv
rg -n "gsk_|GROQ_API_KEY" .
```

## Tests and verification run

- Script compilation: passed
- Manifest validation: passed
- Duplicate checksum check: passed with 0 duplicate groups
- Secret scan in workspace: no matches

## Metrics produced

- Documents collected: 37
- Unique checksum groups: 37
- Authority split: 31 official, 6 faculty
- Status split: 30 active, 7 outdated

## Bugs found and fixed

- Symptom: manifest verification reported checksum mismatches for every HTML file.
- Root cause: the collector originally hashed HTML text before disk-write normalization, so saved bytes and manifest hashes diverged.
- Fix: HTML files are now written as UTF-8 bytes and hashed from the same byte payload.
- Additional issue: a false-negative verification run occurred when collection and verification were launched in parallel; verification was rerun sequentially after collection completed.

## Unresolved risks

- 28 documents still lack reliable `published_at` metadata.
- Later parsing work must remove boilerplate carefully to avoid dropping section labels or instructions.
- The corpus includes both active and outdated rules, so later retrieval/generation stages must preserve status metadata.

## Manual checks recommended

- Spot-check 5 source URLs manually.
- Verify that the 7 outdated documents are still worth keeping for version-aware QA and not better removed.
- Confirm the raw HTML snapshots render the key content sections expected for later parsing.

## Readiness for next phase

- Phase 1 is ready for Phase 2.
- Required Phase 1 quality gate passed.

## Exact next phase recommendation

Proceed to `PHASE_02_PARSING_CLEANING.md` and implement HTML/PDF loaders plus section-aware cleaning while preserving Vietnamese diacritics, page references, and legal headings.
