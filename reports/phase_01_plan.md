# Phase 01 Plan - Data Acquisition

## Phase objectives

- Collect at least 30 public Vietnamese academic and policy documents suitable for VietRAGOps.
- Prioritize official TDTU academic, regulation, curriculum, and guidance sources.
- Save raw source files locally and generate a manifest with complete metadata and SHA256 checksums.
- Produce a specific data collection summary, audit, and completion report for this phase.

## Required inputs found

- `rules.md`
- `ALWAYS_READ/01_PROJECT_CONTEXT.md`
- `ALWAYS_READ/02_CURRENT_PHASE.md`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `project_context_cards/PHASE_01_DATA_ACQUISITION.md`
- `source_materials/Pasted text(11).txt`

## Outputs to create

- `data/raw/`
- `data/manifests/documents_manifest.csv`
- `reports/data_collection_summary.md`
- `reports/phase_01_audit.md`
- `reports/phase_01_completion_report.md`

## Implementation steps

1. Curate official public source URLs from TDTU and, if needed, additional official Vietnamese academic/policy domains.
2. Implement a repeatable collection script that downloads or snapshots raw documents into `data/raw/`.
3. Extract metadata for each source and classify `domain`, `authority_level`, and `status`.
4. Compute SHA256 checksums for every local file and write `data/manifests/documents_manifest.csv`.
5. Review duplicates, stale sources, and manual-review cases; document them in the summary report.

## Commands expected to run

```bash
python --version
python scripts/collect_phase1_docs.py
python scripts/verify_manifest.py data/manifests/documents_manifest.csv
python -m compileall scripts
```

## Quality gates

- At least 30 public documents collected, or a documented blocker with expansion plan.
- Every manifest row has `source_url`, `file_path`, and `checksum`.
- No behind-login or private sources included.
- Manifest parses successfully as CSV.
- Reports are specific and consistent with collected files.

## Audit checklist

- Confirm required output paths exist.
- Validate manifest headers and row count.
- Check that each file path exists on disk.
- Recompute sample checksums and compare with the manifest.
- Verify duplicates and manual-review cases are explicitly listed.
- Confirm implementation log and phase card updates are completed.

## Manual check list

- Spot-check 5 source URLs in a browser.
- Verify no collected source requires login.
- Verify official pages are still current enough for academic-policy usage.
- Review at least 5 `status` labels for `active` vs `outdated`.
