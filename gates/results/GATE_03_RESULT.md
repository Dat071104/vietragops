# Gate 03 Result

Status: WAITING_FOR_USER_SECRET

## Commit / tree state

- Gate 02 result commit `f986976` was reachable before any Gate 03 edit.
  The only commit after it was `d05be38`, verified with `git show --stat`
  to be docs/ops-only (18 new files under `_agent_ops/`, `AGENTS.md`; no
  source/test/data path touched).
- The pre-existing dirty overlay (`AGENTS.md` modified, `rag/generation/
  groq_client.py` modified, five `skills/*/scripts/*.py` deleted, the
  untracked `_agent_ops/` bootstrap layer and `tests/test_groq_rotation.py`)
  remained present, untouched, and unstaged throughout. No reset, restore,
  clean, stash, `git add .`, amend, or rebase was used. No push was
  performed. The Git index was empty before every Gate 03 edit and after
  every commit.
- Six Gate 03 commits were made on top, in order: `74e5113`, `22d99bc`,
  `e6f52cb`, `6e2bb8a`, `db68ed6`, `d2bd02b` (see Files changed below).
  This result/state pair is committed separately as
  `docs(gate-03): record web import result`.
- `external_tools/firecrawl` was independently re-verified clean at pinned
  revision `d26ad4bbf2fe1d0be3b8bb4a94bfe8baa2c15e72` (matching
  `_agent_ops/THIRD_PARTY_TOOLING.md`) and was not modified, imported, or
  started (`docker compose`/`up` was never invoked).
- `.gitignore` covers `.env.firecrawl.local` by the existing filename
  pattern `.env.*` (confirmed with `git check-ignore -v`, file not opened).
- `VietRagOps/.env.firecrawl.local` already existed before this session
  (not created here). Per the secret stop rule this file was never opened,
  read, edited, or content-confirmed. **No user message in this session
  said "FIRECRAWL_API_KEY đã được điền local".** Phase 3.5 (the
  authenticated live proof) was therefore not started; no Firecrawl network
  call was ever made with a real key, and no key value was read, echoed,
  logged, or committed.

## Phases completed

- Phase 3.0 — re-ran pre-edit compile and the focused lifecycle baseline
  (`98 passed`) with the project venv; confirmed the `.gitignore` filename
  coverage; confirmed the local secret handoff file's existence without
  opening it; designed the non-secret `FIRECRAWL_*` config surface
  (default-deny allowlist). No authenticated Firecrawl call was made.
- Phase 3.1 — added `rag/ingestion/firecrawl.py`: a narrow httpx-based
  Firecrawl v2 adapter (`search_preview`, `scrape_markdown` only; no
  map/crawl/actions/custom headers/cookies/proxy/OCR/cloud-parser
  surface), typed outcome classification, bounded retries (max 2, only on
  408/429/500/502/503/504, respecting `Retry-After` including the
  HTTP-date form), a streaming byte-budget cap enforced before appending
  each chunk, and a wall-clock stream deadline independent of per-chunk
  I/O timeouts. The API key is read from the environment at call time
  only and never appears in a repr or exception message.
- Phase 3.2 — added `rag/lifecycle/web_safety.py`: HTTPS-only URL syntax
  validation (rejects non-https schemes, userinfo, fragments, non-default
  ports, percent-encoded host ambiguity), a blocked-hostname list
  (localhost/`*.localhost`/metadata hostnames), request-time DNS
  resolution that rejects any resolved address that is private, loopback,
  link-local, multicast, reserved, or unspecified (IPv4 and IPv6), and a
  server-owned domain allow/deny policy that defaults to deny-all with
  the denylist always winning. Added matching non-secret `FIRECRAWL_*`
  settings to `app/core/config.py`.
- Phase 3.3 — added `rag/lifecycle/web_pipeline.py` (candidate build
  reusing the existing Markdown loader/section builder/chunker, producing
  an extraction record in the *same* schema `rag/lifecycle/pipeline.py`
  uses so the existing `LifecycleService.review/publish/rollback`
  integrity checks accept it unchanged) and `rag/lifecycle/web_import.py`
  (`WebImportService`: runs every URL through `web_safety` before any
  adapter call; document identity is `web-{sha256(canonical_url)[:24]}`,
  never the title; idempotent on unchanged content checksum). Extended
  the SQLite registry with `web_provenance` and `acquisition_attempts`
  tables. Added `scripts/web_import.py`, a local-only CLI
  (`search`/`import`/`recrawl`) because the application has no admin
  authorization to gate a public FastAPI route.
- Phase 3.4 — added `rag/lifecycle/web_diff.py`: a deterministic (no LLM)
  changed-section summary computed by re-running the existing section
  builder over the prior and new `canonical.md` and comparing sections by
  heading path and content hash. Wired into `WebImportService.import_url`
  so a content-changed recrawl creates a new, still-candidate version
  linked via `prior_version_id`/`diff_path` in `web_provenance`, without
  touching the existing `versions.supersedes`/`superseded_by` columns
  (reserved for publish-time semantics).
- Two read-only audits (Explore agent, substituting for Antigravity,
  which is not an available agent type on this platform — recorded once
  as `AGY_UNAVAILABLE`, per the team-mode fallback rule):
  - After Phase 3.2: found the safety module was not yet wired into any
    call path (expected — the wiring is Phase 3.3's job, and is proven by
    `test_disallowed_domain_never_reaches_adapter`/
    `test_private_ip_target_never_reaches_adapter`), a DNS-rebinding/TOCTOU
    limitation inherent to using a third-party hosted scraper (documented
    below, not fixable in this codebase), and three adapter hardening
    gaps (HTTP-date `Retry-After` not parsed, no stream-wide deadline, byte
    cap checked after append) — all three fixed in `e6f52cb` with new
    regression tests.
  - Before this result: found two real recrawl-diff bugs (duplicate
    heading paths silently overwriting each other's hash; a missing prior
    canonical file producing a misleading "everything added" diff instead
    of the documented no-diff behavior) — both fixed in `d2bd02b` with new
    regression tests. No mutation of a prior version's directory was found.
  Every audit finding was independently re-verified by reading the actual
  diff before committing a fix; the audit's own conclusion was never used
  as the sole evidence.
- Phase 3.5 (authenticated live proof) — **not started.** No user
  confirmation of the local key was given in this session. Per the
  secret stop rule, this result is written as `WAITING_FOR_USER_SECRET`
  instead of proceeding.
- Full offline regression (no Firecrawl call involved) was still run and
  is reported below, since it is unrelated to the secret gate.

## Files changed

- `74e5113 feat(gate-03): add bounded firecrawl adapter`
  - `rag/ingestion/firecrawl.py`
  - `tests/test_firecrawl_adapter.py`
- `22d99bc feat(gate-03): enforce bounded web import safety`
  - `rag/lifecycle/web_safety.py`
  - `tests/test_web_safety.py`
  - `app/core/config.py` (FIRECRAWL_* non-secret settings)
  - `tests/test_firecrawl_adapter.py` (map/crawl-surface-absence assertion)
- `e6f52cb fix(gate-03): harden firecrawl adapter after safety audit`
  - `rag/ingestion/firecrawl.py`
  - `tests/test_firecrawl_adapter.py`
- `6e2bb8a feat(gate-03): import firecrawl pages as candidates`
  - `rag/lifecycle/web_pipeline.py`
  - `rag/lifecycle/web_import.py`
  - `rag/lifecycle/registry.py` (web_provenance, acquisition_attempts)
  - `scripts/web_import.py`
  - `tests/test_web_import.py`
  - `app/core/config.py` (`get_web_import_service`)
- `db68ed6 feat(gate-03): track recrawl candidate diffs`
  - `rag/lifecycle/web_diff.py`
  - `rag/lifecycle/web_import.py`
  - `rag/lifecycle/registry.py` (`diff_path` column + migration)
  - `tests/test_web_recrawl_diff.py`
- `d2bd02b fix(gate-03): correct recrawl diff on repeated headings and stale paths`
  - `rag/lifecycle/web_diff.py`
  - `rag/lifecycle/web_import.py`
  - `tests/test_web_recrawl_diff.py`
- This result/state commit
  - `PROJECT_STATE.md`
  - `gates/results/GATE_03_RESULT.md`
  - `gates/baselines/GATE_03_RETRIEVAL_SMOKE.json`
- Not changed by Gate 03: `external_tools/firecrawl` (still clean, still
  pinned, never started); `external_tools/markitdown`; the existing
  37-document corpus, `data/processed/processed_docs.jsonl`,
  `data/manifests/documents_manifest.csv`, `data/chunks/*`; any other
  application route; Docker/compose files; `requirements.txt` (no new
  dependency — httpx was already pinned); `.env`, `.env.example`, or
  `.env.firecrawl.local`; the pre-existing dirty overlay.

## Commands/tests executed

All commands used `.venv/Scripts/python.exe` with
`PYTHON_DOTENV_DISABLED=true` and `LLM_PROVIDER=mock`. No `.env` or
credential handoff file was read.

- Pre-edit compile (`compileall -q app rag scripts evals frontend tests`)
  — passed, before any Gate 03 edit.
- Pre-edit focused lifecycle baseline (9 focused files, workspace
  basetemp) — `98 passed`.
- Compile + focused tests after each phase — passed every time; full
  `pytest -q` (workspace basetemp) grew monotonically with each phase's
  new tests only: `211 -> 214 -> 228 -> 234 -> 236 passed, 0 failed`.
- Final full regression, run after Phase 3.4 with no Firecrawl call
  involved:
  - `compileall -q app rag scripts evals frontend tests` — passed, no
    output.
  - `pytest -q` (workspace basetemp, `-p no:cacheprovider`) — **236
    passed, 0 failed** (157 pre-Gate-03 + 79 new: 17 adapter, 40 safety,
    14 import, 8 recrawl/diff).
  - `scripts/validate_chunks.py --chunks-dir data/chunks` — passed;
    1036/695/572 rows, abnormal 0 for each — identical to Gate 00-02.
  - `scripts/validate_processed_docs.py data/processed/processed_docs.jsonl`
    — passed; 37/37, success rate 1.000 — identical to Gate 00-02.
  - `scripts/verify_manifest.py data/manifests/documents_manifest.csv` —
    passed; 37 rows, 0 duplicate checksum groups — identical to Gate 00-02.
  - `python -m evals.experiments.run_retrieval_eval --chunks
    data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl
    --retriever bm25 --top_k 5 --output
    gates/baselines/GATE_03_RETRIEVAL_SMOKE.json` — passed; 695 chunks, 20
    queries, recall@5 `0.8889`, MRR `0.5917`, precision@5 `0.1889`,
    recall@3 `0.7222`, recall@10 `0.8889`, answerable `18` — bit-for-bit
    identical to `gates/baselines/GATE_02_RETRIEVAL_SMOKE.json`, proving
    the live corpus and retrieval behavior are unchanged by Gate 03.
- No authenticated Firecrawl request was made at any point (`FIRECRAWL_API_KEY`
  was never read for a live call); all 79 new tests mock the httpx
  transport with a placeholder key string (`"test-key-not-real"`).

## Acceptance checklist

- [x] Secret handoff policy followed — `.env.firecrawl.local` never
      opened/edited/content-confirmed; only its filename-based
      `.gitignore` coverage was checked.
- [ ] Search/scrape work after user secret confirmation — **not reached**;
      no user confirmation was given in this session, so no authenticated
      call was attempted (correct behavior per the stop rule, not a defect).
- [x] Private-network targets blocked — `rag/lifecycle/web_safety.py`
      (localhost/`*.localhost`/metadata hostnames, request-time DNS
      rejection of private/loopback/link-local/multicast/reserved/
      unspecified IPv4+IPv6) with 14 dedicated tests in
      `tests/test_web_safety.py`, plus two end-to-end tests in
      `tests/test_web_import.py` proving a blocked target never reaches
      the adapter transport at all.
- [x] Crawl/page/byte/depth/time/retry budget enforced — the adapter has
      no map/crawl/actions method (asserted by
      `test_adapter_exposes_no_map_or_crawl_or_action_surface`); every
      import is exactly one page, depth 0; byte cap enforced during
      streaming (pre-append check); wall-clock stream deadline; retries
      bounded to 2, only on 408/429/500/502/503/504, respecting
      `Retry-After` (delta-seconds and HTTP-date).
- [x] Imported page becomes a candidate, not a live source — every new
      web version starts `review_status="candidate"`;
      `test_allowed_url_becomes_candidate_without_touching_live_corpus`
      and `test_recrawl_never_changes_an_already_published_version` prove
      the live manifest/chunks bytes are byte-identical before and after
      an import/recrawl; the read-only audit before this result
      independently confirmed no code path outside
      `rag/lifecycle/service.py` touches `manifest_path`/`chunks_path`/
      `apply_live_state`.
- [x] Provenance retained — canonical URL, retrieval timestamp (UTC),
      Firecrawl action id, HTTP status/status class, credits used,
      content checksum, domain, adapter/parser policy version, and
      prior-version link are all persisted in the new `web_provenance`
      SQLite table (`test_provenance_records_checksum_timestamp_and_action_id`).
- [x] Recrawl creates a new version/diff — unchanged content is
      idempotent (`test_unchanged_recrawl_is_idempotent_no_change_event`);
      changed content creates a new version linked via `prior_version_id`
      with a deterministic `diff.json`
      (`test_changed_recrawl_creates_new_version_with_prior_link_and_diff`),
      correctly handling repeated heading paths and a missing prior file
      (`test_diff_detects_change_in_earlier_of_two_identically_titled_sections`,
      `test_missing_prior_canonical_file_skips_diff_instead_of_reporting_everything_added`).
- [x] 429/error handling tested — distinct typed outcomes for
      unauthorized/credit_exhausted/rate_limited/timeout/upstream_error/
      invalid_response/blocked_target, each with its own test in
      `tests/test_firecrawl_adapter.py` and cross-checked end-to-end in
      `tests/test_web_import.py::test_rate_limited_and_credit_exhausted_are_recorded_distinctly`.
- [x] `gates/results/GATE_03_RESULT.md` written using the required format.

## Evidence artifacts

- `gates/baselines/GATE_03_RETRIEVAL_SMOKE.json` — current offline BM25
  smoke; bit-for-bit identical metrics to Gate 02.
- 79 new automated tests across 4 files: `tests/test_firecrawl_adapter.py`
  (17), `tests/test_web_safety.py` (40), `tests/test_web_import.py` (14),
  `tests/test_web_recrawl_diff.py` (8).
- Six source commits (`74e5113`, `22d99bc`, `e6f52cb`, `6e2bb8a`,
  `db68ed6`, `d2bd02b`), each preceded by a passing focused test run,
  a full compile, and `git diff --cached --check`.
- Existing corpus/processed/manifest/chunk hashes independently compared
  to Gate 00-02 and match exactly.

## Known issues

- **Phase 3.5 (authenticated live proof) is blocked on the user.** No
  message in this session confirmed the local key is filled in. Resume
  is only valid in a session where the user explicitly states
  "FIRECRAWL_API_KEY đã được điền local" and confirms they will not send
  the value; this result must not be reinterpreted as permission to make
  that call later without that confirmation.
- **DNS-rebinding / TOCTOU across the Firecrawl boundary.** This app
  resolves and rejects private targets before ever calling Firecrawl, but
  Firecrawl's own hosted infrastructure re-resolves the URL independently
  when it performs the actual fetch. An attacker controlling authoritative
  DNS with a very short TTL could in principle return a public address for
  our pre-check and a private/metadata address moments later for
  Firecrawl's fetch. This is a SaaS-boundary limitation this codebase
  cannot close unilaterally (it would require IP-pinning cooperation from
  Firecrawl itself); it is not fixed and is recorded here as a residual
  risk, not a defect in the code that was written.
- The adapter's response-schema parsing (`_parse_search_descriptors`,
  `_parse_scrape_body`) is based on the documented Firecrawl v2 API shape
  and has only been exercised against hand-authored mock responses; it
  has never been verified against a real Firecrawl response, because no
  authenticated call has been made. A schema mismatch would currently
  surface as a safe `invalid_response` outcome, not a crash, but the exact
  shape is unconfirmed until Phase 3.5.
- Candidate directories are not currently pruned/garbage-collected; a
  recrawl diff explicitly detects and reports (rather than silently
  masking) a missing prior canonical file, but nothing in this Gate adds
  retention/cleanup policy for old candidate artifacts.
- The existing single-writer assumption for `LifecycleRegistry` (recorded
  in Gate 01/02) is unchanged; `WebImportService` opens its own
  `LifecycleRegistry` instance against the same SQLite file path as
  `get_lifecycle_service()`, which is safe under SQLite's own connection
  handling but still assumes one operator at a time, consistent with
  every other Gate so far.
- No FastAPI route was added for web import (by design — the app has no
  admin authorization to gate a public endpoint); `scripts/web_import.py`
  is a local-only CLI. If a future gate adds real admin authorization,
  wiring an HTTP route on top of the existing `WebImportService` would be
  additive, not a rewrite.

## Next allowed Gate

None yet. Resume Phase 3.5 of Gate 03 only in a new session where the
user has explicitly confirmed, in that session, that the local
`.env.firecrawl.local` key is filled in and that they will not send its
value. Gate 04 must not begin before Gate 03 reaches a final PASS.

## STOP

No next-Gate work performed. No authenticated Firecrawl call was made.
