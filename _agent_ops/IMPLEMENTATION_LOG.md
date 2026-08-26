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
