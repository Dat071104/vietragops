# Gate 01 — Governed Document Lifecycle

**Status:** `BLOCKED BY GATE 00`
**Source:** `gates/GATE_01_DOCUMENT_LIFECYCLE.md`

## Objective

Replace upload-only behavior with validated intake, durable source/version
records, candidate processing, reviewed atomic publish/retire, and rollback.

## Non-Negotiable Tests

- Unsafe path/name, unsupported/oversized input, and duplicate behavior are
  deterministic and tested.
- Preserve original artifacts and source/version/provenance.
- Candidate content cannot change live RAG before review/publish.
- Publish/retire/rollback and existing RAG regressions are proven.

## Prohibited Here

No auto-publish, arbitrary caller filesystem paths, Firecrawl dependency, or
infrastructure migration for appearance.

## Exit

Write `GATE_01_RESULT.md`; STOP.
