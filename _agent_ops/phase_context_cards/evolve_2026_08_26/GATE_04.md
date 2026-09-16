# Gate 04 — Version-Aware RAGOps

**Status:** `PASS (2026-08-27, uncommitted -- no commit authorized this session)`
**Source:** `gates/GATE_04_VERSION_AWARE_RAGOPS.md`
**Result:** `gates/results/GATE_04_RESULT.md`

## Objective

Resolve every retrieved chunk to source, source version, index version and
authority/freshness state; emit supported, insufficient, stale and conflict
states deterministically.

## Required Evidence

- Retired sources exclude normally; conflicts are explicit rather than silently
  chosen; traces show query/retrieval/ranking/source/index/provider/citations.
- Citation verification remains separate from answer correctness.
- Versioned fixtures and unchanged-version baseline regression threshold pass.

## Exit

Write `GATE_04_RESULT.md`; STOP.
