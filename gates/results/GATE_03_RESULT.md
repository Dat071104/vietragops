# Gate 03 Result

Status: PASS

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
  performed during the work itself. The Git index was empty before every
  Gate 03 edit and after every commit.
- Ten Gate 03 commits were made on top, in order: `74e5113`, `22d99bc`,
  `e6f52cb`, `6e2bb8a`, `db68ed6`, `d2bd02b`, `b178c4b`, `7a1d042`,
  `2e0781e`, and this final result/state commit (see Files changed below).
- An intermediate result was committed as `b178c4b` with
  `Status: WAITING_FOR_USER_SECRET` because no user message in that part
  of the session had confirmed the local key was filled in. Later in the
  same session the user explicitly stated: "Tôi xác nhận
  .env.firecrawl.local đã có key hợp lệ local; không gửi giá trị." and
  separately configured a non-secret domain allowlist entry themselves
  (`FIRECRAWL_ALLOWED_DOMAINS=undergrad.tdtu.edu.vn`, appended to `.env`
  by this agent at the user's explicit instruction, without reading any
  other line of that file). Phase 3.5 then proceeded and this result
  supersedes the intermediate one.
- `external_tools/firecrawl` was independently re-verified clean at
  pinned revision `d26ad4bbf2fe1d0be3b8bb4a94bfe8baa2c15e72` (matching
  `_agent_ops/THIRD_PARTY_TOOLING.md`) and was not modified, imported, or
  started (`docker compose`/`up` was never invoked; the hosted API was
  used, not self-hosting).
- `.gitignore` covers `.env.firecrawl.local` and `.env` by the existing
  filename patterns `.env`/`.env.*` (confirmed with `git check-ignore
  -v`). Neither file was ever opened, read, printed, or committed by this
  agent; the one edit to `.env` was a blind append of a single
  user-dictated non-secret line.

## Phases completed

- Phase 3.0 — re-ran pre-edit compile and the focused lifecycle baseline
  (`98 passed`); confirmed `.gitignore` filename coverage; confirmed the
  local secret handoff file's existence without opening it; designed the
  non-secret `FIRECRAWL_*` config surface (default-deny allowlist).
- Phase 3.1 — `rag/ingestion/firecrawl.py`: a narrow httpx-based
  Firecrawl v2 adapter (`search_preview`, `scrape_markdown` only; no
  map/crawl/actions/custom headers/cookies/proxy/OCR/cloud-parser
  surface), typed outcome classification, bounded retries (max 2, only
  on 408/429/500/502/503/504, respecting `Retry-After` including the
  HTTP-date form), a streaming byte-budget cap enforced before appending
  each chunk, and a wall-clock stream deadline independent of per-chunk
  I/O timeouts. The API key is read from the environment at call time
  only and never appears in a repr or exception message.
- Phase 3.2 — `rag/lifecycle/web_safety.py`: HTTPS-only URL syntax
  validation, a blocked-hostname list (localhost/`*.localhost`/metadata
  hostnames), request-time DNS resolution rejecting any resolved address
  that is private/loopback/link-local/multicast/reserved/unspecified
  (IPv4 and IPv6), and a server-owned domain allow/deny policy defaulting
  to deny-all with the denylist always winning. Matching non-secret
  `FIRECRAWL_*` settings added to `app/core/config.py`.
- Phase 3.3 — `rag/lifecycle/web_pipeline.py` (candidate build reusing
  the existing Markdown loader/section builder/chunker, producing an
  extraction record in the *same* schema `rag/lifecycle/pipeline.py`
  uses so the existing `LifecycleService.review/publish/rollback`
  integrity checks accept it unchanged) and `rag/lifecycle/web_import.py`
  (`WebImportService`: runs every URL through `web_safety` before any
  adapter call; document identity is `web-{sha256(canonical_url)[:24]}`,
  never the title; idempotent on unchanged content checksum). Extended
  the SQLite registry with `web_provenance`/`acquisition_attempts`
  tables. Added `scripts/web_import.py`, a local-only CLI because the
  application has no admin authorization to gate a public FastAPI route.
- Phase 3.4 — `rag/lifecycle/web_diff.py`: a deterministic (no LLM)
  changed-section summary comparing sections by heading path and content
  hash between the prior and new `canonical.md`. Wired into
  `WebImportService.import_url` so a content-changed recrawl creates a
  new, still-candidate version linked via `prior_version_id`/`diff_path`.
- Two read-only audits (Explore agent, substituting for Antigravity,
  which is not an available agent type on this platform — recorded once
  as `AGY_UNAVAILABLE`): after Phase 3.2, found three adapter hardening
  gaps (fixed in `e6f52cb`) and a DNS-rebinding/TOCTOU limitation
  inherent to using a third-party hosted scraper (documented below, not
  fixable in this codebase); before the first result, found two real
  recrawl-diff bugs (fixed in `d2bd02b`). Every finding was independently
  re-verified by reading the diff before committing a fix.
- Phase 3.5 — authenticated live proof, run only after the user's
  explicit in-session secret confirmation and after they configured the
  domain allowlist themselves:
  - Fixed two real defects the live run surfaced immediately:
    `scripts/web_import.py` never added the repo root to `sys.path`
    (`ModuleNotFoundError: No module named 'app'`, matching the exact
    pattern already documented for other direct-script invocations in
    this project), and never loaded `.env`/`.env.firecrawl.local` at all
    (fixed in `7a1d042`, following the exact `sys.path` convention
    already used by every other script in `scripts/`).
  - One bounded `search_preview(limit=1)` call returned exactly one
    descriptor: title "Giáo dục đại học: Trang chủ", URL
    `https://undergrad.tdtu.edu.vn/`. A UnicodeEncodeError while printing
    the Vietnamese title (Windows console codepage) forced one corrective
    re-run after fixing `sys.stdout` to UTF-8 in `2e0781e`; both search
    attempts are visible, unmodified, in `acquisition_attempts` rather
    than hidden.
  - The user was shown that single result and explicitly approved
    scraping it before any scrape call was made.
  - One bounded `scrape_markdown` call on that approved, allowlisted URL
    succeeded: HTTP 200, `parse_status=ok`, stored strictly as
    `review_status=candidate` (`document_id=web-88b8c28734c6c0199ae608b8`,
    `version_id=c013dd02f93043d49ccf147d2701e99a`). The live manifest and
    chunks files were verified byte-for-byte unchanged
    (`git status --short -- data/manifests data/chunks` empty) before and
    after.
  - `credits_used` and `firecrawl_action_id` came back `None` on the real
    response (the account's response did not surface an
    `x-credits-used`-style header or a top-level `id` field the adapter
    looks for) — recorded as a known limitation, not papered over.
  - Full offline regression re-run after the live call (below) confirms
    the live call did not disturb the existing corpus or test suite.

## Files changed

- `74e5113 feat(gate-03): add bounded firecrawl adapter`
  - `rag/ingestion/firecrawl.py`; `tests/test_firecrawl_adapter.py`
- `22d99bc feat(gate-03): enforce bounded web import safety`
  - `rag/lifecycle/web_safety.py`; `tests/test_web_safety.py`;
    `app/core/config.py`; `tests/test_firecrawl_adapter.py`
- `e6f52cb fix(gate-03): harden firecrawl adapter after safety audit`
  - `rag/ingestion/firecrawl.py`; `tests/test_firecrawl_adapter.py`
- `6e2bb8a feat(gate-03): import firecrawl pages as candidates`
  - `rag/lifecycle/web_pipeline.py`; `rag/lifecycle/web_import.py`;
    `rag/lifecycle/registry.py`; `scripts/web_import.py`;
    `tests/test_web_import.py`; `app/core/config.py`
- `db68ed6 feat(gate-03): track recrawl candidate diffs`
  - `rag/lifecycle/web_diff.py`; `rag/lifecycle/web_import.py`;
    `rag/lifecycle/registry.py`; `tests/test_web_recrawl_diff.py`
- `d2bd02b fix(gate-03): correct recrawl diff on repeated headings and stale paths`
  - `rag/lifecycle/web_diff.py`; `rag/lifecycle/web_import.py`;
    `tests/test_web_recrawl_diff.py`
- `b178c4b docs(gate-03): record web import result` (intermediate,
  `WAITING_FOR_USER_SECRET`)
  - `PROJECT_STATE.md`; `gates/results/GATE_03_RESULT.md`;
    `gates/baselines/GATE_03_RETRIEVAL_SMOKE.json`
- `7a1d042 fix(gate-03): load .env and .env.firecrawl.local in the web-import CLI`
  - `scripts/web_import.py`
- `2e0781e test(gate-03): verify bounded web import controls`
  - `scripts/web_import.py` (sys.path + UTF-8 stdout fixes surfaced by
    the live run); `gates/baselines/GATE_03_RETRIEVAL_SMOKE.json`
    (regenerated post-live-proof, metrics unchanged)
- This final result/state commit
  - `PROJECT_STATE.md`; `gates/results/GATE_03_RESULT.md`
- Not changed by Gate 03: `external_tools/firecrawl` (still clean, still
  pinned, never started); `external_tools/markitdown`; the existing
  37-document corpus, `data/processed/processed_docs.jsonl`,
  `data/manifests/documents_manifest.csv`, `data/chunks/*`; any other
  application route; Docker/compose files; `requirements.txt` (no new
  dependency — httpx was already pinned); `.env.example`; the pre-existing
  dirty overlay. `.env` received exactly one appended, user-dictated,
  non-secret line (`FIRECRAWL_ALLOWED_DOMAINS=undergrad.tdtu.edu.vn`);
  `.env.firecrawl.local` was never opened, read, or edited by this agent.

## Commands/tests executed

All commands used `.venv/Scripts/python.exe` with
`PYTHON_DOTENV_DISABLED=true` and `LLM_PROVIDER=mock` for every offline
run; the two live Firecrawl calls in Phase 3.5 ran without that flag so
the CLI would load the real `.env`/`.env.firecrawl.local`.

- Pre-edit compile and focused lifecycle baseline — passed (`98 passed`),
  before any Gate 03 edit.
- Compile + focused tests after each phase — passed every time; full
  `pytest -q` (workspace basetemp) grew monotonically with each phase's
  new tests only: `211 -> 214 -> 228 -> 234 -> 236 passed, 0 failed`,
  unchanged after Phase 3.5's two CLI fixes.
- Final full regression, run again immediately after the live proof:
  - `compileall -q app rag scripts evals frontend tests` — passed.
  - `pytest -q` (workspace basetemp) — **236 passed, 0 failed** (157
    pre-Gate-03 + 79 new: 17 adapter, 40 safety, 14 import, 8
    recrawl/diff).
  - `scripts/validate_chunks.py` — 1036/695/572 rows, abnormal 0 —
    identical to Gate 00-02.
  - `scripts/validate_processed_docs.py` — 37/37, success rate 1.000 —
    identical to Gate 00-02.
  - `scripts/verify_manifest.py` — 37 rows, 0 duplicate checksum groups —
    identical to Gate 00-02.
  - `python -m evals.experiments.run_retrieval_eval ... --output
    gates/baselines/GATE_03_RETRIEVAL_SMOKE.json` — 695 chunks, 20
    queries, recall@5 `0.8889`, MRR `0.5917`, precision@5 `0.1889`,
    recall@3 `0.7222`, recall@10 `0.8889`, answerable `18` — bit-for-bit
    identical to `gates/baselines/GATE_02_RETRIEVAL_SMOKE.json` (that
    file was not overwritten).
- Live Firecrawl calls: one `search` request (plus one corrective re-run
  after a local encoding bug, both `status_class=ok`, `http_status=200`);
  one `scrape` request (`status_class=ok`, `http_status=200`,
  `parse_status=ok`). No crawl/map call was made; no retry occurred (no
  retryable status code was returned); no key value was ever printed,
  logged, or committed.

## Acceptance checklist

- [x] Secret handoff policy followed — `.env.firecrawl.local` never
      opened/read/edited by this agent; confirmation came only from the
      user's own explicit statement in this session.
- [x] Search/scrape work after user secret confirmation — both live
      calls happened only after that confirmation and after the user's
      own domain-allowlist configuration; the scrape additionally
      required the user's explicit per-URL approval.
- [x] Private-network targets blocked — `rag/lifecycle/web_safety.py`
      with 14 dedicated tests plus two end-to-end tests proving a
      blocked target never reaches the adapter transport.
- [x] Crawl/page/byte/depth/time/retry budget enforced — no
      map/crawl/actions method exists on the adapter; every import is
      exactly one page, depth 0; byte cap enforced during streaming;
      wall-clock stream deadline; retries bounded to 2, only on
      408/429/500/502/503/504.
- [x] Imported page becomes a candidate, not a live source — proven both
      offline (mocked tests) and live (the real scraped version stayed
      `review_status=candidate`; live manifest/chunks bytes unchanged).
- [x] Provenance retained — canonical URL, UTC retrieval timestamp, HTTP
      status/status class, content checksum, domain, and adapter/parser
      policy version were all persisted for the real scraped version
      (credits/action-id came back `None` from the real API and are
      recorded as such, not fabricated).
- [x] Recrawl creates a new version/diff — unchanged content is
      idempotent; changed content creates a new linked version with a
      deterministic diff, correctly handling repeated heading paths and
      a missing prior file.
- [x] 429/error handling tested — distinct typed outcomes for all seven
      status classes, each with a dedicated mocked test.
- [x] `gates/results/GATE_03_RESULT.md` written using the required format.

## Evidence artifacts

- `gates/baselines/GATE_03_RETRIEVAL_SMOKE.json` — offline BM25 smoke,
  regenerated post-live-proof; bit-for-bit identical metrics to Gate 02.
- 79 new automated tests across 4 files: `tests/test_firecrawl_adapter.py`
  (17), `tests/test_web_safety.py` (40), `tests/test_web_import.py` (14),
  `tests/test_web_recrawl_diff.py` (8).
- Ten Gate 03 commits, each preceded by a passing focused test run, a
  full compile, and `git diff --cached --check`.
- The one real candidate created live: `document_id=
  web-88b8c28734c6c0199ae608b8`, `version_id=
  c013dd02f93043d49ccf147d2701e99a`, `review_status=candidate` — inspected
  via the registry's safe metadata fields only; its raw scraped Markdown
  was never printed to this conversation.
- Existing corpus/processed/manifest/chunk hashes independently compared
  to Gate 00-02 and match exactly, both before and after the live call.

## Known issues

- **DNS-rebinding / TOCTOU across the Firecrawl boundary.** This app
  resolves and rejects private targets before ever calling Firecrawl, but
  Firecrawl's own hosted infrastructure re-resolves the URL independently
  when it performs the actual fetch. This is a SaaS-boundary limitation
  this codebase cannot close unilaterally; recorded as residual risk, not
  a defect in the code written here.
- **`credits_used`/`firecrawl_action_id` were `None` on the one real
  scrape response.** The adapter looks for an `x-credits-used`/
  `x-firecrawl-credits-used` response header and a top-level `id` field;
  neither appeared on this account's real response. Provenance is still
  fully useful (URL, timestamp, checksum, HTTP status all present); a
  future gate could adjust the parsing if the exact real field names are
  confirmed against more live responses, but this Gate does not fabricate
  a value that was not actually returned.
- Candidate directories are not currently pruned/garbage-collected; a
  recrawl diff explicitly detects and reports a missing prior canonical
  file rather than silently masking it, but nothing in this Gate adds
  retention/cleanup policy for old candidate artifacts.
- The existing single-writer assumption for `LifecycleRegistry` (recorded
  in Gate 01/02) is unchanged.
- No FastAPI route was added for web import (by design — the app has no
  admin authorization to gate a public endpoint); `scripts/web_import.py`
  is a local-only CLI. If a future gate adds real admin authorization,
  wiring an HTTP route on top of the existing `WebImportService` would be
  additive, not a rewrite.
- The two-search-call deviation in Phase 3.5 (a local Windows console
  UnicodeEncodeError forced one corrective re-run) is recorded above,
  not hidden; both calls were harmless (`status_class=ok`, no retry, no
  extra scrape).

## Next allowed Gate

Gate 04, only in a new explicit session after independently re-verifying
this Gate 03 PASS result and its evidence.

## STOP

No next-Gate work performed.
