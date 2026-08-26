# Gate 02 Result

Status: PASS

## Commit / tree state

- Gate 01 result commit `df5d84c232316c4b0068dbd45661ab20d0168a60` was
  reachable before editing. The six tracked dirty-overlay paths and 38
  nonignored untracked paths matched the recorded inventory; the recorded
  SHA-256 of modified `rag/generation/groq_client.py` remained
  `b48cf46c4381176b154ea99ee2157315934edb7b340bbc4a86791cc59e99f68f`.
- The Git index was empty before the first Gate 02 edit and after every commit.
  The pre-existing overlay was not normalized, staged, reset, restored, cleaned,
  stashed, amended, rebased, or pushed.
- Commits after Gate 01 were understood before editing: `7d54d8a` was the
  non-behavioral Gate 02 prompt handoff. Gate 02 work then produced
  `e44e012`, `c36f905`, `3c1cff0`, `bc3b96c`, and `03249ce`. This final
  result/state pair is committed separately; its exact commit is the commit
  containing this file and `PROJECT_STATE.md`.

## Phases completed

- Phase 2.0 — pinned the application dependency
  `markitdown[pdf,docx]==0.1.7`; verified the external provenance checkout and
  the app runtime.
- Phase 2.1 — added the narrow local adapter and boundary tests. The adapter
  accepts only an absolute server-owned original `Path` or a named binary
  stream whose origin re-resolves below the configured lifecycle originals
  directory. It rejects caller path strings, URI-like inputs, symlinks/path
  escape, unverified streams, and non-text converter output. It calls only
  `convert_local` or `convert_stream` with `enable_plugins=False` and no URL,
  endpoint, client, OCR, cloud, or plugin arguments. It makes no writes.
- Phase 2.2 — made MarkItDown the default PDF candidate parser, added PDF
  structural validation, atomic `canonical.md` and `extraction.json`, durable
  checksum/telemetry fields, registry migration, and review/publish/rollback
  integrity guards. The existing Markdown loader, section builder, and
  chunker remain downstream of canonical Markdown.
- Phase 2.3 — enabled DOCX because its real local fixture passed. The existing
  DOCX loader remains available for factual comparison. PPTX and XLSX are not
  enabled and are rejected by the intake allowlist.
- Phase 2.4 — completed fixture comparison, full regression, corpus validation,
  and the offline retrieval-smoke comparison.

## Files changed

- `e44e012 build(gate-02): add local markitdown runtime`
  - `requirements.txt`
- `c36f905 feat(gate-02): add local markdown adapter`
  - `rag/ingestion/__init__.py`
  - `rag/ingestion/markitdown.py`
  - `tests/test_markitdown_adapter.py`
- `3c1cff0 fix(gate-02): classify invalid conversion output`
  - `rag/ingestion/markitdown.py`
  - `tests/test_markitdown_adapter.py`
- `bc3b96c feat(gate-02): convert pdf candidates to markdown`
  - `app/api/routes_documents.py`
  - `app/core/config.py`
  - `app/schemas/document.py`
  - `rag/lifecycle/extraction.py`
  - `rag/lifecycle/pipeline.py`
  - `rag/lifecycle/registry.py`
  - `rag/lifecycle/service.py`
  - `tests/fixtures/gate02/docx_policy.docx`
  - `tests/fixtures/gate02/fixture_manifest.json`
  - `tests/fixtures/gate02/malformed.docx`
  - `tests/fixtures/gate02/malformed.pdf`
  - `tests/fixtures/gate02/normal.pdf`
  - `tests/fixtures/gate02/scanned_no_text.pdf`
  - `tests/fixtures/gate02/table_heavy.pdf`
  - `tests/test_gate02_markdown_pipeline.py`
  - `tests/test_lifecycle_pipeline.py`
  - `tests/test_lifecycle_registry.py`
  - `tests/test_markitdown_adapter.py`
- `03249ce test(gate-02): verify markdown extraction quality`
  - `gates/baselines/GATE_02_EXTRACTION_QA.json`
  - `gates/baselines/GATE_02_RETRIEVAL_SMOKE.json`
- Final result/state commit
  - `PROJECT_STATE.md`
  - `gates/results/GATE_02_RESULT.md`

## Runtime and parser policy proof

- External checkout: `external_tools/markitdown`, clean status, revision
  `9dc0d6579b8739c9d0671ff205e071e3053c7df1`, isolated preparation/runtime
  version `0.1.7`. It was not imported through `PYTHONPATH`, modified, or
  staged.
- Application runtime: Python `3.13.9`, installed MarkItDown `0.1.7`, local
  `MarkItDown.convert_local` and `MarkItDown.convert_stream` available,
  `MarkItDown(enable_plugins=False)` reports plugins disabled and no LLM client,
  and `pip check` reports `No broken requirements found.`
- `requirements.txt` contains one explicit line:
  `markitdown[pdf,docx]==0.1.7`. No PPTX/XLSX extras were requested. The
  normal-index install paused twice; an approved bounded escalated retry
  completed the same pinned install. No provider or conversion request was
  made during installation.
- Default candidate policy is server-owned MarkItDown for PDF and DOCX. The
  existing pypdf loader remains selectable only by
  `VIETRAGOPS_CANDIDATE_PDF_PARSER=pypdf`, records
  `parser_policy=pypdf_explicit_fallback` and the actual pypdf version, and
  does not expose parser choice to the upload caller. A failed MarkItDown
  conversion is failed; it is never silently retried by pypdf.

## Canonical Markdown, telemetry, and lifecycle isolation

- For a validated PDF/DOCX original, the candidate version directory contains
  atomic `canonical.md`, `processed.jsonl`, `chunks_500.jsonl`, and
  `extraction.json` files when applicable. The registry has the backwards-
  compatible `candidate_canonical_path` and `candidate_extraction_path` fields;
  the migration is tested against a Gate 01-shaped registry.
- `extraction.json` records parser name/version/provenance and policy,
  conversion status/duration from a monotonic clock, original and canonical
  SHA-256 values, canonical character count, section count, deterministic table
  count, the table-count rule, parse status, and safe warnings. The original is
  retained under the immutable lifecycle originals directory and is rehashed
  during review/publish/rollback integrity checks.
- Candidate writes stay under the server-owned version directory. Before
  review/publish/rollback, the service verifies the extraction record, original
  checksum, canonical checksum/character/table measures, processed JSONL,
  candidate chunks, parser/status fields, and non-empty sections. A missing,
  corrupt, mismatched, empty, malformed, scanned/no-text, or conversion-failed
  candidate cannot be reviewed or published.
- Candidate artifacts do not touch the live manifest or live chunks until the
  existing explicit reviewed atomic publish transition. Candidate isolation
  and unchanged live-artifact tests passed.

## Fixtures and factual QA/comparison

All fixtures are small, locally authored/generated, tracked, and listed in
`tests/fixtures/gate02/fixture_manifest.json`. No external checkout or user
document is required to locate them.

| Fixture | SHA-256 | MarkItDown candidate facts | Existing-loader comparison |
| --- | --- | --- | --- |
| `normal.pdf` | `0277df8561027d4327e720f10d8823fe10081e39c5ed13aca22393ab4a9df1c6` | `ok`; 233 chars, 3 sections, 0 tables; no warnings | pypdf 6.12.2: 2 blocks, 1 section, 226 chars; `pdf_table_extraction_limited` |
| `malformed.pdf` | `354cc2179748a3d5edc7c033b97e9ca3c6462a54c960f5481cea19abd3bece7c` | failed structural validation; no canonical output; `malformed_pdf` | pypdf failed with `PdfStreamError` |
| `scanned_no_text.pdf` | `16b37bf4359c1e5e85674975fc5ff85574689647a208e79b37deffcb409a130d` | empty Markdown; failed; 0 chars/sections/tables; `empty_markdown` | pypdf: 0 blocks/sections/chars; page-empty/no-block/table warning |
| `table_heavy.pdf` | `60f35f2ddb077b32685dc4d2cbe364a94050ca25bf550ad484c98e1e6ef38582` | `ok`; 325 chars, 1 section, 1 table; no warnings | pypdf 6.12.2: 3 blocks, 1 section, 156 chars; `pdf_table_extraction_limited` |
| `docx_policy.docx` | `fb7fc2d4f3298fd66fa6eeb51318c3d66c78eecb49003c1fe8f958f896a5a31e` | `ok`; 237 chars, 3 sections, 1 table; no warnings | existing python-docx loader 1.2.0: 4 blocks, 2 sections, 106 chars |
| `malformed.docx` | `380faa0aac38de9002e2e5771dc7ed54d9983b53c267afac35208ca670abe370` | failed package validation; no canonical output; `malformed_docx` | existing python-docx loader failed with `PackageNotFoundError` |

The table measure is not a quality score: one table is counted per Markdown
separator row following a row containing `|`. No visual, layout, OCR, or
fidelity claim is made.

## Commands/tests executed

All application commands used `VietRagOps/.venv/Scripts/python.exe` with
`PYTHON_DOTENV_DISABLED=true` and `LLM_PROVIDER=mock` where the app was
loaded. No `.env` or credential handoff file was read.

- Required `session_start.py --root .` — passed; reported the documented dirty
  overlay and stale pre-Gate-02 map.
- Gate 00/01 PASS, commit reachability, commit-range, overlay inventory/hash,
  clean external checkout, empty index, app pre-install import probe, and
  dependency declaration checks — passed as recorded above.
- Pre-edit compile — passed.
- Pre-edit focused lifecycle baseline — corrected exact-file invocation
  `75 passed`; the first wildcard invocation failed with pytest exit 4, and the
  default system temp location produced 32 passes/43 setup errors before the
  workspace-basetemp rerun.
- MarkItDown runtime import/API/plugins-disabled check and `pip check` — passed.
- Adapter focused tests — `12 passed`; symlink branch uses the real OS path
  when permitted and deterministic branch simulation when this runner denies
  symlink creation.
- Phase 2.2 focused integration/lifecycle tests — `97 passed`.
- Required compile command
  `.venv\\Scripts\\python.exe -m compileall -q app rag scripts evals frontend tests`
  — passed.
- Required bare full command `.venv\\Scripts\\python.exe -m pytest -q` —
  environment failure: `90 passed, 67 setup errors` from denied system
  temp/cache paths. Corrected project-interpreter command with exact workspace
  basetemp and cache plugin disabled — `157 passed, 1 warning`.
- `scripts/validate_chunks.py --chunks-dir data/chunks` — passed; rows
  `1036/695/572`, abnormal `0` for each.
- `scripts/validate_processed_docs.py data/processed/processed_docs.jsonl` —
  passed; `37/37`, success rate `1.000`.
- `scripts/verify_manifest.py data/manifests/documents_manifest.csv` — passed;
  37 rows, 0 duplicate checksum groups.
- Required module-form offline BM25 smoke wrote
  `gates/baselines/GATE_02_RETRIEVAL_SMOKE.json` — passed; 695 chunks, 20
  queries, recall@5 `0.8889`, MRR `0.5917`, precision@5 `0.1889`, recall@3
  `0.7222`, recall@10 `0.8889`, answerable `18`; metrics match Gate 01.
- Fixture conversion/legacy comparison probe, QA JSON checksum validation, and
  two read-only audits — passed. No live provider, Firecrawl, OCR/cloud, URL
  conversion, MCP, service, or deployment was used.

## Acceptance checklist

- [x] Validated PDF candidates follow immutable original -> local MarkItDown ->
      canonical Markdown -> existing Markdown loader/section builder/chunker ->
      isolated candidate artifacts.
- [x] Original and canonical Markdown are linked by checksums and durable
      extraction telemetry/registry locations.
- [x] Malformed, scanned/no-text, empty, conversion-failed, no-section, and
      corrupt-record candidates remain failed and cannot be reviewed/published.
- [x] Existing pypdf loader remains available through an explicit, recorded
      server-owned fallback policy; no silent rescue occurs.
- [x] PDF and fixture-validated DOCX are enabled; PPTX and XLSX remain
      unsupported/rejected.
- [x] Existing-corpus RAG regression is unchanged: all baseline artifact hashes
      match and all retrieval metrics match Gate 01.
- [x] `gates/results/GATE_02_RESULT.md` is written in the required format.

## Evidence artifacts

- `gates/baselines/GATE_02_EXTRACTION_QA.json` — metric-only fixture comparison,
  parser provenance, checksums, statuses, and warnings.
- `gates/baselines/GATE_02_RETRIEVAL_SMOKE.json` — current offline BM25 smoke.
- `tests/fixtures/gate02/fixture_manifest.json` — local fixture provenance and
  checksums.
- `tests/test_markitdown_adapter.py` and
  `tests/test_gate02_markdown_pipeline.py` — focused boundary, integration,
  failure, isolation, checksum, DOCX, and fallback coverage.
- Existing corpus/processed/manifest/chunk/QA input hashes were independently
  compared to Gate 00 and match exactly.

## Known issues

- The exact bare pytest command is not runnable in this managed runner because
  its system temp/cache directories deny access. The corrected project-
  interpreter workspace-basetemp run is the current full-suite proof.
- The host did not grant real symlink creation; the symlink rejection code path
  was exercised deterministically by the focused test, while path escape was
  tested with a real outside-root path.
- Fixture comparisons are factual extraction measures only. They do not prove
  visual/layout fidelity, OCR quality, parser superiority in general, or
  production readiness.
- The Gate 01 single-writer lifecycle assumption and the deliberate fact that
  the pre-existing 37-document corpus is not version-tracked remain unchanged.

## Next allowed Gate

Gate 03 only, in a new explicit session after reviewing this result and evidence.

## STOP

No next-Gate work performed.
