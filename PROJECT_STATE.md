# VietRAGOps Project State

## Current gate

Gate 00 is complete with status `PASS` for the reproducible offline baseline
and safe-boundary decision. No Gate 01 or later work was performed.

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

## Authoritative records

- Gate result: `gates/results/GATE_00_RESULT.md`.
- Baseline manifest: `gates/baselines/GATE_00_BASELINE.json`.
- Existing decision record: `_agent_ops/DECISION_LOG.md`.
- No duplicate `DECISIONS.md` was created; the Gate 00 boundary decision is
  recorded in the baseline manifest and result and maps to the existing
  `_agent_ops/DECISION_LOG.md`.

## Current evidence limits

- The offline BM25 smoke is reproducible against the recorded chunks and QA
  hashes, but its timestamp and measured latency are run-specific.
- `python -m pytest -q` could not run because the available interpreter lacks
  `pytest`; this is recorded as a known limitation, not masked or repaired in
  Gate 00.
- No persisted vector/index artifact exists. Runtime retrieval loads
  `data/chunks/chunks_500.jsonl` into an in-memory `ChunkIndexStore`.

## Next allowed action

Only a new explicit session may begin Gate 01, after independently re-verifying
the baseline identity and Gate 00 PASS result. This session stops here.
