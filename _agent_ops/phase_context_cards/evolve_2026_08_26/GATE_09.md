# Gate 09 — Full Evaluation and GCP Deployment

**Status:** `BLOCKED BY GATE 08 AND FROZEN EVIDENCE`  
**Source:** `gates/GATE_09_FULL_EVAL_AND_GCP_DEPLOY.md`

## Objective

Freeze full scientific/product evidence, then deploy the approved flagship with
authenticated MCP and rollback proof.

## Controls

Use Secret Manager; record image digest and Cloud Run revision; keep research
provider-pinned. Prove product E2E, Firecrawl/MarkItDown/version-aware flows,
failure handling, persistence and revision rollback. Local Ollama is not assumed
to exist in Cloud Run.

## Exit

Write `GATE_09_RESULT.md`; only PASS permits Gate 10.
