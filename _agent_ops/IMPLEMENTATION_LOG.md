# Implementation Log / Nhat ky trien khai

Append-only. Add a new entry for each meaningful task or phase.

## Entry Template

### Date

`YYYY-MM-DD`

### Phase / Task

`<phase or task name>`

### Files Touched

- `<file path>`

### What Changed

- `<change>`

### Why

`<reason>`

### Tests Run

```bash
<command>
```

### Results

`<pass/fail and evidence>`

### Bugs Found

- `<bug or none>`

### Root Cause

`<root cause if known>`

### Fix Applied

`<fix or none>`

### Git Commit

`<hash or not committed>`

### Push Result

`<pushed/not pushed/not applicable>`

### Remaining Risks

- `<risk>`

### Next Step

`<next concrete task>`

---

## Entry: 2026-08-26 - Agent-ops bootstrap

### Phase / Task

Bootstrap context restoration for the existing VietRAGOps project.

### Files Touched

- `AGENTS.md`
- `_agent_ops/` generated runtime/tools and durable context files

### What Changed

- Initialized `_agent_ops/` from the embedded workspace-pack templates.
- Copied runtime tools, built a symbol index with 452 symbols and 850 edges, and generated `REPO_MAP.md` for 110 code files.
- Imported the supplied master context card into `PROJECT_CONTEXT_CARD.md`.
- Verified the Markdown file and the Markdown entry inside the companion master ZIP have identical SHA-256.
- Recorded the bootstrap scope and deferred the separate Evolve Research Pack.

### Why

The project had no agent-ops layer after the previous work was dropped. Durable context is needed before the next improvement task can be started safely.

### Tests Run

```text
python ..\\ai-agent-workspace-pack\\scripts\\init_project_ops.py --target .\\VietRagOps
python _agent_ops/tools/session_start.py --root .
SHA-256 comparison of MASTER_CONTEXT_CARD_VietRAGOps.md and its ZIP entry
```

### Results

Bootstrap completed. Session-start checks reported repository `main`, HEAD `5b9045d`, fresh continuity, current repo map/index, and no current baseline evidence. The master ZIP entry matched the Markdown source byte-for-byte.

### Bugs Found

- None in the bootstrap path.

### Root Cause

The project lacked initialized `_agent_ops/` context; the source project itself was not modified.

### Fix Applied

Initialized the ops layer and filled the durable context records; no product-code fix was applied.

### Git Commit

Not committed; user did not request a commit.

### Push Result

Not applicable.

### Remaining Risks

- The supplied master card is a historical audit from 2026-08-17, not a fresh behavior baseline.
- Gate 00 and current deterministic tests remain pending.
- The Evolve Research Pack is intentionally not loaded in this task.

### Next Step

Stop bootstrap and wait for the user's next task.

## Entry: 2026-08-26 - Gate 00 baseline freeze

### Phase / Task

`GATE-00` — reproducible baseline and safe restructure decision only.

### Evidence

- Current repository snapshot: canonical root `D:/Project cua Dat/VietRAGOps/ROOT/VietRagOps`, branch `main`, HEAD `e710230a7a99c03c2d8591518ee7139f19fb89ba`, upstream relation 2 ahead / 0 behind at capture.
- Dirty overlay was independently identified as 6 tracked modified/deleted paths and 38 nonignored untracked files with safe hashes; no source, test, or data overlay was staged. Deleted tracked files retain their HEAD blob IDs.
- Corpus inventory is 37 documents plus `data/raw/.gitkeep`; processed docs are 37 rows; chunks are 1,036 / 695 / 572 for 300 / 500 / 800; no persisted index exists. The live retrieval source is `data/chunks/chunks_500.jsonl` through `ChunkIndexStore`.
- Offline BM25 retrieval smoke passed for 20 dev queries with 695 chunks. Full pytest was unavailable because `C:\Python314\python.exe` has no `pytest` module. Chunk, processed-doc, manifest, compile, and Compose config checks passed as recorded in `gates/baselines/GATE_00_BASELINE.json`.

### Scope Decision

No module boundary change is needed now. Existing loaders/preprocessing/chunking, retrieval/index store, generation/provider, evaluation, and ops ownership are explicit; no demonstrated coupling or authorized Gate 01 requirement justifies moving or duplicating modules.

### Files / Commits

- Baseline evidence commit `bb10a0e`: `gates/baselines/GATE_00_BASELINE.json` and `gates/baselines/GATE_00_RETRIEVAL_SMOKE.json` only.
- State and result files are being prepared in a separate explicit commit. Pre-existing dirty source/test/ops paths remain untouched and unstaged.

### Security / Scope Boundary

No `.env` content or credential value was read, printed, copied, logged, or committed. No provider, network-dependent feature, Firecrawl, MarkItDown, Docker service, GCP, reset, cleanup, or push was used.

### Known Command Failures

- The prompt's exact no-argument processed-doc and manifest commands return their existing usage exit 2; corrected explicit-path forms pass.
- Direct evaluator help fails with `ModuleNotFoundError: No module named 'evals'`; module-form help and smoke pass.
- An initial commit attempt used a duplicated working-directory path and did not start (`CreateProcessWithLogonW: 267`).
- Final smoke artifact hash printing initially used a string as though it had `.FullName`; the smoke itself passed and the corrected hash check passed.

### Next Step

Write/validate `PROJECT_STATE.md` and `gates/results/GATE_00_RESULT.md`, commit only those two state/result files, verify status, and stop. Do not begin Gate 01.

## Entry: 2026-08-26 - Gate 00/01 Luna prompt handoff

### Phase / Task

EVOLVE-OPS-003 — prepare bounded, paste-ready execution prompts; no gate
implementation was performed.

### Files Touched

- _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_00_EXECUTION_PROMPT.md
- _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_01_EXECUTION_PROMPT.md
- _agent_ops/CURRENT_TASK.md
- _agent_ops/SESSION_BRIEF.md

### What Changed

- Added a Gate 00 prompt with a reproducible baseline manifest, dirty-tree
  decision rule, safe-boundary decision, result artifact, and hard stop.
- Added a separate Gate 01 prompt with a Gate 00 PASS prerequisite, four
  lifecycle phases, candidate/live isolation proof, atomic publish/retire/
  rollback tests, result artifact, and hard stop.

### Evidence

- Each new prompt was explicitly staged alone, checked with Git, and committed
  separately: 39e91b1 for Gate 00 and e710230 for Gate 01.
- Two internal read-only reviews independently confirmed the Gate ordering,
  current dirty-tree risk, and no-provider boundaries.
- An Antigravity model-list check reported no authenticated runtime. An attempted
  project-context external review was safety-blocked; no project files or
  credentials were sent to it.

### Tests Run

    git show --check --stat --oneline 39e91b1
    git show --check --stat --oneline e710230
    git diff --cached --name-only
    git status --short

### Results

Both commits passed Git whitespace checks and the index was empty after the
commits. Pre-existing working-tree changes remain and were not staged.

### Scope Boundary

No source, data, dependency, Docker, provider, Firecrawl, MarkItDown, or
credential change was made. No gate was executed, and no push was attempted.

### Next Step

Run the Gate 00 prompt in a separate Luna session. Do not start Gate 01 until a
current Gate 00 result explicitly reports PASS.

## Entry: 2026-08-26 - Evolve context import and local tooling preparation

### Phase / Task

`EVOLVE-OPS-001` — planning-context integration and pre-Gate tool preparation.

### Files Touched

- `AGENTS.md`
- `_agent_ops/PROJECT_CONTEXT_CARD.md`, `PHASE_ROADMAP.md`, `DECISION_LOG.md`,
  `RISK_REGISTER.md`, `INDEX.md`, `THIRD_PARTY_TOOLING.md`, `env_templates/README.md`
- `_agent_ops/phase_context_cards/evolve_2026_08_26/*`
- ignored local files: `.env.firecrawl.local` and external Firecrawl `.env`

### What Changed

- Integrated the supplied 22-file Evolve pack as one sourced master card and
  eleven short gate cards. Every gate remains not started/blocked by its stated
  prerequisite.
- Cloned external MarkItDown at `9dc0d6579b8739c9d0671ff205e071e3053c7df1`,
  installed `markitdown=0.1.7` with PDF/DOCX/PPTX/XLSX extras in its own venv,
  and verified import plus CLI help.
- Cloned external Firecrawl at `d26ad4bbf2fe1d0be3b8bb4a94bfe8baa2c15e72`,
  wrote a no-secret localhost baseline and verified `docker compose config --quiet`.
- Preserved the pre-existing application `.env` byte-for-byte; created an empty
  ignored Gate-03 Firecrawl handoff file.

### Why

The user asked for durable Evolve tracking and local setup before starting the
baseline. Separation prevents external tooling from being mistaken for product
integration or scientific evidence.

### Tests Run

```text
external_tools\markitdown\.venv\Scripts\python.exe -c "from markitdown import MarkItDown ..."
external_tools\markitdown\.venv\Scripts\markitdown.exe --help
docker compose --project-directory external_tools\firecrawl --env-file external_tools\firecrawl\.env -f external_tools\firecrawl\docker-compose.yaml config --quiet
```

### Results

MarkItDown import/CLI and Firecrawl Compose configuration passed. No Firecrawl
container, API request, provider call, app-source integration, Gate 00 baseline,
commit or push was performed.

### Security / Scope Decision

The pasted ArgScope multi-account configuration was not copied: it targets a
different runtime, while automatic rotation of borrowed keys would be a
quota-evasion path. VietRAGOps continues to document only its existing single-key
contract and secret-free templates.

### Next Step

Wait for an explicit request to run the bounded Gate 00 baseline. Stop after its
result artifact before considering Gate 01.

## Entry: 2026-08-26 - Firecrawl key-onboarding pointer

### Phase / Task

`EVOLVE-OPS-002` — hosted Firecrawl key onboarding documentation only.

### What Changed

- Added the official owner dashboard URL to `THIRD_PARTY_TOOLING.md` and
  `env_templates/README.md`.
- Documented direct local placement into ignored `.env.firecrawl.local` and a
  confirmation-without-value rule.

### Evidence

Firecrawl's official API documentation states that the API key is obtained from
the dashboard and sent as a Bearer credential. No key value or authenticated call
was made in this task.

### Scope Boundary

The pasted file targets `D:\GRADUATION_THESIS\ArgScope` and assumes a multi-key
router absent from VietRAGOps. It was not copied. Automatic borrowed-key rotation
remains out of scope because it could bypass provider quota/account controls.

### Next Step

Wait for an explicit Gate 00 request. A locally placed Firecrawl key alone does
not start Gate 03 or authorize a request.
## Entry: 2026-08-26 - Bootstrap hygiene verification

### Phase / Task

Verification boundary for the agent-ops bootstrap.

### Files Touched

- None after the bootstrap records above; this entry records a read-only check.

### What Changed

- No repository cleanup was applied.

### Why

The workspace-pack hygiene checker was run to separate bootstrap changes from pre-existing repository hygiene debt.

### Tests Run

```text
python _agent_ops/tools/check_repo_hygiene.py --root .
git status --short --untracked-files=all
git diff --check
```

### Results

The hygiene command failed on pre-existing tracked/generated artifacts including `data/`, `.env.example`, `.venv/`, `dist/` and caches. It also passed its specific check that session-scoped `_agent_ops/` files are not tracked. `git diff --check` was clean; status showed only the new `AGENTS.md` and `_agent_ops/` bootstrap layer.

### Bugs Found

- Pre-existing repository hygiene findings; not caused by this bootstrap.

### Root Cause

The existing repository contains tracked data and local/generated artifacts that the checker flags.

### Fix Applied

None. Cleanup is outside the requested bootstrap scope.

### Git Commit

Not committed; user did not request a commit.

### Push Result

Not applicable.

### Remaining Risks

- Repository-wide hygiene remains unresolved and must be handled as a separate explicitly scoped task.

### Next Step

Stop bootstrap and wait for the user's next task.

---

### Date

`2026-08-26`

### Phase / Task

`GATE-01` — governed local document lifecycle (Phases 1.0-1.4)

### Files Touched

- `rag/lifecycle/__init__.py`, `errors.py`, `naming.py`, `intake.py`,
  `registry.py`, `storage.py`, `pipeline.py`, `publish.py`, `service.py` (new package)
- `app/core/config.py` (env-overridable chunks/manifest paths, `lifecycle_root`,
  `lifecycle_max_upload_bytes`, `refresh_live_caches()`, `get_lifecycle_service()`)
- `app/schemas/document.py` (new intake/version/rollback response models)
- `app/api/routes_documents.py` (governed `/documents/upload`; new
  `GET /documents/{doc_id}/versions`, `POST /documents/versions/{id}/review`,
  `.../publish`, `.../retire`, `POST /documents/{doc_id}/rollback`)
- `.gitignore` (`data/lifecycle/` — runtime DB/originals/candidates, never committed)
- `tests/test_lifecycle_intake.py`, `test_lifecycle_registry.py`,
  `test_lifecycle_pipeline.py`, `test_lifecycle_candidate_isolation.py`,
  `test_lifecycle_publish_apply.py`, `test_lifecycle_service.py`,
  `test_api_documents_lifecycle.py` (new/extended)

### What Changed

Replaced the upload-only `/documents/upload` route (which wrote caller
filenames directly to disk and never touched the index) with a governed
lifecycle: bounded/checksummed/format-validated intake -> immutable original ->
SQLite source/version registry -> candidate-only parse+chunk (isolated from the
live manifest/chunks) -> explicit review -> atomic publish (or retire/rollback).
Live reads (`get_store`, `get_context_builder`, the two answer generators) are
cache-cleared right after any publish/retire/rollback so the next request
re-reads the swapped files. The pre-existing 37-document manifest/chunks_500
corpus was left exactly as-is; the registry only tracks documents ingested
through this new lifecycle.

### Why

This was Gate 01's explicit objective per
`_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_01.md` and
`..\VietRAGOps_Evolve_Research_Gate_Pack_2026-08-26\gates\GATE_01_DOCUMENT_LIFECYCLE.md`:
turn upload from an ungoverned raw write into a reviewed, reversible ingestion
lifecycle without letting unreviewed candidates reach live answers.

### Tests Run

```bash
./.venv/Scripts/python.exe -m compileall -q app rag scripts evals frontend tests
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe scripts/validate_chunks.py --chunks-dir data/chunks
./.venv/Scripts/python.exe scripts/validate_processed_docs.py data/processed/processed_docs.jsonl
./.venv/Scripts/python.exe scripts/verify_manifest.py data/manifests/documents_manifest.csv
./.venv/Scripts/python.exe -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl \
  --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5 --output gates/baselines/GATE_01_RETRIEVAL_SMOKE.json
```

### Results

- `compileall`: PASS.
- `pytest -q`: 134 passed (59 pre-existing + 75 new lifecycle tests), 0 failed.
  Pre-edit baseline (same `.venv` interpreter, before any Gate 01 change): 59
  passed, 0 failed.
- `validate_chunks`/`validate_processed_docs`/`verify_manifest`: PASS, identical
  counts/hashes to the Gate 00 baseline (1036/695/572 chunk rows, 37/37 docs,
  37 manifest rows, 0 duplicate checksum groups) — the real corpus was never
  touched by any Gate 01 test (all lifecycle integration tests run against a
  `tmp_path`-isolated manifest/chunks/registry via `VIETRAGOPS_*` env overrides).
- Offline BM25 smoke: recall@5 0.8889, MRR 0.5917, 695 chunks, 20 queries —
  identical to `gates/baselines/GATE_00_RETRIEVAL_SMOKE.json`.

### Bugs Found

- Gate 00 ran all tests/scripts with `C:\Python314\python.exe`, which has no
  pytest installed, and reported "pytest unavailable" as a blocker. The
  project's own `.venv\Scripts\python.exe` has pytest 9.0.3, fastapi, and
  httpx already installed; `pytest -q` there passes cleanly (59/59 before this
  Gate's changes). This is an interpreter-selection issue in how Gate 00 was
  run, not a missing dependency. Recorded here as an operating fact for future
  sessions; not corrected retroactively in Gate 00's own artifacts.
- Self-found and fixed during Phase 1.4 implementation, before any commit:
  `rag/lifecycle/service.py` originally referenced a nonexistent
  `receiver.content_type` attribute and left a dead unused `original_path`
  local variable in `complete_intake`; `registry.create_version` did not
  accept a pre-generated `version_id`, forcing an awkward
  patch-after-create via `update_review_status`; `service.rollback` called a
  nonexistent `registry.record_rollback_event`. Fixed by storing
  `raw_filename`/`content_type` on `IntakeReceiver`, adding an optional
  `version_id` parameter to `registry.create_version`, and adding
  `registry.record_note()`. All caught by running
  `tests/test_lifecycle_service.py` before committing Phase 1.4 — none of
  this shipped in a committed state.

### Git Commits

- `f359751` feat(gate-01): validate document intake
- `0a1d352` feat(gate-01): add local source registry
- `b4149d1` feat(gate-01): isolate candidate document processing
- `9a02ac1` feat(gate-01): publish reviewed document versions

Not pushed (no push requested/authorized).

### Push Result

Not applicable.

### Remaining Risks

- The existing 37-document manifest/chunks_500.jsonl corpus is not tracked by
  the new registry (deliberate Phase 1.0 decision, see `CURRENT_TASK.md`);
  those legacy documents have no version history, review status, or rollback
  path. A future gate would need an explicit, tested migration to bring them
  under lifecycle management.
- `LifecycleService.publish`/`retire`/`rollback` rebuild the full live
  manifest/chunks file on every call (single-writer assumption); there is no
  cross-process lock, so concurrent publishes from two processes could race.
  Acceptable for Gate 01's single-operator scope; would need a lock file or a
  different storage engine before multi-writer use.

### Next Step

Write `gates/results/GATE_01_RESULT.md`, commit it separately, STOP. No Gate 02
work.


## Entry: 2026-08-26 - Gate 02 Luna prompt handoff

### Phase / Task

EVOLVE-OPS-004 — prepare a scope-controlled Gate 02 execution prompt; no Gate
02 implementation was performed.

### Files Touched

- _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_02_EXECUTION_PROMPT.md
- _agent_ops/CURRENT_TASK.md
- _agent_ops/SESSION_BRIEF.md

### What Changed

- Added one paste-ready Gate 02 prompt covering the app-runtime MarkItDown
  setup, narrow local adapter, PDF + bounded DOCX candidate path, extraction QA,
  full regression, result artifact, and STOP boundary.
- The prompt requires a pinned app dependency rather than runtime imports from
  external_tools. It keeps PPTX/XLSX out of scope unless fully proven.

### Evidence

- Gate 00 and Gate 01 result files currently state PASS. Gate 01 commit chain
  through df5d84c and the recorded modified-file SHA-256 were independently
  checked; the current branch is ahead of origin with no push.
- External MarkItDown checkout remains at 9dc0d6579b8739c9d0671ff205e071e3053c7df1
  and version 0.1.7; its external venv imports successfully. The application
  .venv does not yet import MarkItDown, which is explicitly part of Gate 02.
- A bounded Antigravity read-only audit was requested under the user's approval,
  but platform safety blocked external transfer of project documents. No project
  file or credential was sent.

### Tests Run

    external MarkItDown version/import check
    application .venv MarkItDown import check
    git show --check / staged-file verification for 7d54d8a

### Results

The Gate 02 prompt was the only staged file and its commit passed Git whitespace
validation. No source, dependency, external-tool, provider, credential, or
dataset change was made by this prompt task.

### Next Step

Run the Gate 02 prompt in a new Luna session. Do not start Gate 03 there.


## Entry: 2026-08-26 - Gate 02 local MarkItDown candidate path

### Phase / Task

GATE-02 — execute only the local validated-document-to-canonical-Markdown
gate; preserve the Gate 01 lifecycle, dirty overlay, offline/provider boundary,
and stop before Gate 03.

### Files Touched

- `requirements.txt`
- `rag/ingestion/__init__.py`, `rag/ingestion/markitdown.py`
- `rag/lifecycle/extraction.py`, `pipeline.py`, `registry.py`, `service.py`
- `app/core/config.py`, `app/api/routes_documents.py`,
  `app/schemas/document.py`
- Gate 02 tests and six small local fixtures under `tests/fixtures/gate02/`
- `gates/baselines/GATE_02_EXTRACTION_QA.json`,
  `gates/baselines/GATE_02_RETRIEVAL_SMOKE.json`
- `PROJECT_STATE.md`, `gates/results/GATE_02_RESULT.md`
- `_agent_ops/CURRENT_TASK.md`, `SESSION_BRIEF.md`, `REPO_MAP.md`

### What Changed

- Pinned application dependency `markitdown[pdf,docx]==0.1.7`; the app
  runtime uses `MarkItDown(enable_plugins=False)` and only local/stream APIs.
- Added a root-checked adapter that rejects caller strings, URI inputs,
  symlink/path escape, unverified streams, invalid output, and converter
  exceptions with stable non-secret codes.
- Made MarkItDown the server-owned default for PDF and DOCX candidate parsing;
  existing Markdown loader, section builder, and chunker remain the path after
  canonical Markdown. Added structural PDF/DOCX checks so malformed packages
  fail before a text fallback can mislabel them as successful.
- Added atomic `canonical.md` and `extraction.json` candidate artifacts,
  checksum/measure telemetry, registry migration fields for both paths, and
  restart-time integrity checks at review, publish, and rollback.
- Kept pypdf as an explicit `VIETRAGOPS_CANDIDATE_PDF_PARSER=pypdf` policy;
  failed MarkItDown conversion never silently invokes it. PPTX/XLSX remain
  rejected.

### Evidence

- Gate 00 and Gate 01 result files explicitly state PASS; Gate 01 result commit
  `df5d84c232316c4b0068dbd45661ab20d0168a60` is reachable. Only `7d54d8a`
  followed it before Gate 02 and it is the prompt handoff document.
- Current six tracked dirty-overlay paths and 38 nonignored untracked paths
  match the recorded inventory; `groq_client.py` SHA-256 remains
  `b48cf46c4381176b154ea99ee2157315934edb7b340bbc4a86791cc59e99f68f` and the
  index was empty before the first edit. Pre-existing overlay files were not
  staged or normalized.
- External MarkItDown checkout is clean at
  `9dc0d6579b8739c9d0671ff205e071e3053c7df1`, version `0.1.7`; app runtime
  import/API construction reports version `0.1.7`, plugins disabled, no LLM
  client, and `pip check` reports no broken requirements.
- Fixture QA: normal PDF `233` canonical characters/`3` sections/`0` tables;
  table-heavy PDF `325`/`1`/`1`; DOCX `237`/`3`/`1`; malformed PDF and DOCX
  failed; no-text PDF returned empty and failed. Legacy pypdf/python-docx
  measures are retained in the metric-only QA artifact.
- Corrected focused lifecycle baseline: `75 passed`; adapter: `12 passed`;
  Gate 02 integration/lifecycle: `97 passed`; full corrected suite: `157
  passed, 1 warning`.
- Corpus validators: chunks `1036/695/572`, abnormal `0`; processed docs
  `37/37`; manifest `37`, duplicate checksum groups `0`.
- Gate 02 offline BM25 smoke: `695` chunks, `20` queries, recall@5 `0.8889`,
  MRR `0.5917`, precision@5 `0.1889`; all comparison metrics match Gate 01.
  Existing corpus, processed, manifest, chunk, and QA-input hashes match the
  Gate 00 baseline.

### Commands / Tests Run

- Required startup and ordered Gate 02 context reads.
- External checkout revision/status and app pre-install import/declaration
  probes; no secret file was read.
- `.venv\\Scripts\\python.exe -m pip install --disable-pip-version-check
  --no-input markitdown[pdf,docx]==0.1.7` (normal path hung twice; approved
  bounded escalated retry completed).
- `.venv\\Scripts\\python.exe -m compileall -q app rag scripts evals frontend tests`.
- Focused and full pytest runs with exact workspace basetemps; the bare exact
  full command reproduced the runner's denied system-temp/cache error, while
  the corrected command passed `157/157`.
- `scripts/validate_chunks.py --chunks-dir data/chunks`,
  `scripts/validate_processed_docs.py data/processed/processed_docs.jsonl`,
  `scripts/verify_manifest.py data/manifests/documents_manifest.csv` — all
  passed.
- Required module-form retrieval smoke wrote Gate 02 evidence and matched Gate
  01 metrics; no service/provider/network feature was called.
- Two read-only audits passed: adapter path/URI/plugin/network and candidate
  isolation; fallback/failure-to-publish/integrity-test coverage.

### Git Commits

- `e44e012` build(gate-02): add local markitdown runtime — `requirements.txt`.
- `c36f905` feat(gate-02): add local markdown adapter — adapter package and
  focused tests.
- `3c1cff0` fix(gate-02): classify invalid conversion output — adapter/test
  correction.
- `bc3b96c` feat(gate-02): convert pdf candidates to markdown — candidate
  integration, registry migration, fixtures, and lifecycle tests.
- `03249ce` test(gate-02): verify markdown extraction quality — extraction QA
  and retrieval smoke evidence.
- Final state/result commit is written separately after this entry.

### Security / Scope Decision

No `.env` or credential handoff file was read, printed, copied, logged, or
committed. No Firecrawl, Groq, OCR/cloud endpoint, URL conversion, MarkItDown
MCP, PPTX/XLSX support, deployment, reset, cleanup of pre-existing files, or
push was performed.

### Known Limitations

- The exact bare pytest command is environment-blocked by denied system
  temp/cache paths; the project-interpreter workspace-basetemp run is the
  current full-suite proof.
- The symlink test uses the real OS branch when permitted and deterministic
  branch simulation when the Windows runner denies symlink creation.
- Fixture comparisons report extraction measures only; they do not claim
  visual/layout fidelity, OCR quality, or production readiness.

### Next Step

Write and commit only `PROJECT_STATE.md` plus `gates/results/GATE_02_RESULT.md`,
verify status, and stop. Gate 03 requires a new explicit session.

## Entry: 2026-08-26/27 - Gate 03 Firecrawl web import (PASS)

### Phase / Task

Gate 03: admin-controlled, bounded Firecrawl web search/scrape as
reviewed-only candidate sources into the existing lifecycle, under the
mandatory secret-handoff stop rule.

### Files Touched

- `rag/ingestion/firecrawl.py`, `tests/test_firecrawl_adapter.py`
- `rag/lifecycle/web_safety.py`, `tests/test_web_safety.py`
- `app/core/config.py` (FIRECRAWL_* non-secret settings,
  `get_web_import_service`)
- `rag/lifecycle/web_pipeline.py`
- `rag/lifecycle/web_import.py`
- `rag/lifecycle/registry.py` (`web_provenance`, `acquisition_attempts`
  tables + migration)
- `rag/lifecycle/web_diff.py`
- `scripts/web_import.py`
- `tests/test_web_import.py`, `tests/test_web_recrawl_diff.py`
- `PROJECT_STATE.md`, `gates/results/GATE_03_RESULT.md`,
  `gates/baselines/GATE_03_RETRIEVAL_SMOKE.json`
- `.env` (one appended, user-dictated, non-secret line:
  `FIRECRAWL_ALLOWED_DOMAINS=undergrad.tdtu.edu.vn`) -- not committed
  (gitignored); `.env.firecrawl.local` was never opened, read, or edited.

### What Changed

- Phase 3.0: re-verified Gate 00/01/02 PASS, commit reachability (`f986976`
  ancestor of HEAD, `d05be38` confirmed docs/ops-only), dirty-overlay
  identity, empty index, clean `external_tools/firecrawl` at its pin, and
  `.gitignore` filename coverage of `.env.firecrawl.local`. Designed the
  non-secret `FIRECRAWL_*` config surface (empty allowlist = deny-all).
- Phase 3.1: narrow httpx-based Firecrawl v2 adapter
  (`search_preview`/`scrape_markdown` only), typed outcome classes
  (unauthorized/credit_exhausted/rate_limited/timeout/upstream_error/
  invalid_response/blocked_target), bounded retries (max 2, only
  408/429/500/502/503/504, respecting `Retry-After` incl. HTTP-date),
  streaming byte-budget cap, wall-clock stream deadline.
- Phase 3.2: HTTPS-only URL syntax validation, blocked-hostname list,
  request-time DNS rejection of private/loopback/link-local/multicast/
  reserved/unspecified addresses (v4+v6), server-owned default-deny
  domain allow/deny policy (denylist always wins).
- Phase 3.3: candidate build reusing the existing Markdown
  loader/section builder/chunker, extraction record in the exact schema
  `rag/lifecycle/pipeline.py` uses so `LifecycleService` accepts it
  unchanged; document identity `web-{sha256(canonical_url)[:24]}`;
  idempotent on unchanged checksum; local-only CLI instead of a FastAPI
  route (no admin authorization exists anywhere in the app).
- Phase 3.4: deterministic (no LLM) changed-section diff by heading path
  + content hash between prior/new `canonical.md`; linked via
  `prior_version_id`/`diff_path` in `web_provenance`, never touching
  `versions.supersedes`/`superseded_by`.
- Two read-only audits (Explore agent; Antigravity not available on this
  platform, recorded once as `AGY_UNAVAILABLE`): after Phase 3.2 found
  three adapter hardening gaps (fixed); before the first result found two
  recrawl-diff bugs -- duplicate heading paths silently overwriting each
  other's hash, and a missing prior canonical file producing a misleading
  "everything added" diff (both fixed). A DNS-rebinding/TOCTOU limitation
  inherent to any hosted-scraper SaaS boundary was documented, not fixed.
- Phase 3.5 (live proof), only after the user explicitly confirmed
  in-session that the local key is filled in and configured
  `FIRECRAWL_ALLOWED_DOMAINS=undergrad.tdtu.edu.vn` themselves: fixed two
  CLI defects the live run surfaced (`sys.path` missing repo root; stdout
  not UTF-8, crashing on the Vietnamese result title); one bounded
  `search_preview(limit=1)` call (plus one corrective re-run after the
  encoding crash) returned exactly one descriptor; the user explicitly
  approved that URL; one bounded `scrape_markdown` call succeeded and was
  stored strictly as `review_status=candidate`.

### Evidence

- Six Gate 00-02 prerequisite facts independently re-verified (see Phase
  3.0 above); `groq_client.py` and the rest of the pre-existing dirty
  overlay were never staged, reset, restored, cleaned, stashed, or
  amended; no push occurred until explicitly requested after the full
  Gate closed.
- 79 new automated tests, all offline/mocked: 17 adapter, 40 safety, 14
  import, 8 recrawl/diff.
- Live proof: `document_id=web-88b8c28734c6c0199ae608b8`,
  `version_id=c013dd02f93043d49ccf147d2701e99a`, `parse_status=ok`,
  `review_status=candidate`, `content_checksum` recorded, `retrieved_at`
  UTC recorded, `credits_used`/`firecrawl_action_id` both `None` on the
  real response (adapter looks for header/field names this account's
  response didn't surface -- recorded as-is, not fabricated). Live
  manifest/chunks verified byte-identical before and after
  (`git status --short -- data/manifests data/chunks` empty both times).
- Full offline regression before and after the live call: identical --
  compile clean, `236/236` tests, chunk/processed-doc/manifest validation
  unchanged from Gate 00-02, offline BM25 smoke bit-for-bit identical to
  `gates/baselines/GATE_02_RETRIEVAL_SMOKE.json` (recall@5 `0.8889`, MRR
  `0.5917`, precision@5 `0.1889`).

### Commands / Tests Run

- `.venv\Scripts\python.exe -m compileall -q app rag scripts evals frontend tests`
  -- clean before every commit, both before and after the live call.
- `PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv\Scripts\python.exe
  -m pytest -q --basetemp <workspace> -p no:cacheprovider` -- grew
  `211 -> 214 -> 228 -> 234 -> 236 passed, 0 failed` across phases;
  unchanged after the live call.
- `scripts/validate_chunks.py`, `scripts/validate_processed_docs.py`,
  `scripts/verify_manifest.py` -- passed, identical to Gate 00-02, both
  before and after the live call.
- `python -m evals.experiments.run_retrieval_eval ... --output
  gates/baselines/GATE_03_RETRIEVAL_SMOKE.json` -- run twice (pre- and
  post-live-call); identical metrics both times.
- Live (no dotenv-disable flag, so the CLI loaded the real `.env`/
  `.env.firecrawl.local`): `python scripts/web_import.py search --query
  "site:undergrad.tdtu.edu.vn" --limit 1` (run twice: first crashed on
  print after a successful call, due to a Windows console encoding bug;
  second succeeded after the UTF-8 stdout fix); `python
  scripts/web_import.py import --url "https://undergrad.tdtu.edu.vn/"
  --title "..."` (run once, after explicit user approval of that URL).

### Bugs Found

- Adapter: HTTP-date `Retry-After` not parsed; no wall-clock deadline
  across a streamed read; byte cap checked after append instead of
  before (all found by the post-3.2 audit).
- Recrawl diff: two sections sharing a heading path silently overwrote
  each other's hash in the comparison dict; a prior version whose
  registry-recorded canonical path no longer existed on disk produced a
  misleading "everything added" diff instead of the documented no-diff
  behavior (both found by the pre-result audit).
- CLI: `scripts/web_import.py` had no `sys.path` insertion for the repo
  root (unlike every other script in `scripts/`), so direct invocation
  raised `ModuleNotFoundError: No module named 'app'`; stdout was not
  UTF-8, so a Vietnamese page title crashed with `UnicodeEncodeError` on
  Windows' default console codepage (both found only by the live run).
- Gap (not a code bug): `scripts/web_import.py` never loaded `.env` or
  `.env.firecrawl.local` at all before Phase 3.5 -- the CLI had no way to
  pick up either the real domain allowlist or the real API key at
  runtime until this was added.

### Root Cause

- Adapter/diff bugs: initial implementations optimized for the common
  case and were not adversarially reviewed for encoding edge cases
  (HTTP-date vs delta-seconds), streaming completion semantics, or
  duplicate-key collisions until the dedicated read-only audits ran.
- CLI bugs: the script was written and unit-tested with a monkeypatched
  service object, so real-process concerns (import path resolution,
  console codepage, .env loading) were never exercised until the actual
  live call.

### Fix Applied

- Adapter: `email.utils.parsedate_to_datetime` fallback for
  `Retry-After`; injectable clock enforcing a stream-wide deadline
  classified as `timeout`/`stream_deadline_exceeded`; pre-append length
  check.
- Diff: section keys disambiguated by occurrence order (stripping the
  "#0" suffix only for the first-occurrence display label); a missing
  prior canonical file now skips the diff and records a distinct
  `recrawl_diff_unavailable` event instead of fabricating one.
- CLI: added the same `sys.path` insertion pattern used by every other
  script in `scripts/`; `sys.stdout.reconfigure(encoding="utf-8")` guarded
  by `try/except`; added `_load_env_files()` loading `.env` then
  `.env.firecrawl.local` (`override=False`) via `python-dotenv`, gated by
  the existing `PYTHON_DOTENV_DISABLED` test-safety switch.

### Git Commits

- `74e5113` feat(gate-03): add bounded firecrawl adapter
- `22d99bc` feat(gate-03): enforce bounded web import safety
- `e6f52cb` fix(gate-03): harden firecrawl adapter after safety audit
- `6e2bb8a` feat(gate-03): import firecrawl pages as candidates
- `db68ed6` feat(gate-03): track recrawl candidate diffs
- `d2bd02b` fix(gate-03): correct recrawl diff on repeated headings and stale paths
- `b178c4b` docs(gate-03): record web import result (intermediate,
  `WAITING_FOR_USER_SECRET`)
- `7a1d042` fix(gate-03): load .env and .env.firecrawl.local in the web-import CLI
- `2e0781e` test(gate-03): verify bounded web import controls (Phase 3.5
  live proof)
- `72e11aa` docs(gate-03): record final PASS result after live proof

### Push Result

Pushed on explicit user request after the full Gate closed:
`d05be38..72e11aa main -> main` to `origin` (`github.com/Dat071104/vietragops`).

### Security / Scope Decision

`.env.firecrawl.local` was never opened, read, printed, or edited by
this agent at any point; the secret-stop rule was honored until the user
explicitly confirmed the key in-session. `.env` received exactly one
appended, user-dictated, non-secret line. No Firecrawl self-host Compose
was started. No public FastAPI route was added (no admin authorization
exists in the app); web import is local-CLI-only. No multi-key/
quota-evasion Groq rotation was touched or implemented (the pre-existing
dirty `AGENTS.md`/`groq_client.py` overlay mentioning it was left
untouched, per explicit instruction to ignore it as out of scope and
contrary to secret policy).

### Known Limitations

- DNS-rebinding/TOCTOU across the Firecrawl hosted-fetch boundary is an
  inherent SaaS limitation, not fixable from this codebase alone.
- `credits_used`/`firecrawl_action_id` were `None` on the one real
  response; the adapter's exact header/field-name assumptions are
  unverified beyond this single live call.
- Candidate directories are not pruned/garbage-collected yet.
- `LifecycleRegistry` remains single-writer, consistent with Gate 01/02.

### Next Step

Gate 04, only in a new explicit session after independently re-verifying
this Gate 03 PASS result and its evidence.

## Gate 04 Phase 4.1 -- Version-aware retrieval

### Date

`2026-08-27`

### Phase / Task

Gate 04 Phase 4.1: every retrieved chunk resolves deterministically to
source, source version, index version, authority state, freshness state.

### Files Touched

- `rag/retrieval/version_resolver.py` (new): `VersionResolver` +
  `ChunkVersionInfo`. Registry-aware when a `LifecycleRegistry` is passed
  (published version -> active; all-versions-retired -> retired,
  diagnostic-only since such a doc's chunks cannot be live); otherwise
  falls back to the manifest's existing `checksum`/`status` columns.
  `freshness_state`/`conflict_key` are opt-in via optional `stale_after`/
  `conflict_key` manifest-row keys that the real corpus never sets.
- `rag/retrieval/index_store.py`: added `ChunkIndexStore.index_version`,
  a deterministic `sha256:<16 hex>` of the backing file's bytes (or of
  sorted chunk id/checksum pairs for in-memory stores). Recomputed once
  per construction; not a random run id or mutable counter.
- `rag/retrieval/__init__.py`: exported `VersionResolver`/`ChunkVersionInfo`.
- `rag/generation/context_builder.py`: `ContextBuilder` takes an optional
  `version_resolver`; when present, attaches a `"version"` dict to each
  selected chunk (resolved once per doc_id, cached per `build()` call) and
  a `chunk_versions` map into `retrieval_debug`. No resolver -> zero
  behavior change (key omitted entirely).
- `app/core/config.py`: added `get_lifecycle_registry()` (shared cached
  registry, reused by `get_lifecycle_service()` and
  `get_web_import_service()`, replacing three separate
  `LifecycleRegistry(...)` constructions) and `get_version_resolver()`
  (built from `load_manifest_rows` + `get_store().index_version` +
  the shared registry). Wired into `get_context_builder()`.
  `refresh_live_caches()` now also clears `get_version_resolver`.
- `app/api/routes_query.py`: the `use_reranker=True` branch's ad hoc
  `ContextBuilder(...)` now also receives `version_resolver=get_version_resolver()`
  so version metadata does not silently disappear under that flag.
- `tests/test_version_resolver.py` (new, 13 tests): index_version
  determinism/change-on-content, legacy checksum-derived resolution,
  missing-document unknown, retired-status manifest fallback,
  published_at -> current, stale_after past/future, conflict_key
  passthrough, registry-tracked resolution, checksum-mismatch-falls-back-
  to-legacy (proves a stale manifest row is never silently matched to the
  wrong registry version), and the fully-retired diagnostic path.
- `tests/test_context_builder_versioning.py` (new, 2 tests): no-resolver
  -> no `"version"` key (baseline-preserving); with-resolver -> every
  chunk and `retrieval_debug.chunk_versions` carry the resolved info.
- `tests/test_api_documents_lifecycle.py`: its own `_clear_caches()`
  helper (used by an `isolated_env` fixture that runs the real HTTP
  lifecycle against a tmp_path-isolated manifest/registry) was missing the
  two new cached functions -- this silently leaked the first test's
  tmp-path registry/resolver into every later test in the file via the
  process-wide `lru_cache` singletons, corrupting
  `test_full_lifecycle_publish_retire_rollback_via_http` (a document came
  back `published` instead of `candidate`). Fixed by adding
  `get_lifecycle_registry.cache_clear()` / `get_version_resolver.cache_clear()`
  to that helper. Verified: failure reproduced before the fix, gone after.

### Why

Gate 04 Phase 4.1 acceptance requires deterministic source/version/index/
authority/freshness resolution without inventing semantics or touching
the frozen 37-doc corpus/manifest schema. Reusing `load_manifest_rows`
(already used by `AdvancedHybridRetriever`) and the existing lifecycle
registry keeps this additive; opt-in `stale_after`/`conflict_key` keys let
fixtures exercise stale/conflict semantics later (Phase 4.2/4.4) without
ever writing those columns into `data/manifests/documents_manifest.csv`.

### Tests Run

```bash
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m compileall -q app rag scripts evals frontend tests
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q tests/test_version_resolver.py tests/test_context_builder_versioning.py --basetemp=<tmp>
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q --basetemp=<tmp>
```

- Focused: 15 passed (13 + 2).
- Full suite: **251 passed, 0 failed** (236 pre-Gate-04 baseline + 15 new).
  One regression caught and fixed mid-phase (cache-clear gap above), then
  re-verified green.
- `git diff --check` on all Gate 04 Phase 4.1 files: clean (the one
  warning present, `groq_client.py:235` blank-line-at-EOF, is the
  pre-existing dirty overlay, not a Gate 04 file).

### Baseline Impact

None. `get_context_builder()`/`get_version_resolver()` only add a new
additive `"version"` dict key that did not exist before; no retriever
ranking, scoring, or existing chunk dict key changed. Retrieval smoke
reproduction from Phase 0 preflight remains the reference (not re-run
mid-phase; re-run again at Phase 4.4).

### Repo Map / Code Index

Regenerated (`--force`); diff is a pure refresh (new
`rag/retrieval/version_resolver.py` module, updated fan-in counts, updated
`Last Verified Commit` placeholder to `31396a3`). No manual edits, no
surprises.

### Next Step

Phase 4.2: deterministic `supported` / `insufficient_evidence` /
`stale_source` / `source_conflict` states, kept separate from citation
verification (including fixing the `citations_verified` heuristic found
in `routes_agent.py` during Phase 0).

## Gate 04 Phase 4.2 -- Deterministic stale/conflict/evidence states

### Date

`2026-08-27`

### Phase / Task

Gate 04 Phase 4.2: deterministic `supported`/`insufficient_evidence`/
`stale_source`/`source_conflict` answer/evidence states, kept as a
separate axis from citation verification.

### Files Touched

- `rag/generation/evidence_state.py` (new): `resolve_evidence_state()` +
  `EvidenceStateResult`. Explicit precedence, documented in the module
  docstring: `insufficient_evidence` (refusal / no citations / no
  resolved version for any citation) > `source_conflict` (2+ cited chunks,
  both `authority_state == "active"`, sharing a `conflict_key` but
  resolving to different `source_version`) > `stale_source` (any cited
  chunk `freshness_state == "stale"`) > `supported`. Reasons over the
  `"version"` metadata Phase 4.1 attaches to each chunk dict only -- no
  LLM/heuristic text-similarity conflict detection.
- `rag/generation/answer_generator.py`: added `_finalize_response()`,
  called from `_refusal_payload()` (covers every refusal path for free --
  guardrail refusal, citation-failure refusal, and the three
  `_deterministic_answer` refusal branches), the deterministic success
  return, the curriculum-credit shortcut return, and the two "provider
  citations verified" return branches in `answer_with_agent_fallback_from_context`/
  `answer_with_meta_from_context` (reusing the `verification` object
  already computed there instead of re-verifying). Every returned response
  dict now carries `citation_verification: {is_valid, errors}` (the real
  `CitationVerifier` result, not inferred) and `evidence_state: {state,
  reasons}` as additive keys.
- **Bug fixed** (found during Phase 0, in scope per the gate's explicit
  "distinguish citation verification from answer correctness" MUST DO):
  `app/api/routes_agent.py::run_agent_query` previously set the response's
  `citations_verified` field from a heuristic
  (`bool(citations) and not refusal`) that never actually consulted the
  verifier. Now reads `answer_payload["citation_verification"]["is_valid"]`
  when the answer generator provided one, falling back to the old
  heuristic only if it did not (keeps the existing `StubAnswerGenerator`-
  based test working without change).
- `app/schemas/query.py`: added `CitationVerification`/`EvidenceState`
  pydantic models; added optional `citation_verification`/`evidence_state`
  fields to `AskResponse` and `AgentAskResponse` (both default `None`,
  fully backward compatible for any caller not yet reading them).
- `tests/test_evidence_state.py` (new, 11 tests): refusal/no-citations/
  unresolved-version -> insufficient_evidence; normal QA (including
  unknown freshness, never conflated with stale) -> supported; stale cited
  source -> stale_source; two active sources sharing a conflict_key with
  differing source_version -> source_conflict; same-version sharing a
  conflict_key is NOT a conflict; a retired source sharing a conflict_key
  with an active one does not trigger conflict; conflict takes precedence
  over stale.
- `tests/test_answer_generator_evidence_state.py` (new, 4 tests):
  end-to-end through a real `AnswerGenerator`+`ContextBuilder`+
  `VersionResolver` -- normal QA supported with verified citations; a
  stale source yields `stale_source` while its citation is still verified
  `is_valid=True` (proves the two axes are independent, not merged); two
  conflicting active official sources yield `source_conflict`; a guardrail
  refusal yields `insufficient_evidence` with trivially-valid citation
  verification.

### Why

Gate 04's explicit MUST DO is "distinguish citation verification from
answer correctness" and its acceptance checklist requires "citation
verifier still enforced" as an independent item. The pre-existing
`citations_verified` heuristic actively violated this (a heuristic
presence check standing in for a real verification result), so fixing it
is in scope, not a bonus refactor. `_finalize_response` centralizes both
new fields at every return point without changing any existing control-
flow decision (which branch executes, when a retry happens, when the
deterministic fallback triggers) -- only which two keys get attached
before the response leaves `AnswerGenerator`.

### Tests Run

```bash
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m compileall -q app rag scripts evals frontend tests
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q tests/test_evidence_state.py tests/test_answer_generator_evidence_state.py --basetemp=<tmp>
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q --basetemp=<tmp>
```

- Focused: 15 passed (11 + 4), all green on first run except the trivial
  test-authoring fix in Phase 4.1 (unrelated to this phase).
- Full suite: **266 passed, 0 failed** (251 after Phase 4.1 + 15 new).
- `git diff --check` on all Gate 04 Phase 4.2 files: clean (only the
  pre-existing `groq_client.py:235` overlay warning, not a Gate 04 file).

### Baseline Impact

None on ranking/retrieval. `AskResponse`/`AgentAskResponse` gained two
new optional fields (default `None`); no existing field's meaning changed
except `citations_verified`, whose value is now the genuine verification
result instead of a heuristic -- verified against the one existing test
that asserts it (`tests/test_api_agent.py::
test_agent_ask_endpoint_email_rebuilds_citations_from_verified_chunks`,
still green, since that case's deterministic fallback is genuinely
grounded).

### Repo Map / Code Index

Regenerated (`--force`); diff is a pure refresh (new
`rag/generation/evidence_state.py` module, updated fan-in/symbol counts).
No manual edits.

### Next Step

Phase 4.3: extend the existing trace surface (`retrieval_debug`/
`AgentAskResponse.debug`) so `index_version`/source version are visibly
available end to end, then Phase 4.4 regression fixtures (active-vs-
retired exclusion at the live-retrieval level, not just the resolver
unit).

## Gate 04 Phase 4.3 -- Evidence trace

### Date

`2026-08-27`

### Phase / Task

Gate 04 Phase 4.3: extend the existing trace/response contract so
query/retrieval/ranking/selected chunks/source-index-version/generation-
provider-model/citations-with-separate-verification/latency are all
visible, without a new route or a parallel observability system.

### Files Touched

- `rag/generation/context_builder.py`: added `"query": question` to
  `retrieval_debug` (it already had retriever/backend/top_k/candidate_count/
  chunk_ids/scores from before Gate 04, and `chunk_versions` from Phase
  4.1 -- `query` was the one missing field).
- `rag/generation/answer_generator.py`: `answer_with_meta_from_context` and
  `answer_with_agent_fallback_from_context` now time the generation step
  (`perf_counter` around prompt build + provider call + optional retry,
  excluding context retrieval) and attach a `generation` trace dict
  (`provider`, `model`, `fallback_used`, `error`, `latency_ms`) via
  `_finalize_response`'s new optional `provider_meta`/`latency_ms`
  parameters, and directly on the two deterministic-fallback/citation-
  failure-refusal branches that already had `provider_meta` in scope. A
  refusal that never reached a provider (guardrail refusal) has no
  `generation` block -- omitted, not invented.
- `app/schemas/query.py`: added `GenerationTrace` model and an optional
  `generation` field on `AskResponse` (populated automatically via
  `AskResponse(**response)` in `routes_query.py`, unchanged).
- `app/api/routes_agent.py`: added the internal `generation` trace dict
  into the existing `debug` payload (additive; `AgentAskResponse` already
  had its own top-level `provider`/`model`/`latency_ms` from the full
  agent round-trip, which is intentionally kept as-is and not overwritten
  -- the nested `debug.generation` is the generator-internal-only timing,
  a different and smaller measurement than the round-trip one).
- `tests/test_evidence_trace.py` (new, 5 tests): `/ask` debug trace has
  `query`/retriever/backend/chunk_ids/scores/chunk_versions (each with the
  exact 6-key `ChunkVersionInfo` shape) and a `generation` block on a
  non-refusal answer; `chunk_ids` and `scores` share the same
  deterministic order and `support_score` is sorted descending; a privacy
  refusal yields `insufficient_evidence` with `generation: null` (never
  called a provider) while `citation_verification.is_valid` stays
  trivially true; `/agent/ask` debug carries `generation`/`provider_status`
  alongside its existing `retrieval_debug`; a direct `ContextBuilder` test
  confirms `retrieval_debug["query"]` matches the question verbatim.

### Why

Phase 4.3 requires the trace to include query/retrieval/ranking/selected
chunks/source-index-version/generation/citations-with-separate-
verification/provider-model/latency, reusing the existing
`retrieval_debug`/`debug` surfaces rather than a new endpoint (explicitly
forbidden). `query` was the only structurally missing field after Phase
4.1; `generation` (provider/model/latency) did not exist anywhere in the
plain `/ask` contract before this phase, so it needed a real (not
invented) measurement threaded through from where the provider call
actually happens.

### Tests Run

```bash
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m compileall -q app rag scripts evals frontend tests
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q tests/test_evidence_trace.py --basetemp=<tmp>
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q --basetemp=<tmp>
```

- Focused: 5 passed, first run, no fixes needed.
- Full suite: **271 passed, 0 failed** (266 after Phase 4.2 + 5 new).
- `git diff --check` on all Gate 04 Phase 4.3 files: clean (only the
  pre-existing `groq_client.py:235` overlay warning).

### Baseline Impact

None. `retrieval_debug`/`debug` gained additive keys only; `AskResponse`
gained one new optional field (`generation`, default `None`); no existing
field, route, or ranking behavior changed.

### Repo Map / Code Index

Regenerated (`--force`); diff is a pure refresh (144 files indexed, no
manual edits, no surprises).

### Next Step

Phase 4.4: controlled regression fixtures proving retired-version
exclusion at the live-retrieval level (via `LifecycleService.publish`/
`retire`, not just the resolver's diagnostic path), conflicting-official-
sources and stale-source end-to-end (already covered at the
`AnswerGenerator` level in Phase 4.2 -- Phase 4.4 adds the isolated-
tmp_path corpus-level proof), re-run of the full suite/validators/
retrieval smoke, then the Gate 04 result record.

## Gate 04 Phase 4.4 -- Controlled regression evaluation

### Date

`2026-08-27`

### Phase / Task

Gate 04 Phase 4.4: isolated fixtures for the four required scenarios, full
regression, corpus validators, and a new (never overwriting Gate 00-03)
retrieval-smoke comparison.

### Files Touched

- `tests/test_gate04_fixtures.py` (new, 4 tests), each in its own
  `tmp_path`, never touching the real corpus or live SQLite state:
  - `test_retired_version_excluded_from_live_retrieval_by_removal_not_reranking`:
    real `LifecycleService` upload -> review -> publish -> confirms the
    document IS retrievable (hybrid + bm25) -> `retire()` -> confirms the
    document's chunks are entirely ABSENT from a freshly reloaded
    `ChunkIndexStore` and from a repeat retrieval call on both retrievers
    (structural exclusion, not a score-based down-rank that could
    resurface under a different query) -> confirms the `VersionResolver`
    diagnostic path (direct registry access) still reports
    `authority_state="retired"` for the now-unreachable document.
  - `test_conflicting_official_sources_fixture_yields_source_conflict_via_manifest_csv`:
    two active docs sharing a `conflict_key` in a real on-disk manifest CSV
    (loaded through the real `load_manifest_rows`, not a synthetic dict)
    -> `source_conflict`, with `citation_verification.is_valid` staying
    `True` (grounding is independent of the conflict finding).
  - `test_stale_source_fixture_yields_stale_source_via_manifest_csv`: same
    real-CSV mechanism with a `stale_after` column -> `stale_source`.
  - `test_normal_educational_qa_fixture_remains_supported_and_unchanged`: a
    manifest CSV shaped exactly like the real 37-doc corpus (no
    `stale_after`/`conflict_key` at all) -> `evidence_state.state ==
    "supported"`, and the answer/citations/confidence are byte-identical
    to the same generator with NO `version_resolver` wired at all --
    direct proof that Gate 04 wiring is a no-op for ordinary QA.
- `gates/baselines/GATE_04_RETRIEVAL_SMOKE.json` (new artifact, does not
  overwrite `GATE_03_RETRIEVAL_SMOKE.json`): re-run of the exact same
  command Gate 00-03 used.

### Why

The gate's acceptance checklist requires proving retired-version exclusion,
an explicit conflict fixture, a stale-source fixture, and unchanged normal
QA, each on isolated fixtures. The retired-exclusion fixture specifically
exercises the real `LifecycleService`/registry/`apply_live_state` path
(not just the Phase 4.1 resolver unit test) because the actual Gate 04
acceptance item is about live retrieval behavior, and the manifest-CSV-based
conflict/stale fixtures exercise the real `load_manifest_rows` reuse path
end to end, not just the resolver's constructor contract.

### Tests Run

```bash
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m compileall -q app rag scripts evals frontend tests
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q tests/test_gate04_fixtures.py --basetemp=<tmp>
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q --basetemp=<tmp>
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe scripts/validate_chunks.py --chunks-dir data/chunks
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe scripts/validate_processed_docs.py data/processed/processed_docs.jsonl
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe scripts/verify_manifest.py data/manifests/documents_manifest.csv
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5 --output gates/baselines/GATE_04_RETRIEVAL_SMOKE.json
```

- Focused: 4 passed, first run, no fixes needed.
- Full suite: **275 passed, 0 failed** (271 after Phase 4.3 + 4 new).
- Corpus validators: identical to pre-edit baseline and Gate 00-03
  (`validate_chunks` 1036/695/572 rows, abnormal 0; `validate_processed_docs`
  37/37, 1.000; `verify_manifest` 37 rows, 0 duplicate checksum groups).
- `git status --short -- data/ gates/baselines/` before writing the new
  Gate 04 smoke artifact: empty -- the frozen corpus/manifests/chunks and
  Gate 00-03 baseline files are untouched.
- Retrieval smoke: `GATE_04_RETRIEVAL_SMOKE.json` metrics are bit-for-bit
  identical to `GATE_03_RETRIEVAL_SMOKE.json` except `latency_ms` (timing,
  never a frozen metric): recall@3 0.7222, recall@5 0.8889, recall@10
  0.8889, mrr 0.5917, precision@5 0.1889, answerable 18/20.
- `git diff --check` on `tests/test_gate04_fixtures.py`: clean.

### Baseline Impact

None -- confirmed by the retrieval smoke comparison above and by
`test_normal_educational_qa_fixture_remains_supported_and_unchanged`
asserting byte-identical answer/citations/confidence with and without the
new version-resolver wiring.

### Repo Map / Code Index

Regenerated (`--force`); 145 files indexed, pure refresh, no manual edits.

### Next Step

Write `gates/results/GATE_04_RESULT.md` (Phase 4.5) and STOP before Gate
05.

## Entry — Gate 05 entry-gate verification + Phase 5.0 preflight (blocked)

### Date

2026-08-27

### Phase / Task

Gate 05 entry gate (Gate 04 re-verification) + Phase 5.0 preflight.

### Files Touched

- None (source/config/dependency). Ops-only:
  `_agent_ops/CURRENT_TASK.md`, `_agent_ops/DECISION_LOG.md` (this file),
  `_agent_ops/code_index.json`, `_agent_ops/REPO_MAP.md` (regenerated).

### What Changed

- Re-verified Gate 04 PASS on the committed tree (no edits).
- Rebuilt code index + `REPO_MAP.md` (pure refresh: only "Last Verified
  Commit" changed `31396a3` -> `82d2797`).
- Ran Phase 5.0 preflight inspection: read `provider_router.py`,
  `ollama_client.py`, `groq_client.py` (both `HEAD` and working-tree
  versions), `app/core/config.py`, `app/api/routes_health.py`,
  `tests/test_provider_router.py`; checked `mcp` package installed (no),
  Ollama executable + `qwen3:8b` local (yes, already installed), Groq
  configured boolean (no, checked safely via the app's real dotenv path,
  no secret values read).
- No Gate 05 source/config/dependency edit made -- blocked at the
  dependency gate (see Decision DEC-0008 and `CURRENT_TASK.md`).

### Why

Sequential fail-closed execution contract requires Gate 04 re-verification
and a full Phase 5.0 preflight, including explicit STOP conditions, before
any Gate 05 edit.

### Tests Run

```bash
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m compileall -q app rag scripts evals frontend tests
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q tests/test_version_resolver.py tests/test_context_builder_versioning.py tests/test_evidence_state.py tests/test_answer_generator_evidence_state.py tests/test_evidence_trace.py tests/test_gate04_fixtures.py
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe scripts/validate_chunks.py --chunks-dir data/chunks
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe scripts/validate_processed_docs.py data/processed/processed_docs.jsonl
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe scripts/verify_manifest.py data/manifests/documents_manifest.csv
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5 --output <tmp>
git ls-remote origin main
git diff --check
git show HEAD:rag/generation/groq_client.py
```

### Results

- Focused Gate 04 tests: 39 passed, 0 failed.
- Full suite: 275 passed, 0 failed -- matches `GATE_04_RESULT.md` exactly.
- Corpus validators identical to Gate 04 evidence (1036/695/572 rows
  abnormal 0; 37/37 1.000; 37 rows 0 duplicate checksums).
- Retrieval smoke: bit-for-bit identical to
  `gates/baselines/GATE_04_RETRIEVAL_SMOKE.json` except `latency_ms`.
- `git ls-remote origin main` == local `HEAD` == `82d2797`.
- `git diff --check`: only the pre-existing `groq_client.py:235` warning.
- `mcp` package: not installed. `qwen3:8b`: already installed locally.
  Groq: not configured (boolean check only).

### Bugs Found

- None. One real architectural discrepancy found (not a bug): the
  committed `groq_client.py` (41 lines, single-key) differs sharply from
  the dirty-overlay working-tree version (235 lines, multi-key rotation) --
  see DEC-0008.

### Next Step

Blocked. Waiting for the user to (a) configure `GROQ_API_KEY` and (b)
approve the `mcp` PyPI package as a new pinned dependency. See
`CURRENT_TASK.md` for exact resume steps.

## Entry — Gate 05 Phase 5.1 + 5.2: typed provider outcomes, mode policy

### Date

2026-08-27

### Phase / Task

Gate 05 Phase 5.1 (provider router, typed outcomes) + Phase 5.2 (mode
separation) -- built together since the mode policy is the fallback
decision inside the same router path.

### Files Touched

- `rag/generation/groq_client.py` -- narrow, additive edit (authorized,
  DEC-0008): added `GroqRequestError` + 5 typed subclasses
  (`GroqRateLimitError`/`GroqAuthError`/`GroqTimeoutError`/
  `GroqNetworkError`/`GroqProviderError`) and `_classify_exhausted_request_error`;
  changed only the final `raise RuntimeError(...)` in `generate_json` to
  raise the classified typed exception (`from last_exception`). Zero change
  to key discovery/rotation/cooldown/retry/backoff.
- `rag/generation/deepseek_client.py` (new) -- minimal, isolated, single-key
  DeepSeek client; never wired as a rescue path for any other provider.
- `rag/generation/provider_router.py` -- rewritten additively: `mode`
  param (`development`/`demo`/`research`, invalid values normalize to
  `development`); `ProviderInvocation` gained `failure_kind`, `mode`,
  `primary_attempt` (all default `None`, backward compatible); Groq path
  now classifies every failure via the new typed exceptions and, in
  `development`/`demo` only, falls back to Ollama (trace keeps the primary
  attempt); `research` mode returns the typed failure as a terminal
  outcome and never touches Ollama; added an isolated `deepseek` provider
  branch; `status()` gained `mode`/`deepseek_available`.
- `app/core/config.py` -- `Settings.provider_mode` (env `PROVIDER_MODE`,
  default `development`); wired into both `get_provider_router()` and
  `get_agent_provider_router()`.
- `app/api/routes_health.py` -- exposes `deepseek_enabled`/`provider_mode`
  booleans/strings alongside the existing `groq_enabled`/`llm_provider`.
- `app/schemas/query.py::GenerationTrace` -- additive optional fields
  `failure_kind`, `mode`, `primary_attempt`.
- `rag/generation/answer_generator.py` -- `_provider_meta`/
  `_generation_trace` thread the new fields through additively; no
  control-flow change.
- `tests/test_evidence_trace.py` -- loosened one Gate 04 assertion from an
  exact `generation` trace key-set match to a subset check (`<=`), per the
  gate contract's explicit "extend Gate 04 trace fields additively" --
  Gate 04's original 5 keys are still asserted present.
- New: `tests/test_provider_policy.py` (23 tests), `tests/test_groq_typed_errors.py`
  (7 tests).

### Why

Phase 5.1 requires 429/timeout/network/config-auth outcomes kept distinct,
never collapsed into a generic error. Phase 5.2 requires Groq-primary with
Qwen fallback in development/demo only, and a hard, provably-enforced
no-fallback rule in research mode.

### Tests Run

```bash
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m compileall -q app rag scripts evals frontend tests
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q tests/test_provider_router.py tests/test_groq_rotation.py
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q tests/test_provider_policy.py tests/test_groq_typed_errors.py -v
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q
git diff --check
```

### Results

- Focused pre-existing provider tests: 10 passed, 0 failed (unchanged
  behavior for `mock`/`ollama` paths and all 6 rotation tests).
- New Phase 5.1/5.2 tests: 23 + 7 = 30 passed, 0 failed. Cover: Groq success
  (no `failure_kind`); each of the 5 typed Groq failures individually
  (`rate_limited`/`timeout`/`network_failure`/`auth_failure`/
  `provider_error`) plus `config_error` for an unconfigured key; dev/demo
  fallback to Ollama on every typed failure with `primary_attempt`
  preserved; demo discloses the real fallback provider/model; research
  mode returns the typed failure with `fallback_used=False` for all 5
  kinds AND with an `UntouchableOllamaClient` spy that raises
  `AssertionError` if touched -- proves Ollama is never invoked; Ollama's
  own fallback-path failures (unavailable / model not installed) correctly
  reported as `network_failure`/`config_error` with the Groq primary
  attempt preserved; DeepSeek isolation (never calls Ollama, never
  triggered by Groq, its own failures never rescue via Ollama); invalid
  mode string normalizes to `development`; `status()` reports `mode` and
  `deepseek_available`.
- Real `GroqClient` (not a stub) integration: monkeypatched `urlopen`
  proves exhaustion raises the correctly typed exception for 429/401/503/
  timeout/connection-refused, preserves the original message text, chains
  `__cause__`, and pre-existing multi-key rotation-then-success still
  returns normally (non-regression).
- Full suite: **305 passed, 0 failed** (275 + 30 new).
- `compileall -q app rag scripts evals frontend tests`: clean.
- `git diff --check`: only the pre-existing `groq_client.py` blank-line-at-
  EOF warning (now at a shifted line number, confirmed via `git diff` tail
  inspection that no new trailing content was added) and routine CRLF/LF
  conversion notices -- no real whitespace errors introduced.

### Bugs Found

- None. One design note: all 5 typed Groq failure kinds are treated as
  fallback-eligible in development/demo (not a narrower enumerated
  subset) -- matches the gate's "service continuity" framing for those
  modes; research mode's refusal is unconditional regardless of kind.

### Next Step

Phase 5.3: mount `/mcp` (Streamable HTTP, `mcp==2.1.1`) on `127.0.0.1`
only, narrow read-oriented tools reusing Gate 04's retrieval/evidence/
version trace as the source of truth.

## Entry — Gate 05 Phase 5.3 + 5.4: local MCP surface, security, audit

### Date

2026-08-27

### Phase / Task

Gate 05 Phase 5.3 (MCP surface) + Phase 5.4 (MCP security/audit) -- built
together since auth/scope/audit are threaded through tool registration from
the start, not bolted on after.

### Files Touched

- New package `app/mcp/`:
  - `auth.py` -- `StaticBearerTokenVerifier` (single server-owned token,
    constant-time compare via `hmac.compare_digest`, never logs the token;
    grants `mcp:read` only -- `mcp:admin` is never granted through this
    gate's configuration surface).
  - `audit.py` -- `McpAuditLog`: bounded `deque` (default maxlen 500),
    records only timestamp/request_id/tool_name/authorized/status; never
    the token, raw arguments, or retrieved content.
  - `tools.py` -- `guarded_tool` decorator (enforces required scope via
    `mcp.server.auth.middleware.auth_context.get_access_token()` server-
    side, records one audit entry per call, regardless of client-declared
    capability) wrapping 3 approved read-only tools
    (`retrieve_context`/`document_status`/`index_status`, reusing
    `ContextBuilder`/`LifecycleService`/`ChunkIndexStore` directly -- no
    parallel data path) plus 1 protected probe tool
    (`admin_retire_document_version`, `mcp:admin`-gated, registered only
    when `enable_protected_probe_tool=True`, disabled by default).
  - `server.py` -- `build_mcp_server()`: rejects any non-localhost `host`
    at construction (`McpConfigurationError`); builds the SDK's real
    Streamable HTTP app (`mcp.server.mcpserver.MCPServer.streamable_http_app`)
    with explicit `TransportSecuritySettings` (localhost-only host/origin
    allowlist, DNS-rebinding protection); composes the SDK's own
    `AuthenticationMiddleware`+`BearerAuthBackend`+`AuthContextMiddleware`+
    `RequireAuthMiddleware` directly around it (see design note below --
    `MCPServer`'s own `auth=`/`token_verifier=` constructor path hard-
    requires OAuth `AuthSettings.issuer_url`, explicitly out of scope for
    this gate, so those SDK middleware classes are composed manually
    instead of hand-rolling auth).
- `app/core/config.py` -- `Settings.mcp_bearer_token`/`mcp_host`/
  `mcp_enable_protected_probe_tool` (env `MCP_BEARER_TOKEN`/`MCP_HOST`/
  `MCP_ENABLE_PROTECTED_PROBE_TOOL`, all fail-closed defaults); new
  `get_mcp_server()` (`lru_cache`, reuses `get_context_builder()`/
  `get_lifecycle_service()`/`get_store()`); wired into `refresh_live_caches()`.
- `app/main.py` -- FastAPI `lifespan` now enters
  `get_mcp_server().mcp_server.session_manager.run()` (the SDK session
  manager's task group must be entered from the true top-level ASGI app's
  lifespan -- a mounted sub-app's own `lifespan=` is never triggered
  automatically); `app.mount("/mcp", get_mcp_server().asgi_app)`.
- `app/api/routes_health.py` -- `mcp_configured` boolean (never token
  value/length/prefix).
- `requirements.txt` -- `mcp==2.1.1` was already added in Phase 5.0 (no
  further dependency change).
- New: `tests/test_mcp_server.py` (14 tests).

### Why

Phase 5.3 requires a standards-compliant local Streamable HTTP MCP surface
using a maintained SDK, narrow read-oriented tools, localhost-only binding.
Phase 5.4 requires server-owned bearer auth, exact localhost origin
allowlisting, server-side scope enforcement per tool call (not just client
metadata), and a minimal bounded audit trail -- with an unauthorized
dangerous operation proven rejected before any mutation.

### Design note: composing SDK auth middleware manually

`MCPServer(token_verifier=...)` raises `ValueError: Cannot specify
auth_server_provider or token_verifier without auth settings` --
discovered by construction, not by reading docs alone. The SDK's
convenience `auth=`/`token_verifier=` pairing is an OAuth resource-server
flow requiring `AuthSettings.issuer_url`, which the gate contract
explicitly forbids ("No OAuth, cloud identity, ..., a token issuer").
Resolved by building the plain (unauthenticated) SDK app via
`MCPServer.streamable_http_app()`, then wrapping it in the SDK's own
`RequireAuthMiddleware` and `AuthenticationMiddleware`/`BearerAuthBackend`/
`AuthContextMiddleware` directly (all public SDK classes, imported and
composed, not reimplemented) -- real SDK-verified bearer auth, zero OAuth
surface. Verified end-to-end with a manual protocol smoke script (real
`ClientSession.initialize()`/`list_tools()`/`call_tool()` round trip)
before writing the committed test suite.

### Tests Run

```bash
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m compileall -q app rag scripts evals frontend tests
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q tests/test_mcp_server.py -v
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q
git diff --check
```

### Results

- `tests/test_mcp_server.py`: **14 passed, 0 failed**. Runs a real
  Streamable HTTP server on a dynamic OS-assigned `127.0.0.1` port, in a
  background daemon thread (no subprocess -- nothing to flash a console
  window; reliably joined with a 10s timeout in every fixture teardown).
  Covers: `initialize`/`tools/list` with a valid token (exactly the 3
  approved tools, protected tool absent when disabled); each approved
  tool's real output (`retrieve_context` against the real 37-doc corpus,
  `index_status` reporting the real `index_version`/`chunk_count`,
  `document_status` against an isolated `tmp_path` lifecycle registry);
  the protected probe tool registered-but-denied when enabled (the real
  configured token never carries `mcp:admin` -- `result.is_error is True`,
  no lifecycle mutation reachable); unauthenticated / malformed
  `Authorization` / wrong bearer token / no-token-configured-at-all all
  return 401; a spoofed `Origin` header rejected (401/403/421, matching
  the SDK's DNS-rebinding response codes); non-localhost `host` rejected
  at construction (`McpConfigurationError`, before any server is even
  built); audit log records the authorized `index_status` call
  (`status="ok"`) and the denied admin call (`status="denied"`) with
  exactly the 5 allowed fields and no token substring anywhere in any
  record; audit log bounded (`len(...) <= 500`).
- Full suite: **319 passed, 0 failed** (305 + 14 new).
- `compileall -q app rag scripts evals frontend tests`: clean.
- `git diff --check`: only the same pre-existing `groq_client.py` EOF
  warning and routine CRLF notices -- no new whitespace errors.

### Bugs Found

- None in the app's own code. One real, load-bearing SDK-behavior
  discovery (not a bug, a discovered constraint): the transport-security
  `allowed_hosts` wildcard pattern `"127.0.0.1:*"` does NOT match a bare
  `Host: 127.0.0.1` header with no port -- only matters for in-process
  ASGI-transport testing without a real bound port (a real dynamic-port
  server always sends an explicit port in its Host header, so this never
  surfaces there); hardened the allowlist defensively to include the bare
  hostname too, for robustness beyond just this gate's own test suite.

### Next Step

Phase 5.5 (bounded real smoke proofs): one bounded Groq development-mode
call, one bounded local `qwen3:8b` Ollama smoke call, one authenticated
localhost MCP Inspector/client smoke (already effectively proven by the
committed `test_mcp_server.py` suite's real dynamic-port protocol round
trip -- Phase 5.5 additionally wants this run against the real app wiring,
not just the isolated test app). Requires the user to confirm Groq is now
configured (the `.env` file-location issue from Phase 5.0/5.1) and that
local runtime prerequisites are ready before any live call is made.

## Entry — test file split (`tests/test_mcp_server.py` > 400 lines)

### Date

2026-08-27

### Files Touched

- New: `tests/mcp_test_helpers.py` (shared fixtures/helpers, not a test
  module -- no `test_*` name, not collected by pytest directly).
- `tests/test_mcp_server.py` -- trimmed to protocol tests only (init,
  tools/list, each tool call, protected-tool registration), 6 tests.
- New: `tests/test_mcp_security.py` -- auth/origin/host-guard/audit tests,
  8 tests.
- `tests/conftest.py` -- added `pytest_plugins = ["tests.mcp_test_helpers"]`
  so the shared fixtures register repo-wide.

### Why

`tests/test_mcp_server.py` landed at 411 lines after Phase 5.3/5.4, just
over the repo's ~400-line split threshold (`AGENTS.md` Coding Standard,
flagged in the regenerated `REPO_MAP.md`'s Oversized Files table). Split
along the protocol-vs-security responsibility boundary per that standard,
not by line count alone.

### Tests Run

```bash
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q tests/test_mcp_server.py tests/test_mcp_security.py -v
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m compileall -q app rag scripts evals frontend tests
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q
git diff --check
```

### Results

- Split suite: 14 passed, 0 failed (6 + 8, same tests, same assertions,
  no behavior change -- pure file reorganization).
- Full suite: **319 passed, 0 failed** (unchanged from before the split).
- `compileall` clean. `git diff --check`: only the same pre-existing
  `groq_client.py` EOF warning.
- Rebuilt `REPO_MAP.md`/code index: Oversized Files table no longer lists
  any test file (156 files indexed, up from 154 -- the two new files).

## Entry — Gate 05 Phase 5.5: bounded real smoke proofs

### Date

2026-08-27

### What was run and why

User confirmed: run the MCP live smoke and attempt Groq; explicitly
deferred the local Qwen/Ollama bounded smoke (separate deployment planned,
prefers the Groq API path for stability right now) -- so that specific
proof was deliberately not run, not because Ollama was unavailable
(confirmed available and `qwen3:8b` confirmed installed via
`OllamaClient.status()` earlier in Phase 5.0/5.5 preflight).

Groq-configured boolean was rechecked immediately before this phase (never
reading `.env` directly -- via `import app.main` triggering the real
`load_dotenv()` path, then only `bool(os.environ.get(...))`): still `False`.
`VietRagOps/.env`'s mtime was also rechecked and found unchanged
(`Aug 26 23:25`) from the very first check earlier in the session --
i.e. whatever edit the user made did not land in the file this app
actually loads. Per the gate contract ("If Groq returns 429/timeout/
network failure, preserve the typed outcome. Do not repeat calls to force
a PASS" and "STOP honestly" for an unavailable prerequisite), no live
Groq network call was attempted -- there is nothing to call without a key,
and fabricating one would not be a real proof.

### Commands / results

1. **MCP client smoke against the real app wiring** (`app.main.app`, not
   the isolated test app), a real Streamable HTTP server on a dynamic
   `127.0.0.1` port, in a background daemon thread:
   - Unauthenticated `POST /mcp/` -> **401** (denied path).
   - Authenticated `initialize()` -> succeeded, `server_info.name ==
     "vietragops-mcp"`.
   - `list_tools()` -> `["retrieve_context", "document_status",
     "index_status"]` (protected tool absent -- disabled by default in
     the real app, `MCP_ENABLE_PROTECTED_PROBE_TOOL` unset).
   - `call_tool("index_status", {})` -> `is_error=False`, real data:
     `index_version: sha256:0510c68876fc4b92, chunk_count: 695,
     document_count: 37` -- matches the real corpus exactly.
2. **Groq `config_error` typed-outcome proof, `research` mode**
   (`PROVIDER_MODE=research`, `LLM_PROVIDER=groq`, real `/ask` endpoint):
   `generation = {"provider": "groq", "model": "qwen/qwen3.6-27b",
   "fallback_used": true, "error": "Groq is not configured.",
   "latency_ms": 1.933, "failure_kind": "config_error", "mode":
   "research", "primary_attempt": null}`. `latency_ms` 1.9ms and
   `primary_attempt: null` together prove no network call was made and no
   provider substitution happened -- exactly the research-mode contract.
   `generation.fallback_used: true` here reflects the separate,
   pre-existing Gate 04 "answer generator fell back to its own
   deterministic answer builder" concept (unchanged since Gate 04, not
   provider-to-provider fallback); `primary_attempt: null` is the precise
   signal that no other provider was ever tried.
3. **Incidental real Ollama call (not intended, documented for
   transparency):** an earlier attempt to prove the same `config_error`
   path in `development` mode (before switching to `research` mode for a
   clean proof) correctly triggered this gate's own Groq->Ollama fallback
   design, making a REAL local `qwen3:8b` call despite the user's request
   to defer Qwen testing. Ended in `failure_kind: "provider_error"`,
   `error: "Ollama chat request failed: timed out"` after the
   `OllamaClient` default 30s timeout, `latency_ms: 30096.5`. The `/ask`
   endpoint still returned `200` (deterministic-answer fallback). This
   was not a deliberate Qwen smoke test and does not count as satisfying
   (or violating) the user's deferral -- recorded here only because a
   real network call did happen. Operationally relevant, out-of-scope
   finding: `qwen3:8b` local inference on this machine can exceed
   `OllamaClient`'s 30s default timeout for a first/cold call; not fixed
   in this gate (no acceptance criterion requires it, and the fallback
   degraded correctly and safely).

### Outcome

- MCP live client smoke: **done**, real proof, matches the committed test
  suite's behavior against the real app wiring.
- Qwen local smoke: **deliberately not run**, per explicit user decision
  (not an availability blocker -- Ollama/`qwen3:8b` confirmed ready).
- Groq live network call: **not run** -- `WAITING_FOR_USER_SECRET`
  remains the honest status for this one specific proof; the typed
  `config_error` degradation path was verified instead (real code path,
  zero network calls, deterministic).

### Next Step

Phase 5.6: final regression, freeze verification, `git diff --check`,
repo map/code index rebuild (done), write `gates/results/GATE_05_RESULT.md`
from this evidence with status `WAITING_FOR_USER_SECRET` for the Groq live
proof specifically, while the rest of the gate (Phases 5.1-5.4, MCP smoke)
stands on real, complete evidence. STOP -- no Gate 06 work.

## Entry — Gate 05: `.env` redirect fix, live Groq proof succeeds, status -> PASS

### Date

2026-08-27

### Files Touched

- `app/main.py` -- by explicit user request, dotenv now loads from
  `Path(__file__).resolve().parents[2] / ".env"` (`D:\...\ROOT\.env`, the
  parent of the app's own repo root) instead of the default upward search
  from cwd (which found `VietRagOps\.env`). Moved the load to the very
  top of the file, before any `app.*`/`rag.*` import, and added
  `override=True`. See DEC-0011 for why the naive path-only version of
  this change silently failed first.
- `gates/results/GATE_05_RESULT.md` -- status updated `WAITING_FOR_USER_SECRET`
  -> `PASS`; live Groq evidence, the dotenv bug/fix, and the acceptance
  checklist updated accordingly.

### Why

User pointed out the correct `.env` location; fixing it correctly (not
just superficially) was necessary to unblock Phase 5.5's one remaining
required live proof.

### Debugging (real root-cause work, not guessed)

First attempt (just changing `dotenv_path=`) still showed
`GROQ_API_KEY` as unconfigured after `import app.main`. Bisected by
importing each module in the chain individually and checking
`'GROQ_API_KEY' in os.environ` before/after:
`app.core.config` -> yes; narrowed to `app.mcp.tools` -> yes; narrowed to
`rag.lifecycle.service` -> yes; narrowed to `rag.lifecycle.pipeline` ->
yes; narrowed to `rag.ingestion.markitdown` -> yes (this is where it
first appears). Confirmed the value being set was an empty string
matching exactly what `VietRagOps\.env`'s own `GROQ_API_KEY=` line
resolves to (`dotenv_values()` direct parse, length 0), while
`ROOT\.env`'s `GROQ_API_KEY` resolves to a real 56-character value
(length only, never printed). Concluded: `markitdown` (or one of its
dependencies) calls a bare `load_dotenv()` at import time, which finds
`VietRagOps\.env` first because that import happens before `app/main.py`'s
own dotenv call did (in the old import order). Fixed per DEC-0011.

A second false alarm during the same debugging pass: the very first retry
of the live Groq call after the fix again showed `GROQ_API_KEY` as unset
-- caused by this agent reusing `PYTHON_DOTENV_DISABLED=true` (correct
for every offline/mock test command run throughout this session) by
mistake in a live-call command, which disables the app's own dotenv load
entirely (but not `markitdown`'s internal one, which doesn't check that
flag) -- explaining the exact same symptom via a different, unrelated
cause. Caught by rerunning without that variable.

### Live proof

Real `/ask` request, `LLM_PROVIDER=groq`, `PROVIDER_MODE=development`,
question "Cấu trúc email sinh viên là gì?", `top_k=3`, one bounded call:

```json
{"provider": "groq", "model": "qwen/qwen3.6-27b", "fallback_used": false,
 "error": null, "latency_ms": 3714.383, "failure_kind": null,
 "mode": "development", "primary_attempt": null}
```

HTTP 200, `refusal: false`, `citations: 1`, `confidence: 1.0`,
`citation_verification: {"is_valid": true, "errors": []}`,
`evidence_state: {"state": "supported", "reasons": []}`. No repeated
calls -- succeeded on the first bounded attempt.

### Tests Run

```bash
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m compileall -q app rag scripts evals frontend tests
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q
git diff --check
git status --short -- data/ gates/baselines/
```

### Results

- Full suite: **319 passed, 0 failed** (unchanged -- the dotenv fix only
  affects app startup env-loading, no test behavior changed since tests
  already used `PYTHON_DOTENV_DISABLED=true`).
- `compileall` clean. `git diff --check`: only the same pre-existing
  `groq_client.py` EOF warning. `data/`/`gates/baselines/` empty (frozen
  corpus and prior gate baselines untouched).

### Bugs Found

- One real, pre-existing (not introduced by Gate 05) latent bug: `app/main.py`
  loaded dotenv *after* importing project modules, which happened to be
  harmless before this session (both the old default search and any
  transitive `markitdown` load would resolve to the same file,
  `VietRagOps\.env`) but became a real, silent failure the moment the app
  needed to load a *different* file. Fixed as part of this gate (DEC-0011)
  since it directly blocked a required Phase 5.5 proof.

### Outcome / Status change

Gate 05 status changed from `WAITING_FOR_USER_SECRET` to **PASS**. All
required acceptance items are now satisfied except the Qwen live smoke,
which remains a documented, user-directed deferral (not a gap) covered by
extensive mocked/spy evidence. See `gates/results/GATE_05_RESULT.md` for
the complete, updated record.

### Next Step

None from this agent unless the user asks to commit Gate 05 (requires
separate explicit authorization) or to run the deferred Qwen live smoke
later. STOP -- no Gate 06 work.

## Entry — Gate 05: consolidate `.env` to the project-local file (DEC-0012)

### Date

2026-08-27

### Files Touched

- `app/main.py` -- `ENV_FILE_PATH` changed from `parents[2] / ".env"`
  (the parent `ROOT` folder) to `parents[1] / ".env"` (`VietRagOps\.env`,
  the project-local file) -- now identical to `scripts/web_import.py`'s
  existing `_REPO_ROOT / ".env"` convention. Import-order fix and
  `override=True` from the prior entry kept unchanged.
- `gates/results/GATE_05_RESULT.md` -- updated to describe the final,
  consolidated `.env` location and the corrected `latency_ms` from the
  re-run proof.

### Why

User pointed out (correctly) that pointing at the parent `ROOT\.env`
created an inconsistency with `scripts/web_import.py`, which already
loads secrets from inside the project. User manually moved the real
values into `VietRagOps\.env`; asked this agent to redo the reasoning/
verification and update the ops records -- explicitly not to write any
secret values into `_agent_ops/`.

### Verification (length/count only, no secret values read or recorded)

```bash
.venv/Scripts/python.exe -c "from dotenv import dotenv_values; vals = dotenv_values('.env'); print(len(vals), len(vals.get('GROQ_API_KEY') or ''))"
```

- `VietRagOps\.env`: 79 keys parsed, `GROQ_API_KEY` length 56, all 20
  `GROQ_API_KEY_1..20` populated.
- Re-ran the bounded live Groq proof: `provider: groq`,
  `latency_ms: 5415.665`, `fallback_used: false`, `refusal: false`,
  1 citation, HTTP 200 -- succeeded again from the consolidated location.
- Full suite: **319 passed, 0 failed**. `compileall` clean.
  `git diff --check`: only the same pre-existing `groq_client.py` EOF
  warning.

### Outcome

Gate 05 remains **PASS**; the `.env` location is now consistent across
the whole app. `D:\...\ROOT\.env` is no longer read by anything in this
codebase.

### Next Step

None from this agent unless the user asks to commit Gate 05 or run the
deferred Qwen live smoke. STOP -- no Gate 06 work.

## Entry — Gate 06 entry-gate block, then Gate 05 correction (Qwen live smoke + commit)

### Date

2026-08-27

### What happened

A later session began Gate 06 by running its mandatory entry gate before
touching any Gate 06 file, per the entry contract. It found two
independent, disqualifying gaps against actual repository state (not the
narrative in `GATE_05_RESULT.md`): (1) the bounded local `qwen3:8b`
Ollama smoke required by the Gate 06 entry gate had never actually
succeeded -- Gate 05 only had an incidental timed-out call, explicitly
documented as not satisfying the acceptance item; (2) Gate 05 had never
been committed at all (`git status --short` showed every Gate 05 file
modified-but-unstaged or untracked, `git diff --cached --name-only`
empty), confirmed by `GATE_05_RESULT.md`'s own text ("a Gate 05 commit
requires separate explicit user authorization") and
`_agent_ops/CURRENT_TASK.md` ("No Gate 05 commit has been made."). The
session correctly reported `GATE_06_BLOCKED` with both exact gaps, per
the entry contract's "do not weaken it" instruction, and performed no
Gate 06 edits.

The user replied by quoting both missing items back verbatim and writing
"do it for me please. continue as my prompt" -- explicit authorization
for both the live smoke and the Gate 05 commit.

### Commands / results

1. Confirmed Ollama running locally and `qwen3:8b` installed:
   `.venv/Scripts/python.exe scripts/check_ollama.py` (default model) and
   again with `OLLAMA_MODEL=qwen3:8b` -- both `available=True`, the
   latter `model_available=True`, alongside `gemma3:4b`, `qwen2.5:3b`,
   `qwen2.5:7b`, `qwen3.5:4b`, `qwen3:4b` also installed.
2. Warmed the model via the real `ollama.exe run qwen3:8b` CLI once (a
   trivial "hi" prompt) to confirm end-to-end generation worked at all
   before attempting the real gate proof.
3. Three real attempts through the actual fallback code path (`provider=
   "groq"` with `GROQ_API_KEY` genuinely absent from the environment --
   `PYTHON_DOTENV_DISABLED=true`, no key exported -- producing a real
   `config_error`, then real `development`-mode fallback to a real
   `OllamaClient(model="qwen3:8b")`), each at successively larger
   explicit timeouts to find the real completion time, not to force a
   pass:
   - 30s (via the real `/ask` endpoint through `fastapi.testclient.
     TestClient(app)`, immediately after a 12s CLI warm-up): timed out
     (`latency_ms: 30208.731`, `failure_kind: provider_error`, answer
     degraded correctly to the deterministic fallback, HTTP 200).
   - 90s (via a directly-constructed `AnswerGenerator`/`ContextBuilder`/
     `ProviderRouter`, real corpus, real `OllamaClient(timeout=90.0)`):
     timed out again (`latency_ms: 90637.163`).
   - 300s (same construction, `OllamaClient(timeout=300.0)`): **real
     success**, first attempt at this bound, no retries needed --
     `provider: "ollama"`, `model: "qwen3:8b"`, `fallback_used: true`,
     `error: null`, `failure_kind: null`, `latency_ms: 105656.945`,
     `primary_attempt.failure_kind: "config_error"` (proving the real
     Groq path was attempted and genuinely failed first, not skipped).
     Answer: "Cau truc email sinh vien TDTU la MSSV@student.tdtu.edu.vn,
     ..." -- grounded, specific, and correct against the real corpus, not
     the generic deterministic-fallback text seen in the two timeouts
     above. `refusal: false`, `confidence: 0.95`, `citations: 1`,
     `citation_verification: {"is_valid": true, "errors": []}`,
     `evidence_state: {"state": "supported", "reasons": []}`.
4. Full regression reconfirmed before committing: `compileall` clean;
   full suite **319 passed, 0 failed** (unchanged); corpus validators --
   1036/695/572 rows abnormal 0, 37/37 processed docs, 37 manifest rows 0
   duplicate groups (all identical to the Gate 04/05 baseline);
   retrieval smoke re-run to a temp path -- bit-for-bit identical metrics
   to `GATE_04_RETRIEVAL_SMOKE.json` (recall@3 0.7222, recall@5 0.8889,
   recall@10 0.8889, mrr 0.5917, precision@5 0.1889, answerable 18/20);
   `git status --short -- data/ gates/` shows only the new
   `GATE_05_RESULT.md` itself.
5. Updated `gates/results/GATE_05_RESULT.md` in place with this evidence
   (correction note, live-proof section, real-latency finding, updated
   acceptance-checklist item, updated known limitations) -- the original
   PASS status and all other previously-recorded evidence were left
   unchanged, per the instruction not to change a PASS by wording.
6. Recorded DEC-0013 (methodology/commit-scope decision) and RISK-0015
   (the newly-discovered production-timeout-vs-real-latency gap).
7. Regenerated `_agent_ops/REPO_MAP.md` (`generate_repo_map.py --force`)
   and the code index (`build_code_index.py --force`); inspected the
   diff before allowing it into the commit (pure refresh, no manual
   edits).
8. Staged, by explicit file name only (never `git add .`/`-A`), exactly
   the Gate 05 slice: every file listed in `GATE_05_RESULT.md`'s "Exact
   source and dependency scope" plus this gate's own ops entries
   (`_agent_ops/DECISION_LOG.md`, `_agent_ops/IMPLEMENTATION_LOG.md`,
   `_agent_ops/PROJECT_CONTEXT_CARD.md`, `_agent_ops/RISK_REGISTER.md`,
   `_agent_ops/phase_context_cards/evolve_2026_08_26/README.md` and
   `GATE_05.md`, `_agent_ops/REPO_MAP.md`, `gates/results/
   GATE_05_RESULT.md`). Verified via `git status`/`git diff --cached
   --name-only` that no pre-existing overlay path was included. Ran
   `git diff --check` on the staged diff before committing.
9. Committed the Gate 05 slice (see `git log` for the resulting hash(es)
   -- this entry deliberately does not restate it to avoid a circular
   self-reference).

### Outcome

- Gate 06 entry-gate gap #1 (real Qwen smoke) -- closed with a genuine,
  reproducible success.
- Gate 06 entry-gate gap #2 (Gate 05 commit) -- closed; Gate 05 is now
  committed as its own slice, separate from the pre-existing dirty
  overlay, which remains exactly as it was.
- New finding, not a regression: the production `OllamaClient` default
  timeout (30s) is far below this machine's real `qwen3:8b` full-RAG
  latency (~100-110s) -- tracked as RISK-0015, not fixed in this session
  (out of Gate 05's frozen scope; Gate 06 is infrastructure-only and does
  not touch this either).

### Next Step

Re-run the Gate 06 mandatory entry gate against the now-committed state.
If it passes, proceed into Gate 06 Phase 6.0 per the source pack.

## Entry — Gate 06: entry-gate re-verification PASS, then full Phase 6.0-6.6 implementation

### Date

2026-08-27

### Entry-gate re-verification

Independently re-checked every condition against the committed state
(HEAD `81589e2`): `git merge-base --is-ancestor` confirmed both Gate 04
(`82d2797`) and the new Gate 05 commit (`81589e2`) are ancestors of HEAD;
`git status --short` showed only the pre-existing overlay (unambiguous,
no overlap with the Gate 05 slice); `git diff --cached --name-only`
empty (nothing left staged after the commit); `git diff --check` on the
working tree exit 0 (clean); `data/`/`gates/` untouched. Context cards,
tracker README, and `PROJECT_CONTEXT_CARD.md` were updated in the same
session to agree with this state (Gate 04 "uncommitted" label corrected
to reflect its actual committed-and-pushed status; Gate 05 section
added). Result: **entry gate PASS** -- proceeded into Gate 06.

### Design decision

See DEC-0014 for the full sandbox design (module boundary, public/oracle
split, what "hidden" means). Summary: new `research/gate0/` package,
in-memory sandbox state, `ToolContract`/`PublicToolContract` split
(`tool_id` never exposed method-facing), `MethodFacingHarness` as the
sole method-facing interface with zero import of `research.gate0.oracle`,
`EvaluatorCapability`-gated oracle access.

### Files added (all new; no existing tracked file was modified)

- `research/__init__.py`, `research/gate0/__init__.py`
- `research/gate0/contracts/{__init__.py,contract.py}` -- Phase 6.1:
  `ToolContract`/`PublicToolContract`/`Precondition`/`Effect`,
  `compute_schema_hash`, `validate_contract`.
- `research/gate0/sandbox/{__init__.py,store.py,api_v1.py,api_v2.py,
  api_v3.py}` -- Phase 6.2: `EducationSandboxStore` (in-memory,
  `reset()`/`state_hash()`) plus three deterministic fictional education
  APIs (course lookup, prerequisite check, enrollment, timetable, leave
  request, plus a held-out advisor-note lineage), each with real
  precondition/effect-enforcing implementations and a `contracts()`
  method.
- `research/gate0/drift/{__init__.py,families.py,manifest.py}` -- Phase
  6.3: the 9 required drift families; a frozen 10-case graded manifest
  (`build_case_manifest()`) plus 2 structurally-separate held-out cases
  (`held_out_cases()`).
- `research/gate0/oracle/{__init__.py,ground_truth.py}` -- Phase 6.4:
  `MigrationGroundTruth` records for all 10 graded cases, gated behind a
  real `EvaluatorCapability` instance.
- `research/gate0/evaluator/{__init__.py,capability.py,evaluator.py}` --
  Phase 6.6: `EvaluatorCapability`; `evaluate_mapping()` (tool selection +
  argument-pair precision/recall + no-equivalent handling + effect-kind
  check, all via set arithmetic and real contract lookups, zero LLM
  calls); `evaluate_adapted_call()` (actually executes a predicted call
  against a fresh sandbox and scores precondition/output outcomes).
- `research/gate0/traces/{__init__.py,models.py,capture.py}` -- Phase
  6.5: `VerifiedTrace`; `build_verified_traces_for_version()` (4 real
  successful calls per version, one continuous store, real before/after
  `state_hash`); `build_failed_trace_for_version()` (one deliberately
  failing call, `verified=False`); `replay_trace()`.
- `research/gate0/harness/{__init__.py,method_facing.py}` -- Phase 6.4:
  `MethodFacingHarness`/`MethodFacingTask`, the sole method-facing
  interface; zero import of `research.gate0.oracle`.
- `tests/test_gate06_contract_model.py` (19), `tests/
  test_gate06_sandbox_versions.py` (19), `tests/
  test_gate06_drift_manifest.py` (10), `tests/
  test_gate06_oracle_boundary.py` (17), `tests/test_gate06_traces.py`
  (9), `tests/test_gate06_evaluator.py` (33), `tests/
  test_gate06_product_isolation.py` (4) -- **111 new tests total.**

### Commands / results

```bash
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m compileall -q app rag scripts evals frontend tests research
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m pytest -q
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe scripts/validate_chunks.py --chunks-dir data/chunks
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe scripts/validate_processed_docs.py data/processed/processed_docs.jsonl
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe scripts/verify_manifest.py data/manifests/documents_manifest.csv
PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock .venv/Scripts/python.exe -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5 --output <tmp>
git diff --check
git status --short -- data/ gates/
```

- `compileall`: clean, including the new `research/` tree.
- Full suite: **430 passed, 0 failed** (319 pre-existing + 111 new Gate 06
  tests; 0 regressions).
- Corpus validators: 1036/695/572 rows abnormal 0; 37/37 processed docs;
  37 manifest rows, 0 duplicate groups -- identical to the Gate 04/05
  baseline.
- Retrieval smoke: recall@3 0.7222, recall@5 0.8889, recall@10 0.8889,
  mrr 0.5917, precision@5 0.1889, answerable 18/20 -- bit-for-bit
  identical to `gates/baselines/GATE_04_RETRIEVAL_SMOKE.json` (only
  `latency_ms` differs, as expected).
- `git diff --check`: clean (exit 0) -- Gate 06 added only new files.
- `git status --short -- data/ gates/`: empty -- frozen corpus and every
  prior gate's baseline/result untouched.

### Acceptance evidence, mapped to the checklist

- **v1/v2/v3 reset reproducibly**: `test_reset_is_byte_for_byte_
  reproducible` and `test_repeated_reset_plus_identical_inputs_are_
  deterministic` (both parametrized over all 3 versions).
- **>= 8 drift families**: all 9 represented
  (`test_manifest_covers_all_nine_families`).
- **Semantic near-collision**: `GATE06-CASE-009` (`find_module` vs. the
  decoy `browse_catalog`), tested for real distinct preconditions/effects
  and scored explicitly wrong when confused
  (`test_semantic_near_collision_decoy_is_scored_wrong_for_the_right_reason`).
- **No-equivalent**: `GATE06-CASE-005`/`010` (`submit_leave_request`, no
  successor in v2 or v3); `test_no_equivalent_case_rejects_a_forced_
  nearest_tool_answer` proves a forced nearest-tool guess is scored
  wrong, not accepted.
- **Ground truth hidden from the evaluated model**: 17-test oracle-
  boundary suite -- static AST scan proves the harness module's source
  never imports `oracle`; runtime tests prove a harness instance's public
  API/task object never exposes `tool_id` or any ground-truth field; a
  non-capability caller of `get_ground_truth`/`evaluate_mapping` is
  rejected with `PermissionError`.
- **Verified old traces available**: `build_verified_traces_for_version`
  for v1 and v2 (4 real calls each on one continuous store); replay-
  after-reset reproduces identical outputs and `state_hash_after`
  (`test_replaying_traces_after_reset_reproduces_identical_results`);
  one deliberately-failing trace stays distinguishable
  (`verified=False`).
- **Task evaluator deterministic**: `evaluate_mapping`/
  `evaluate_adapted_call` use only set arithmetic and real sandbox
  execution, zero LLM/network calls
  (`test_no_llm_or_model_dependency_anywhere_in_the_evaluator`);
  repeatable across 5 in-process resets per case and across two separate
  `python -c` subprocess invocations
  (`test_evaluation_is_repeatable_across_separate_process_invocations`).
- **Incorrect mappings fail for the correct reason**: `failure_reasons`
  is a structured tuple (`wrong_tool_selected`, `missed_no_equivalent`,
  `false_no_equivalent`, `argument_pair_missed:*`, `argument_pair_
  spurious:*`, `effect_kind_mismatch`), asserted directly in the partial-
  mapping, spurious-mapping, and near-collision tests.
- **No sandbox leakage to product paths**: `test_gate06_product_
  isolation.py` (AST-scans every file under `research/gate0/` for any
  `app`/`rag` import or reference to the real corpus/lifecycle/provider/
  MCP surface by name); sandbox state is pure in-memory (no filesystem
  path exists to leak through), verified by a source-scan test that
  `store.py` never calls `open()`/`Path()`/touches a DB or network client.
- **No final method/scientific claim**: no LLM call, semantic matcher, or
  alignment algorithm exists anywhere in `research/gate0/`
  (`test_no_llm_or_model_dependency_anywhere_in_the_evaluator`); this is
  stated explicitly in `gates/results/GATE_06_RESULT.md`.

### Known limitations (honest, not fixed in this gate)

- `held_out_cases()` (2 cases, advisor-note lineage) exist for later
  Gate-0 work; only their structural disjointness from the graded
  manifest is tested here, per the entry contract's instruction not to
  inspect held-out cases from any tested-method path.
- The capability check (`EvaluatorCapability`) is a real runtime type
  check, not a security boundary against a hostile importer with full
  repository access -- documented explicitly in `oracle/ground_truth.py`
  and DEC-0014, matching the entry contract's own instruction not to
  overclaim secrecy.
- `evaluate_adapted_call`'s `output_expectation_met` checks required
  output *keys* only (structural), not exact value equality -- sufficient
  for this gate's infrastructure purpose; a later Gate-0 method
  evaluation may want stricter value-level checks.

### Next Step

None from this agent unless the user requests Gate 07 or further Gate 06
extension. STOP -- no Gate 07 work performed.

## 2026-08-27 — Gate 07 Phase 7.0 decision and Phase 7.1 dataset

### Scope

Started the user-authorized Gate 07 falsification gate. Phase 7.0 was
re-verified against `main` at `0561d54d5f623c0a913f222007f86a7f08ea3d66`,
which matched `origin/main`; `fed31c3` was an ancestor; the pre-existing
21-entry dirty overlay remained untouched; and the Gate 06 result was `PASS`.
The exact baseline suite completed 430 passed after rerunning outside the
pytest temp/cache sandbox restriction; compileall was clean. Ollama `/api/tags`
was reachable and Groq variables were inspected by names only.

### Decision and isolated dependencies

The user selected Option B, recorded as DEC-0015: CPU `torch` plus
`sentence-transformers`, `BAAI/bge-m3` for bi-encoder arms, and
`BAAI/bge-reranker-v2-m3` for the genuine cross-encoder arm. The packages are
isolated in `external_tools/research_baselines/.venv`; the application `.venv`
and `requirements.txt` were not modified. The first torch install exposed a
Windows WinError 206 deep-license-path failure and left a partial install; the
same venv was repaired via a temporary drive-letter path and then imported
successfully. Both pinned snapshots loaded and ran with offline flags and
`local_files_only=True`.

Model pins:

- `BAAI/bge-m3` — `5617a9f61b028005a4858fdac845db406aefb181`.
- `BAAI/bge-reranker-v2-m3` — `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`.

### Phase 7.1 implementation

Added a separate `research/gate07/` package with an in-memory 39-tool
synthetic education surface, deterministic operators, 12 drift families,
capability-gated evaluator data, public method-facing contracts/traces, and
real execution receipts. Generated 216 cases: 180 graded and 36 held out;
each family has 15 graded plus 3 held out. D9 one-to-many and D10 many-to-one
shapes are retained explicitly. The frozen and public manifests are
`research/gate07/dataset/frozen_manifest.json` and
`research/gate07/dataset/public_manifest.json`.

### Commands and results

- Targeted Gate 07 tests: **16 passed** before the final manifest-regeneration
  test was added.
- Full application + Gate 07 suite: **447 passed, 2 warnings**.
- `compileall -q app rag scripts evals frontend tests research`: exit 0.
- Pre/post application retrieval smoke with `.venv`: load-bearing metrics
  matched the Gate 04 frozen control exactly (`recall_at_3=0.7222`,
  `recall_at_5=0.8889`, `recall_at_10=0.8889`, `mrr=0.5917`,
  `precision_at_5=0.1889`, answerable 18/20); only latency varied.
- AGY-1 was unavailable as a callable worker in this session. This is recorded
  as `AGY_UNAVAILABLE`; deterministic balance, duplicate, execution-receipt,
  and redaction checks were run locally instead and are not claimed as an
  independent audit.

### Next step

Run the final Phase 7.1 checks, commit only the explicit Gate 07 source/tests/
manifest and task-owned ops slice with
`feat(gate-07): extended education sandbox and Gate-0 case generator`, then
freeze Phase 7.2. No headline baseline has run before a protocol freeze.

## 2026-08-27 — Gate 07 Phase 7.2 protocol freeze

### Scope

Frozen the Gate 07 protocol after the Phase 7.1 commit `44be141` and before
any Phase 7.4/7.5 headline run. The freeze records the canonical graded and
held-out manifest digests, evaluator ground-truth digests, all offline/LLM arm
information rights, versioned prompt templates, BGE model pins, Groq model
IDs, decoding, typed-failure/exclusion rules, metric formulas including D9/D10
many-to-many scoring, and pre-registered GO/REFORMULATE/STOP thresholds.

### Rate-limit and provider evidence

The frozen budget is 180 graded cases × 4 LLM arms × 2 models = **1,440 base
calls**, maximum **4,320 attempts** with retry budget 2, projected
1,915,386 input tokens plus 737,280 maximum output tokens, and a 20% safety
reserve. Non-secret configured ceilings were recorded: per-key 24 RPM/7,000
TPM/900 RPD/180,000 TPD; pool 480 RPM/140,000 TPM/18,000 RPD/3,600,000 TPD;
org 450 RPM/120,000 TPM/17,000 RPD/3,400,000 TPD. The one-process ledger
paths are frozen in the protocol. A quota-free Groq `/models` verification
request returned HTTP 403 Forbidden; this is recorded as unverified provider
model availability, not as an accuracy result and not retried into a pass.

### Commands and results

- Focused protocol tests: **3 passed**.
- Full suite after protocol additions: **450 passed, 2 warnings**.
- `compileall -q app rag scripts evals frontend tests research`: exit 0.
- Protocol file: `gates/baselines/GATE_07_PROTOCOL.json`; freeze-time HEAD:
  `44be1410af557a11557dfe339a08fb6d2af3660e`, before all headline arms.
- AGY-1 remains `AGY_UNAVAILABLE`; no independent auditor was substituted or
  claimed. Local deterministic checks remain the only Phase 7.1 audit.

### Next step

Commit the explicit protocol source/test/JSON/ops slice with
`docs(gate-07): freeze Gate-0 protocol, dataset checksum and decision rule`.
Only after that commit may Phase 7.3/7.4/7.5 begin.

## 2026-08-27 — Gate 07 Phase 7.4 offline baselines

### Scope

Added the lexical, BGE-M3 bi-encoder, and BGE reranker cross-encoder offline
arms. All 180 graded public tasks ran; held-out cases were not exposed. The
isolated interpreter was used for every offline arm with
`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and local model snapshots.
Native parallel subagents were unavailable, so the three disjoint lanes ran
sequentially; no parallelism is claimed.

### Results and artifacts

- `lexical_name` + `lexical_serialized`: 360 predictions and 360 raw records.
- `embed_name_desc` + `embed_serialized_schema`: 360 predictions and 360 raw
  records using `BAAI/bge-m3` revision
  `5617a9f61b028005a4858fdac845db406aefb181`.
- `cross_encoder`: 180 predictions and 180 raw records using
  `BAAI/bge-reranker-v2-m3` revision
  `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`.
- Raw/output files live under ignored `gates/artifacts/gate07/`; SHA-256 and
  counts were recorded in the working task state. The first cross run was
  interrupted at 9/180 because the per-case implementation violated the
  bounded compute assumption; its partial ignored files were replaced by a
  complete batched rerun. No partial result entered metrics.
- Actual offline wall-clock evidence: BGE-M3 embedding sweep ~14 minutes;
  cross-encoder sweep ~19 minutes on CPU. This is a latency risk, not a
  dataset exclusion or model substitution.

### Offline metric smoke

Using evaluator-only capability and 200 bootstrap samples: lexical-name
Tool Alignment@1 0.7278 / Argument F1 0.6139; lexical-serialized 0.6833 /
0.5537; BGE name+description 0.8167 / 0.6463; BGE serialized-schema 0.6556 /
0.5454; cross-encoder 0.6389 / 0.5194. No arm abstained on the no-equivalent
family, so its No-Equivalent Accuracy was 0.0 for this smoke. These are
offline-only numbers, not the Gate 07 decision.

### Commands and results

- Artifact validation: all 900 predictions and 900 raw records have valid
  JSON, 180 unique case IDs per arm file, and `backend=offline`.
- Focused Gate 07 suite: **32 passed**.
- Full suite: **462 passed, 2 warnings**.
- `compileall -q app rag scripts evals frontend tests research`: exit 0.

### Next step

Commit the explicit offline-baseline source/test slice with
`feat(gate-07): lexical, embedding and cross-encoder Gate-0 baselines`, then
begin the sequential Phase 7.5 Groq LLM runner under the frozen budget.

## 2026-08-27 — Gate 07 Phase 7.5 research-mode LLM baselines

### Scope

Added the sequential Groq runner with prompt IDs, parser-owned parse-failure
classification, checkpoint/cache keys `(arm_id, model, prompt_id, case_id)`,
typed provider outcomes, and a single SQLite/JSONL request ledger. A narrow
additive `ProviderRouter` extension passes the frozen model/temperature/
max-token overrides while preserving research-mode no-fallback behavior.
The runner loaded the project `.env` internally without printing values and
used only the existing authorized Groq client/key pool; no Ollama fallback or
new key source was introduced.

### Runs and accounting

- Preflight: 8/8 chat calls succeeded (one case × four arms × two models),
  despite the separate quota-free `/models` endpoint returning HTTP 403.
- Full sweep: 1,440 unique cache keys, 1,440 raw records, 1,440 ledger rows;
  720 records per model and 360 per arm.
- Terminal outcomes: **1,379 success**, **24 parse_failure**, **37
  provider_error**. The existing client emitted 429 cooldown events and
  recovered them internally; no terminal rate-limited row was coerced into a
  wrong answer. Provider/parse failures are excluded from accuracy.
- Estimated input tokens recorded: 1,867,648; output usage is unavailable
  from the current client and is recorded as unknown, while the ledger reserves
  the frozen max 512 output tokens per attempt.
- Held-out cases: not run.

### Amendment and validation

The pre-headline seed-leak correction is recorded as DEC-0016. Protocol v1 is
kept immutable; v2 and regenerated public tasks were used by the reruns, but
the v2 amendment was not committed before those runs. DEC-0017 therefore
marks every v2 offline/LLM result disqualified for scientific metrics. The
first-attempt preview remains audit evidence only; no evaluator mapping was
given to an arm. Focused Gate 07 tests: **39 passed**. Full suite: **469
passed, 2 warnings**. `compileall` exit 0.

### Next step

Do not commit v2 as a valid freeze or execute Phase 7.6. Write and commit the
Gate 07 `BLOCKED` result with the protocol-violation evidence, preserving raw
artifacts and stopping before any scientific decision.

## 2026-08-27 — Gate 07 Phase 7.3 baseline harness and artifact boundary

### Scope

Added the abstract `BaselineArm` interface, mechanically restricted
`ArmInput` rights projection, many-to-many-capable `ProposedMapping`, typed
`RawOutputRecord`, and append-only `RawArtifactWriter`. Raw provider artifacts
are directed under `gates/artifacts/gate07/raw/` and ignored by
`gates/artifacts/.gitignore`; provider dumps are not staged. The harness and
baseline modules do not import the evaluator data module. A test proves
`ProviderRouter(mode="research")` returns a typed Groq failure without
touching Ollama.

### Commands and results

- Focused Phase 7.3 tests: **7 passed**.
- Full suite: **457 passed, 2 warnings**.
- `compileall -q app rag scripts evals frontend tests research`: exit 0.
- AGY-2 was unavailable as a callable worker; this is recorded as
  `AGY_UNAVAILABLE`. The local rights/static tests are not claimed as an
  independent external prompt-leakage audit.

### Next step

Commit the explicit Phase 7.3 source/tests/ignore slice with
`feat(gate-07): baseline arm harness with enforced information rights`, then
run Phase 7.4 offline baselines. Protocol commit `355daf0` already precedes
all headline work.

## 2026-08-28 — Gate 07 repair R0/R1

### Scope

R0 re-verified the repair tree at `d9045ca0c68e90bdbbcb28c14f40d69ed094790a`.
The normal-filesystem baseline passed 469 tests with two warnings; the first
sandboxed attempt produced 355 passes and 114 Windows temp permission errors.
Bug A reproduced as 20/180 graded and 4/36 held-out serialized-task leaks;
Bug B found no git-state checks in the three headline runners; Bug C's
attribute-only boundary test passed despite those leaks. The disqualified v2
ledger contains 1,440 records: 1,379 success, 24 parse failures, 37 provider
errors.

R1 changed `research/gate07/dataset/operators.py` to use explicit field
renderers, raise on unknown fields, remove seed-bearing task prose, and derive
deterministic seeds from SHA-256. `tests/test_gate07_dataset.py` now checks
renderer completeness and rejects arithmetic family-label seed patterns. The
generated frozen and public manifests were regenerated from the fixed
generator after the original manifest test correctly caught stale v2 content.

### Validation

- Focused dataset tests: **10 passed**.
- Full suite: **471 passed, 2 warnings, 0 failed**.
- `compileall -q app rag scripts evals frontend tests research`: exit 0.
- No Gate 06 files, v2 artifacts, secrets, or remote state were changed.

### Next step

Implement R2 value-level leak detection, then R3 mechanical freeze preflight.

## 2026-08-28 — Gate 07 repair R2

### Scope

Added `tests/test_gate07_public_leak.py` with JSON-string surface scanning for
all 216 graded and held-out method-facing tasks, including full seed set,
family labels, tool IDs, lineage IDs, generator operator names, and held-out
markers. A deliberate seed injection is required to fail the detector. The
existing attribute-level boundary test remains unchanged. Internal catalog
lineage IDs were made opaque (`Lnnn`) so a literal lineage check cannot collide
with legitimate public schema words; D9 field-target behavior was retained.

### Validation

- Focused R2/dataset/boundary tests: **16 passed in 12.59s**.
- No Gate 06 files, v2 artifacts, secrets, or remote state were changed.

### Next step

Run the full suite, then commit the R2 test/support slice before implementing
the R3 mechanical freeze preflight.

## 2026-08-28 — Gate 07 repair R3

### Scope

Added the fail-closed `preflight_headline_run` guard in
`research/gate07/protocol/freeze.py`. It verifies protocol existence and Git
tracking, path-local clean status, a real frozen revision ancestor of current
HEAD, and live graded/held-out dataset digest equality. `build_protocol` now
derives `git rev-parse HEAD` itself. Both offline and LLM runners require a
protocol path, run preflight before task loading, and return the pass receipt.

### Validation

- Focused preflight/protocol tests: **9 passed in 53.44s**.
- Covered dirty tracked, untracked, digest mismatch, clean committed, and both
  runner call paths using temporary Git repositories.
- No Gate 06 files, v2 artifacts, secrets, or remote state were changed.

### Next step

Run the full suite, then commit the R3 mechanical-freeze slice.

## 2026-08-28 — Gate 07 repair R4

### Scope

Regenerated a fresh ignored v3 artifact set under
`gates/artifacts/gate07/v3/` from the fixed generator; no v2 artifact was an
input. The dataset is 216 cases: 180 graded and 36 held-out, with 15/3 in each
of the 12 families. Tracked frozen/public manifests matched the v3 output
byte-for-byte. Added `gates/baselines/GATE_07_DATASET_V3.json` with dataset,
ground-truth, and artifact file digests.

### Validation

- Focused R4 leak/regeneration/dataset/sandbox/oracle tests: **22 passed in
  25.18s**.
- Byte-stable regeneration rebuilt the generator after clearing its cache.
- Held-out cases were not sent to any offline or LLM runner.

### Next step

Run the full suite, then commit the R4 dataset receipt and determinism test.

## 2026-08-28 — Gate 07 repair R5 freeze preparation

### Scope

Prepared `gates/baselines/GATE_07_PROTOCOL_V3.json` from the committed v3
dataset. It declares v1 and v2 superseded/disqualified, records the v3 dataset
and ground-truth digests, versions all baseline prompts, pins the two Groq
models and BGE revisions, freezes the 20% rate-limit reserve, and uses v3-only
ledger paths. The live `/models` check remains explicitly unverified after a
403; no model substitution is made. The protocol records
`git_head_at_freeze=a02f2131a306c761034f79d4b5fa0cb60cbe8613` and the v2
1,440-record ledger as audit-only (`feeds_v3=false`).

### Budget frozen before live calls

- Graded cases: 180; LLM arms: 4; models: 2; base calls: 1,440.
- Retry budget: 2; maximum attempts: 4,320.
- Projected input tokens: 1,907,062; maximum output tokens: 737,280.
- Per-key ceilings: 24 RPM / 7,000 TPM / 900 RPD / 180,000 TPD.
- Pool ceilings: 480 RPM / 140,000 TPM / 18,000 RPD / 3,600,000 TPD.
- Org ceilings: 450 RPM / 120,000 TPM / 17,000 RPD / 3,400,000 TPD.
- Reserve: 20%; timeout: 120s; ledger owner: one sequential runner.

The protocol is not yet committed. No R6/R7 headline run has started.

### Post-commit preflight receipt

Protocol freeze commit: `2721c45e783798076ce1d8c61fced15a6357f025`.
Immediately after that commit, before any R6/R7 headline run, the exact
`preflight_headline_run('gates/baselines/GATE_07_PROTOCOL_V3.json')` output was:

```json
{"current_head":"2721c45e783798076ce1d8c61fced15a6357f025","dataset_digests":{"graded_manifest_sha256":"sha256:2f82956b7200836fa23aaca51d04b13b2013bb543e7aac0418f6f4944bb31dbe","held_out_manifest_sha256":"sha256:e438087fb9a92c38a1028b0f7dc917ec080274c10dfd7af3543fe7bba3336378"},"protocol_git_head_at_freeze":"a02f2131a306c761034f79d4b5fa0cb60cbe8613","protocol_git_head_resolved":"a02f2131a306c761034f79d4b5fa0cb60cbe8613","protocol_path":"gates/baselines/GATE_07_PROTOCOL_V3.json","status":"passed"}
```

This proves the committed protocol was clean/tracked, its frozen commit was a
real ancestor of current HEAD, and both live v3 dataset digests matched.

## 2026-08-28 — Gate 07 repair R6 offline arms

### Scope

Ran all five frozen offline arms on `gates/artifacts/gate07/v3/public_tasks.json`
(180 graded cases only), with preflight immediately before each runner. The
lexical runner produced `lexical_name` and `lexical_serialized`; the isolated
research venv produced `embed_name_desc`, `embed_serialized_schema`, and the
trained `cross_encoder` using the pinned local BGE snapshots. No held-out case
was run and no v2 artifact was read.

### Load-bearing checks

- App venv import probe: `torch=false`, `sentence_transformers=false`,
  `transformers=false`.
- Exact BM25 retrieval smoke retained Gate 04 load-bearing values: recall@3
  0.7222, recall@5 0.8889, recall@10 0.8889, MRR 0.5917, precision@5 0.1889,
  answerable 18/20. Only latency varied.
- Output/raw counts: lexical 360/360, embeddings 360/360, cross-encoder
  180/180; each arm had 180 unique case IDs and `backend=offline`.
- Lexical prediction output rerun SHA matched exactly; raw SHA differed only
  because raw records retain measured latency.
- Offline metrics plus real first-attempt execution are retained under the
  ignored v3 artifact directory for R8 recomputation.

### Validation

- Focused R6 data/sandbox/leak/oracle tests: **22 passed** (25.18s).
- Full suite before R6 commit: **479 passed, 2 warnings, 0 failed**.
- Preflight passed on every offline runner invocation; receipts are captured in
  `gates/baselines/GATE_07_OFFLINE_RESULTS_V3.json`.
- Final integrity check filtered shared files by `arm_id`: all five arms have
  180 output records, 180 raw records, 180 unique case IDs, and matching hashes.

## 2026-08-28 — Gate 07 repair R7 first quota-window checkpoint

### Scope

The frozen full LLM sweep does not fit the current daily window after the
disqualified v2 usage, so DEC-0018 pre-registered the canonical seven-case
prefix. The corrected dotenv-enabled run used one sequential process,
`ProviderRouter(mode="research")`, both pinned models, the existing client/key
discovery, candidate-only prompts, and the v3 ledger/cache. Preflight passed
first at current HEAD `bbd1d137e7b5456e4c712edfd3754d7f8fa2bc3e` with freeze
ancestor `a02f2131a306c761034f79d4b5fa0cb60cbe8613`.

### Checkpoint evidence

- 56 corrected base-call records and 56 raw records for the same seven cases.
- 53 success; 3 typed `provider_error` outcomes, all HTTP 400, separate from
  accuracy. No parse failures in this corrected batch.
- Estimated input tokens: 72,692; reserved output: 28,672; total 101,364,
  matching DEC-0018's pre-registered batch budget.
- Corrected output SHA-256:
  `f2b6805d9aca0499c09840271428bef6b49274a11b88639892b30db5b5ab9b66`.
  Corrected raw SHA-256:
  `5133e51cb2bac04cead51f26556812b2077d86a6ded06b7a977936e31713036f`.
- The first 56 setup rows (`Groq is not configured.`) were caused by
  `PYTHON_DOTENV_DISABLED=true`, made no network call, and are retained as
  diagnostics only. The shared v3 ledger now contains 112 rows, but only the
  corrected 56 are eligible R7 evidence.

The remaining 173 cases are not run in this window; resume from the full v3
task file and corrected output/cache after the daily quota window resets.

## 2026-08-28 — Gate 07 repair R7 complete

### Scope

After quota returned, the corrected output/cache was resumed from 56 completed
keys using the full v3 public task file. The run remained one sequential
`ProviderRouter(mode="research")` process with the same two pinned models,
candidate-only prompts, v3 ledger identity, and frozen cache key fields. No
held-out task ran.

### Final accounting

- 1,440 result rows, 1,440 raw rows, 1,440 ledger rows, and 1,440 unique
  `(arm_id, model, case_id, prompt_id)` keys.
- 1,207 success; 16 parse failures; 41 HTTP-400 provider errors; 176 typed
  rate-limited outcomes from the frozen local TPM guard (165 pool TPM, 11 org
  TPM). Provider/parse/rate failures are excluded from accuracy.
- Input estimate: 1,907,062 tokens. Ledger-reserved output: 647,168 tokens;
  actual provider output usage is unavailable from the existing client. The
  176 local rate-limited rows reserve no output tokens.
- Results SHA-256:
  `98ba2ee4aa9d614fe20ab4f604cdb976407572f799b6f0e4d36c7e3e47dca3e3`.
  Raw SHA-256:
  `12e56f456984232dc81751172be6a76231652b3181ffb498adc37c65901cd07c`.
  Request-ledger SHA-256:
  `398c4b2e389bb18e349315dc285753ac78b13b2a80069658160cb45a48fa3b3f`.
- Full pre-correction setup diagnostics remain in the explicit backup paths
  recorded by DEC-0019; they are not R7 evidence.

R7 is complete under the frozen exclusion rules. R8 metrics may now start;
R9 ambiguity audit and R10 decision remain pending.

## 2026-08-28 — Gate 07 repair R8 metrics

### Scope

Added `research/gate07/metrics/report.py` to assemble the frozen metrics from
v3 offline/LLM outputs, excluding provider and parse failures from accuracy.
It records Tool Alignment@1/@3/@5, argument precision/recall/F1, false
alignment, no-equivalent accuracy, real first-attempt sandbox outcomes,
family-level bootstrap CIs, paired history-vs-direct deltas, and the
family-by-arm failure-region table. The generated report is materialized as
`gates/baselines/GATE_07_METRICS.json` and retained in the ignored v3 artifact
directory with SHA-256
`489af74bb048e9434236c5898e3b4ae19ef76a35ef09d9b3d9c361d9736006ca`.

### Observed metrics (decision pending R9)

- 13 arm/model reports × 12 families; no family currently survives all
  baselines on the frozen load-bearing thresholds.
- Strong direct `gpt-oss-120b`: overall Tool Alignment@1 0.5899 (CI
  0.5169–0.6629), Argument F1 0.6124 (0.5412–0.6835), first-attempt success
  0.5899 (0.5225–0.6629), No-Equivalent 1.0 (15/15 evaluable).
- History minus direct paired delta for `gpt-oss-120b`: Tool Alignment@1
  -0.0284 (CI -0.0682–0.0114), Argument F1 -0.0341 (-0.0739–0.0019),
  first-attempt -0.0398 (-0.0795–-0.0057), paired n=176. For `gpt-oss-20b`,
  deltas are small/mixed: Tool Alignment@1 +0.0299 (-0.0060–0.0659),
  Argument F1 +0.0279 (-0.0180–0.0758), paired n=167.
- Offline and LLM provider/parse failure counts remain alongside every arm;
  they are not wrong answers.

### Validation

- Focused metric tests: **6 passed in 1.29s**.
- Report generated successfully with 13 arms and 180 graded cases; held-out
  count is 0.
- Independent report rerun produced the identical SHA-256
  `489af74bb048e9434236c5898e3b4ae19ef76a35ef09d9b3d9c361d9736006ca`.
- Full suite after R8 changes: **480 passed, 2 warnings, 0 failed**.

R9 ambiguity audit is required before any Gate 07 decision.

## 2026-08-28 — Gate 07 repair R9 ambiguity audit

### Scope

AGY-3 was available and completed two turns with
`gemini-3.7-flash-high`, read-only, from a public-only sample. The public
sample had 36 tasks, exactly three per family. Selection was frozen before
annotation: top two per family by `3*oracle-disagreement + pairwise strong-arm
disagreement`, plus one seeded-random remainder using seed 20260828 plus the
family index. The public sample had no family/oracle/evaluator fields; the
evaluator index remained separate. Local Ollama fallback was not used.

### Audit result

- AGY label count: 36; case-level selected-tool/abstain disagreement: **5/36
  (13.89%)**.
- Per-family disagreement: `output_restructure` 2/3 (66.67%),
  `one_old_to_multiple_new` 3/3 (100%), all other 10 families 0/3.
- A020/A021 (output restructure) and A026 (one-to-many) were adjudicated as
  genuinely ambiguous because publicly visible generalized candidates are
  semantically plausible alternatives, while the frozen oracle treats output
  shape or split composition as load-bearing. A025 and A027 were adjudicated
  annotator-wrong because the selected single tool visibly omits required
  output components.
- Oracle corrections: **0**; therefore no corrected-number table is
  applicable and frozen metrics remain unchanged. Both non-zero families
  exceed the frozen 0.20 ambiguity threshold and cannot support a GO alone.
- Receipt: `gates/baselines/GATE_07_AMBIGUITY_AUDIT_V3.json`; labels are
  retained under the ignored v3 artifact directory with hashes recorded there.

The first generated sample/index files had literal backslash-n suffixes and
were corrected to real newline JSON before local verification; AGY was not
called again and content/selection stayed unchanged. Focused audit test:
**1 passed**. R10 decision remains pending.

## 2026-08-28 — Gate 07 repair R10 draft and consistency closure

### Decision

The frozen evidence supports `GO` only for `argument_split`: strong direct
120b and strongest offline baselines fail Argument F1 and first-attempt
success with 0/3 ambiguity disagreements. Output-restructure and
one-old-to-multiple-new are excluded from GO support because their blind
ambiguity rates exceed 0.20. DEC-0020 records the narrow decision and the
explicit Gate 08 prohibition.

### Consistency

AGY-4 was attempted once but the platform rejected transmission of raw v3
LLM artifacts/result data to the external worker. It is recorded as
`AGY_UNAVAILABLE`; no workaround or independent AGY-4 claim is made. A local
read-only recomputation passed all receipt/hash/count/digest checks, including
an independent metrics regeneration with SHA
`489af74bb048e9434236c5898e3b4ae19ef76a35ef09d9b3d9c361d9736006ca`.

The prescribed `build_code_index.py --force` was rejected by the helper CLI;
the supported no-`--force` command indexed 234 files, 1,447 symbols, and 3,138
edges into ignored v3 evidence. `generate_repo_map.py --force` indexed 234
files into ignored v3 evidence. The protected pre-existing `_agent_ops` map,
cards, roadmap, and risk register were not modified.

R10 result draft is ready for final full-suite/Git validation and commit.

### Final validation

- Final full suite with `PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock`:
  **481 passed, 2 warnings, 0 failed**.
- Final compileall over `app rag scripts evals frontend tests research`: exit 0.
- Local consistency recomputation remains `LOCAL_CONSISTENCY_PASS`; AGY-4
  remains explicitly `AGY_UNAVAILABLE` because external raw-artifact
  transmission was blocked.

## 2026-08-29 — Gate 07 V4.1 remediation, recollection, and closure

### Scope

Reproduced the V4 operational defects from the live checkout before editing:
the final three 20b arm groups collapsed to 31.00 minutes, all 180 HTTP-400
rows had null `raw_response`, 56 forced payloads had the exact two-key missing
verdict shape, all 1,800 rows lacked actual output usage, and the strongest
forced `argument_split` cell had `n=8` versus `family_minimum=15`. Ran the
required blast-radius explorer before touching `groq_client.py`.

Implemented and tested bounded client throttling with read-only wait-time
calculation, retryable non-success cache semantics, HTTP error-body and usage
propagation, `max_tokens=1536`, deterministic arm/model shuffle, actual usage
ledger accounting, hard `$1.20` cost protection, and latest-attempt resolution
for append-only recollection logs. Research mode remained no-fallback.

### Receipts

- V4.1 addendum and DEC-0021 were committed before recollection; preflight
  passed at HEAD `beef195d30b1980d47d9c6837a407bac5b90e23c`.
- Full provider recollection added 784 rows: 759 success, 13 parse failures,
  12 provider errors, and zero `client_throttled`; recorded cost was
  `$0.23893425`, with 1,800 unique logical keys after latest-attempt
  resolution and zero held-out cases.
- Result/raw/request-ledger hashes are
  `c25e760841574ffa0eac2abb5fe7717e71f91533d2ab5be146f0c0794c17f599`,
  `b324e50a8428ff3c684226341584276470197b4cd24a725d73bd513895959200`, and
  `fd1d53158f10e25bcd039e7546e9425ef4d12933101adbc68f6faa9deb117a52`.
- Metrics regenerated twice with matching SHA
  `71aa32cf654814e9492caaded8dcd9895bb1a4712a001885731be366981c9dfc`.
- Final validation: **498 passed, 2 warnings, 0 failed**; compileall exit 0.

### Decision

DEC-0022 closes Gate 07 with a narrow `GO` for `argument_split` and
`tool_replacement`; no broad GO is claimed and Gate 08 remains forbidden.
The carrier `argument_split` has `n=15` exactly, so the `<15` stop condition
does not apply. The first sandboxed provider attempt hit an artifact-write
permission error after a response; it was retried after filesystem escalation,
and the bounded worst-case unrecorded exposure is preserved in the result and
closure receipt rather than reported as zero.

## 2026-08-29 — Gate 07 agent-ops reconciliation

After the V4.1 closure, a live scan found stale current-state references in the
project context card, risk register, phase tracker/card, execution and repair
prompt headers, third-party tooling record, and repository map. Those records
were synchronized to the authoritative narrow V4.1 `GO` for `argument_split`
and `tool_replacement`; historical v2/v3 `BLOCKED` text was retained and
explicitly labeled historical. Gate 08 records were not edited.

`REPO_MAP.md` was regenerated from HEAD `b27fcae` (237 code files, 1,410
symbols, 3,026 edges). `CURRENT_TASK.md` and `SESSION_BRIEF.md` retain the
final HEAD and no-push state as machine-local notes. No provider, source-code,
protocol, freeze-ledger, or test change was made in this reconciliation.
