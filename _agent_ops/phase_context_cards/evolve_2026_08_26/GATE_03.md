# Gate 03 — Firecrawl Web Discovery and Import

**Status:** `TOOL PREPARED ONLY; BLOCKED BY GATE 02`  
**Source:** `gates/GATE_03_FIRECRAWL_WEB_IMPORT.md`

## Objective

Provide admin-controlled, bounded web import into the reviewed candidate-source
lifecycle.

## Secret Stop Gate

Before the first authenticated call, use only ignored
`VietRagOps/.env.firecrawl.local` containing `FIRECRAWL_API_KEY=`. Stop with
`WAITING_FOR_USER_SECRET`; do not look for another project/account key. Resume
only after the owner explicitly confirms a valid local key.

## Required Controls

Block private/loopback/link-local/metadata targets. Enforce URL/domain/content
type/page/byte/depth/time budgets; retain URL/timestamp/provenance; keep imports
as candidates; record 429/credit failures separately.

## Prohibited Here

No public arbitrary crawl, auto-publish, or authority claim based only on crawler
output.

## Preparation Note

Firecrawl source and Compose configuration are prepared but no service or
authenticated request has started.

## Exit

Write `GATE_03_RESULT.md`; STOP.
