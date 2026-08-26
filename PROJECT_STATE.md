# VietRAGOps Project State

## Current gate

Gate 01 is complete with status `PASS` for the governed local document
lifecycle (validated intake, durable source/version registry, candidate-only
processing, reviewed atomic publish/retire/rollback). Gate 00 (reproducible
offline baseline and safe-boundary decision) is also `PASS`. No Gate 02 or
later work was performed.

## Baseline identity

- Baseline snapshot: `main` at `e710230a7a99c03c2d8591518ee7139f19fb89ba`
  plus the exact pre-existing dirty overlay recorded in
  `gates/baselines/GATE_00_BASELINE.json`.
- Overlay identity SHA-256:
  `90b7b0a60dc0680d84c49c76903b3af553971469e63e7326c0b5708f04bc9bcd`.
- Baseline evidence commits: `bb10a0e` plus the factual snapshot-count
  correction `b76cf41`.
- The working tree intentionally remains dirty with the pre-existing overlay;
  Gate 00 did not reset, restore, clean, stash, or stage it.

## Gate 00 decision

No application module boundary change is needed now. Existing loaders,
preprocessing, chunking, retrieval/index storage, generation/provider routing,
evaluation, and operations records have identifiable owners and call paths. No
empty target folders, duplicate wrappers, or behavior-changing moves were
created.

The compact responsibility table and evidence are in the baseline manifest.

## Gate 01 decision and evidence

Governed lifecycle added under `rag/lifecycle/` (stdlib-only: `sqlite3`,
`hashlib`, `uuid`, `csv`, `json`, `os.replace`-based atomic writes). No new
dependency, server, or database product. The existing 37-document
`data/manifests/documents_manifest.csv` / `data/chunks/chunks_500.jsonl`
corpus was preserved as-is, not migrated into the registry -- the registry
only tracks documents ingested through the new `/documents/upload` ->
review -> publish flow from this Gate forward. Full detail, phase-by-phase
evidence, and the acceptance checklist are in `gates/results/GATE_01_RESULT.md`.

## Authoritative records

- Gate 00 result: `gates/results/GATE_00_RESULT.md`.
- Gate 01 result: `gates/results/GATE_01_RESULT.md`.
- Baseline manifests: `gates/baselines/GATE_00_BASELINE.json`,
  `gates/baselines/GATE_01_RETRIEVAL_SMOKE.json` (post-Gate-01 regression smoke;
  identical metrics to `GATE_00_RETRIEVAL_SMOKE.json`, proving the live corpus
  and retrieval quality were not altered).
- Existing decision record: `_agent_ops/DECISION_LOG.md`.
- No duplicate `DECISIONS.md` was created; the Gate 00 and Gate 01 decisions
  are recorded in their respective results/manifests and map to the existing
  `_agent_ops/DECISION_LOG.md`.

## Current evidence limits

- The offline BM25 smoke is reproducible against the recorded chunks and QA
  hashes, but its timestamp and measured latency are run-specific.
- Gate 00 reported `python -m pytest -q` as unavailable because it was run
  with `C:\Python314\python.exe`, which has no `pytest` installed. The
  project's own `.venv\Scripts\python.exe` has pytest 9.0.3 and the full
  suite passes there (134/134 after Gate 01). Use `.venv/Scripts/python.exe`
  going forward; this is not a retroactive correction of the Gate 00 result.
- No persisted vector/index artifact exists. Runtime retrieval loads
  `data/chunks/chunks_500.jsonl` into an in-memory `ChunkIndexStore`; Gate 01
  did not change this, only how that file (and the manifest) get written.
- The pre-existing 37-document corpus has no version history or rollback path
  in the new registry (see Gate 01 decision above).
- `LifecycleService.publish`/`retire`/`rollback` assume a single writer; no
  cross-process lock exists yet.

## Next allowed action

Only a new explicit session may begin Gate 02, after independently
re-verifying the baseline/HEAD identity and the Gate 01 PASS result. This
session stops here.
