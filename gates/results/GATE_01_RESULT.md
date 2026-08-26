# Gate 01 Result

Status: PASS

Commit / tree state:

- Prerequisite verified before any edit: `gates/results/GATE_00_RESULT.md` is
  `PASS`. Pre-edit HEAD `b52f2b9` matched the recorded final Gate 00 commit.
  The dirty overlay was re-derived independently (`git status --porcelain`,
  `git rev-list --left-right --count HEAD...@{upstream}`, and a fresh SHA-256
  of `rag/generation/groq_client.py`) and matched
  `gates/baselines/GATE_00_BASELINE.json` exactly: 6 tracked
  modified/deleted paths, 38 nonignored untracked files (once the
  `_agent_ops/archive/` and `_agent_ops/tools/` directory lines are expanded
  to their file contents), and `groq_client.py`'s worktree SHA-256
  (`b48cf46c4381176b154ea99ee2157315934edb7b340bbc4a86791cc59e99f68f`) unchanged.
- Four Gate-01 commits were made on top, in order:
  `f359751`, `0a1d352`, `b4149d1`, `9a02ac1` (see Files changed below). This
  result/state pair is committed separately as
  `docs(gate-01): record document lifecycle result`.
- The same pre-existing dirty overlay (`rag/generation/groq_client.py`
  modified; 5 `skills/*/scripts/*.py` deleted; the untracked `_agent_ops/`
  bootstrap layer and `tests/test_groq_rotation.py`) remains present,
  untouched, and unstaged throughout. No reset/restore/clean/stash/`git add .`
  was used. No push was performed.

Phases completed:

- Phase 1.0: verified the Gate 00 handoff (above); discovered the project's
  own `.venv\Scripts\python.exe` has pytest 9.0.3/fastapi/httpx installed
  (Gate 00 had used `C:\Python314\python.exe`, which lacks pytest, and
  recorded a false "pytest unavailable" blocker) and used it for every
  command in this Gate; ran the pre-edit baseline (`59 passed, 0 failed`);
  recorded the lifecycle design decision (storage owner, registry format,
  candidate/live boundary, review transitions, publish atomicity, rollback,
  cache refresh) in `_agent_ops/CURRENT_TASK.md`.
- Phase 1.1: secure intake -- basename/extension normalization and traversal
  rejection, extension+MIME allowlist, bounded streaming size enforcement,
  SHA-256 checksum, deterministic magic-byte/UTF-8 format check.
- Phase 1.2: durable local source/document/version registry on SQLite
  (stdlib `sqlite3`), with a `(document_id, checksum)` unique constraint for
  deterministic duplicate rejection, an append-only `events` audit log, and
  restart-survival proven by reopening a fresh `LifecycleRegistry` against the
  same DB file.
- Phase 1.3: candidate-only processing -- reuses the existing
  `rag/loaders/*` + `rag/preprocessing/section_detector.py` +
  `rag/chunking/section_chunker.py` pipeline (the same one
  `scripts/run_phase2_processing.py`/`scripts/chunk_documents.py` already
  use); writes only under a per-version candidate directory, never under the
  live chunks/manifest path; a parser exception or empty-section result is
  recorded as `parse_status="failed"` rather than raised, so a bad candidate
  can never corrupt the original or crash intake.
- Phase 1.4: review/atomic publish/retire/rollback -- `rag/lifecycle/publish.py`
  rebuilds the live manifest CSV and chunks JSONL in memory and replaces each
  with `os.replace` (atomic on NTFS/POSIX); `rag/lifecycle/service.py` enforces
  the state machine (`candidate -> reviewed -> published -> superseded/retired`,
  with `candidate -> reviewed -> published` again on rollback) and calls
  `app/core/config.refresh_live_caches()` (clears `get_store`,
  `get_context_builder`, and both answer-generator `lru_cache`s) after every
  live-state change. Rollback republishes a prior version's already-stored
  candidate chunks and never re-parses or touches the immutable original
  (proven with a test that monkeypatches `process_candidate` to raise if
  called during rollback).

Files changed:

- `f359751` — `rag/lifecycle/__init__.py`, `errors.py`, `naming.py`,
  `intake.py`; `tests/test_lifecycle_intake.py`.
- `0a1d352` — `rag/lifecycle/registry.py`; `tests/test_lifecycle_registry.py`.
- `b4149d1` — `rag/lifecycle/storage.py`, `pipeline.py`;
  `tests/test_lifecycle_pipeline.py`, `test_lifecycle_candidate_isolation.py`.
- `9a02ac1` — `rag/lifecycle/publish.py`, `service.py`; `rag/lifecycle/registry.py`
  (extended: `get_document` source join, `record_note`, optional
  `create_version(version_id=...)`); `rag/lifecycle/intake.py` (extended:
  `IntakeReceiver.raw_filename`/`.content_type`); `app/core/config.py`
  (env-overridable `chunks_path`/`manifest_path`, `lifecycle_root`,
  `lifecycle_max_upload_bytes`, `refresh_live_caches()`, `get_lifecycle_service()`);
  `app/schemas/document.py` (new intake/version/rollback response models);
  `app/api/routes_documents.py` (governed `/documents/upload`; new
  `GET /documents/{doc_id}/versions`, `POST /documents/versions/{id}/review`,
  `.../publish`, `.../retire`, `POST /documents/{doc_id}/rollback`);
  `.gitignore` (`data/lifecycle/` runtime state); `tests/test_lifecycle_registry.py`
  (extended), `test_lifecycle_publish_apply.py`, `test_lifecycle_service.py`,
  `test_api_documents_lifecycle.py` (new).
- This result commit — `gates/results/GATE_01_RESULT.md`, `PROJECT_STATE.md`,
  `gates/baselines/GATE_01_RETRIEVAL_SMOKE.json`.
- Not changed by Gate 01: the existing 37-document
  `data/manifests/documents_manifest.csv` / `data/chunks/chunks_500.jsonl`
  corpus, `data/processed/processed_docs.jsonl`, `data/raw/*`, any other
  application route, Docker/compose files, dependency manifests, or the
  pre-existing dirty overlay.
- `_agent_ops/CURRENT_TASK.md`, `SESSION_BRIEF.md`, `IMPLEMENTATION_LOG.md`
  were updated but intentionally not staged (`CURRENT_TASK.md`/`SESSION_BRIEF.md`
  are gitignored machine-local notes; `IMPLEMENTATION_LOG.md` is part of the
  pre-existing untracked overlay Gate 00 also left unstaged, and this Gate
  preserves that same boundary rather than changing the overlay's identity).

Commands/tests executed (all with `.venv/Scripts/python.exe`):

- `python -m compileall -q app rag scripts evals frontend tests` — PASS, run
  after every phase.
- `python -m pytest -q` — pre-edit baseline: `59 passed`. Final, after all
  four phases: **`134 passed, 0 failed`** (59 pre-existing + 75 new lifecycle
  tests: 32 intake, 12 registry, 6 pipeline, 1 candidate-isolation, 4
  publish-apply, 16 service, 4 full-HTTP-lifecycle integration). Re-run once
  more immediately before this result was written, with identical outcome.
- `python scripts/validate_chunks.py --chunks-dir data/chunks` — PASS;
  1036/695/572 rows, `abnormal=0` for all three, identical to Gate 00.
- `python scripts/validate_processed_docs.py data/processed/processed_docs.jsonl`
  — PASS; 37/37, 100% success, identical to Gate 00.
- `python scripts/verify_manifest.py data/manifests/documents_manifest.csv` —
  PASS; 37 rows, 0 duplicate checksum groups, identical to Gate 00.
- `python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl
  --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5 --output
  gates/baselines/GATE_01_RETRIEVAL_SMOKE.json` — PASS; 695 chunks, 20 queries,
  recall@5 `0.8889`, MRR `0.5917` — bit-for-bit identical metrics to
  `gates/baselines/GATE_00_RETRIEVAL_SMOKE.json`, proving the live corpus and
  retrieval behavior were not altered by this Gate.
- `git status --short -- data/` — clean before and after every test run; all
  lifecycle integration tests operate on a `tmp_path`-isolated manifest/chunks
  registry via `VIETRAGOPS_CHUNKS_PATH`/`VIETRAGOPS_MANIFEST_PATH`/
  `VIETRAGOPS_LIFECYCLE_ROOT` env overrides, never the committed corpus.
- `git diff --cached --check` — clean before every commit.
- Docker compose config-only validation was NOT re-run this Gate (no Docker
  or dependency-manifest change was made; Gate 00's result already covers it
  and nothing here invalidates that check).

Acceptance checklist:

- [x] Unsafe filename/path rejected — `tests/test_lifecycle_intake.py`
      (traversal, separators, empty, reserved Windows device names, malformed
      extension) and `tests/test_api_documents_lifecycle.py::test_upload_rejects_path_traversal_filename`.
- [x] Unsupported/oversized file rejected — `test_lifecycle_intake.py`
      (MIME allowlist, magic-byte/UTF-8 format check, bounded streaming size)
      and `test_api_documents_lifecycle.py::test_upload_rejects_oversized_file`.
- [x] Duplicate ingestion is deterministic — `test_lifecycle_registry.py`
      (unique `(document_id, checksum)` constraint), `test_lifecycle_service.py`
      (`test_reuploading_identical_content_is_idempotent`,
      `test_reuploading_different_content_same_filename_creates_new_version`),
      and the HTTP-level duplicate check inside
      `test_full_lifecycle_publish_retire_rollback_via_http`.
- [x] Source/version metadata durable locally — `test_lifecycle_registry.py::test_registry_survives_reopen_against_same_db_path`
      and the provenance-retention/unknown-fields tests in the same file.
- [x] Candidate source cannot affect live RAG —
      `tests/test_lifecycle_candidate_isolation.py` (queries the real
      `app.core.config.get_store()` against the real committed corpus) and
      step 4 of `test_full_lifecycle_publish_retire_rollback_via_http`
      (candidate absent from `/retrieve` and the live manifest before review/publish).
- [x] Publish atomically changes live version — `rag/lifecycle/publish.py`
      (`os.replace`-based swap of both the manifest and the chunks file),
      `test_lifecycle_publish_apply.py`, `test_lifecycle_service.py::test_publish_switches_live_manifest_and_chunks_and_refreshes_cache`
      and `test_publishing_a_new_version_supersedes_the_previous_live_version`.
- [x] Retire/rollback verified — `test_lifecycle_service.py::test_retire_removes_from_live_but_keeps_provenance`,
      `test_rollback_restores_prior_version_without_reparsing` (proves no
      re-parse via a monkeypatch that raises if the parser is called),
      `test_rollback_rejects_mismatched_document`,
      `test_rollback_to_currently_live_version_is_idempotent_noop`; end-to-end
      through the HTTP API in `test_full_lifecycle_publish_retire_rollback_via_http`.
- [x] RAG regression tests pass — full `pytest -q`: 134/134 (0 failed); offline
      BM25 smoke metrics identical to the Gate 00 baseline; `validate_chunks`,
      `validate_processed_docs`, `verify_manifest` all identical to Gate 00.
- [x] `gates/results/GATE_01_RESULT.md` written using the required format.

Evidence artifacts:

- `gates/baselines/GATE_01_RETRIEVAL_SMOKE.json` — offline BM25 regression
  smoke, metrics identical to `gates/baselines/GATE_00_RETRIEVAL_SMOKE.json`.
- 75 new automated tests across 7 files under `tests/test_lifecycle_*.py` and
  `tests/test_api_documents_lifecycle.py`; full list and command in
  `_agent_ops/IMPLEMENTATION_LOG.md`.
- Four source commits (`f359751`, `0a1d352`, `b4149d1`, `9a02ac1`), each
  preceded by a passing focused test run and `git diff --cached --check`.

Known issues:

- Gate 00's "pytest unavailable" was caused by running with
  `C:\Python314\python.exe`; the project's own `.venv\Scripts\python.exe` has
  pytest 9.0.3 and works. This is recorded as an operating fact, not a
  retroactive edit to the Gate 00 result.
- The pre-existing 37-document corpus is not tracked by the new registry
  (deliberate Phase 1.0 decision: migrating it was judged to be exactly the
  kind of restructure-for-appearance this Gate prohibits, and Gate 00 already
  found no coupling that requires it). Those documents have no version
  history, review status, or rollback path yet.
- `LifecycleService.publish`/`retire`/`rollback` rebuild the full live
  manifest/chunks file per call and assume a single writer; there is no
  cross-process lock. Acceptable for this Gate's single-operator scope.
- The `/documents/upload` route applies one `source_url`/`publisher`/`domain`/
  `authority_level` to every file in a batch call; a caller wanting different
  provenance per file must call the endpoint once per file.
- Docker/compose behavior was not re-validated this Gate (nothing here
  changes it); Gate 00's config-only validation still stands.

Next allowed Gate:

Gate 02, only in a new explicit session after independently re-verifying this
Gate 01 PASS result and matching baseline/HEAD identity.

STOP:

No next-Gate work performed.
