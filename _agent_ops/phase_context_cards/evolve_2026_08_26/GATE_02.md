# Gate 02 — MarkItDown Fast Document Mode

**Status:** `TOOL PREPARED ONLY; BLOCKED BY GATE 01`
**Source:** `gates/GATE_02_MARKITDOWN_FAST_MODE.md`

## Objective

Add a narrow, local validated-document-to-Markdown adapter for PDF and only
formats that pass fixtures.

## Required Evidence

- Preserve originals; record output checksums, parser/version and quality telemetry.
- Retain current PDF loader fallback until representative comparison passes.
- Test malformed, scanned and table-heavy inputs; failure blocks candidate publish.
- Re-run existing RAG regressions.

## Prohibited Here

No public MarkItDown MCP, arbitrary `file://` input, or unproven layout-fidelity
claims.

## Preparation Note

MarkItDown 0.1.7 is locally installed in an isolated third-party venv. This is
not an app dependency or adapter implementation.

## Exit

Write `GATE_02_RESULT.md`; STOP.
