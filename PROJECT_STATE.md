# VietRAGOps Project State

## Current gate

Gate 03 is `WAITING_FOR_USER_SECRET`: a bounded Firecrawl web
search/scrape adapter, URL/domain/private-network safety layer, and
candidate/provenance/recrawl-diff integration with the existing
lifecycle are implemented and fully tested offline (79 new tests, mocked
httpx transport only). No authenticated Firecrawl call has been made and
none will be until a user, in an explicit session, confirms the local
`.env.firecrawl.local` key is filled in. See
`gates/results/GATE_03_RESULT.md`. Gate 00, Gate 01, and Gate 02 remain
`PASS`.

## Baseline identity

- Baseline snapshot: `main` at `e710230a7a99c03c2d8591518ee7139f19fb89ba`
  plus the exact pre-existing dirty overlay recorded in
  `gates/baselines/GATE_00_BASELINE.json`.
- Overlay identity SHA-256:
  `90b7b0a60dc0680d84c49c76903b3af553971469e63e7326c0b5708f04bc9bcd`.
- Baseline evidence commits: `bb10a0e` plus the factual snapshot-count
  correction `b76cf41`.
- Gate 01 result commit `df5d84c` was the reachable prerequisite baseline for
  this Gate. Gate 02 commits are `e44e012`, `c36f905`, `3c1cff0`, `bc3b96c`,
  and `03249ce`; they contain only the pinned runtime, local adapter,
  candidate integration/fixtures, and QA evidence described below.
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
- Gate 02 result: `gates/results/GATE_02_RESULT.md`.
- Gate 02 evidence: `gates/baselines/GATE_02_EXTRACTION_QA.json` and
  `gates/baselines/GATE_02_RETRIEVAL_SMOKE.json`.

## Gate 02 decision and evidence

The candidate path is `immutable original -> local MarkItDown -> atomic
candidate/version_id/canonical.md -> existing Markdown loader -> existing
section builder -> existing chunker -> candidate processed/chunks artifacts`.
`extraction.json` records parser/provenance, status, duration, original and
canonical SHA-256 values, character/section/table counts, and warnings. The
registry locates `canonical.md` and `extraction.json` with the backwards-
compatible `candidate_canonical_path` and `candidate_extraction_path` fields.

PDF and DOCX are the enabled MarkItDown candidate formats. The existing HTML,
Markdown, and text lifecycle paths remain available through their existing
loaders. PPTX and XLSX are unsupported/rejected in this Gate. PDF defaults to
MarkItDown; `VIETRAGOPS_CANDIDATE_PDF_PARSER=pypdf` is the explicit
server-owned fallback policy. A failed MarkItDown conversion is recorded as
failed and is never silently retried through pypdf.

Representative local fixtures passed factual extraction QA: normal PDF and
table-heavy PDF converted successfully; the no-text PDF, malformed PDF, and
malformed DOCX remained failed/unusable; the DOCX fixture converted
successfully. No layout or visual-fidelity claim is made.

The committed existing corpus, processed documents, manifests, chunk files,
and QA input hashes remain identical to the Gate 00 baseline. The Gate 02
offline BM25 smoke has 695 chunks and 20 queries with recall@5 `0.8889`, MRR
`0.5917`, and precision@5 `0.1889`, matching Gate 01's metrics.

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
- The exact bare `pytest -q` command remains blocked by this runner's denied
  system temp/cache directories; the equivalent project-interpreter run with
  an exact workspace basetemp and cache plugin disabled passed 157/157.
- The symlink test exercises the real rejection branch when the host permits
  symlink creation and a deterministic branch simulation when it does not.
- Gate 02 fixture comparisons are extraction measures only; they do not prove
  layout fidelity, OCR quality, or production readiness.

## Gate 03 decision and evidence

The web import path is `admin CLI (scripts/web_import.py) -> web_safety
(HTTPS-only, blocked hostnames, request-time private/loopback/link-local/
metadata rejection, server-owned default-deny domain allowlist) ->
rag/ingestion/firecrawl.py (bounded search_preview/scrape_markdown,
typed outcome classes, capped retries) -> rag/lifecycle/web_pipeline.py
(candidate build reusing the existing Markdown loader/section
builder/chunker, extraction record in the same schema pipeline.py uses)
-> existing LifecycleService review/publish/rollback -> candidate-only
processed/chunks artifacts`. There is no FastAPI route for this: the
application has no admin authorization to gate a public endpoint, so the
CLI is the only interface. Document identity is
`web-{sha256(canonical_url)[:24]}`, never the title, so recrawl lookups
are idempotent and stable; unchanged content records a no-op event, and
changed content creates a new still-candidate version linked via
`prior_version_id` plus a deterministic (no-LLM) section diff in the new
`web_provenance`/`acquisition_attempts` SQLite tables.

No authenticated Firecrawl call has been made. `.env.firecrawl.local` was
never opened; only its `.gitignore` filename coverage was checked. 79 new
tests (17 adapter, 40 safety, 14 import, 8 recrawl/diff) all mock the
httpx transport. Full offline regression (compile, 236/236 tests,
chunk/processed-doc/manifest validation, offline BM25 smoke) is
bit-for-bit identical to Gate 02. Full detail, phase-by-phase evidence,
two read-only-audit findings and fixes, and the acceptance checklist are
in `gates/results/GATE_03_RESULT.md`.

## Next allowed action

Resume Gate 03 Phase 3.5 (the authenticated live proof) only in a new
session where the user explicitly confirms, in that session, that
`.env.firecrawl.local` is filled in locally and that they will not send
its value. Gate 04 must not begin before Gate 03 reaches a final PASS.
This session stops here.
