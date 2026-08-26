# Gate 00 — Baseline Freeze and Safe Restructure

**Status:** `NEXT / NOT STARTED`
**Source:** `gates/GATE_00_BASELINE_AND_RESTRUCTURE.md`

## Objective

Create a reproducible baseline without changing scientific or product behavior.

## Required Evidence

- Canonical Git root, commit, working tree and corpus/index counts recorded.
- Deterministic compile/test/retrieval smoke actually run; failures recorded.
- Machine-readable baseline manifest records hashes, commands, provider mode and warnings.
- Safe module-boundary work uses compatibility/tests, not a rewrite.

## Prohibited Here

No MarkItDown integration, Firecrawl, alignment method, production GCP, or paper
writing. Setup completed before this gate is not a baseline result.

## Exit

Write `GATE_00_RESULT.md`; STOP. Only PASS permits Gate 01.
