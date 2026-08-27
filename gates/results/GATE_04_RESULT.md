# Gate 04 Result

Status: PASS

## Commit / tree state

- Starting revision: `31396a3` (HEAD == `origin/main`, live-verified with
  `git ls-remote origin main` before any edit). `72e11aa` (Gate 03 final
  result/state commit, `Status: PASS`) confirmed an ancestor of `HEAD` via
  `git merge-base --is-ancestor`.
- The pre-existing dirty overlay (`AGENTS.md` modified, `rag/generation/
  groq_client.py` modified [one pre-existing blank-line-at-EOF only --
  confirmed with `git diff --check`, not a Gate 04 change], five
  `skills/*/scripts/*.py` deletions, the untracked `_agent_ops/` bootstrap
  layer -- `PHASE_ROADMAP.md`, `archive/`, `env_templates/`, gate cards
  03/05-10, additional tools -- and `tests/test_groq_rotation.py`) remained
  present, untouched, and unstaged throughout. No reset, restore, clean,
  stash, `git add .`, amend, or rebase was used. The Git index was empty
  before every Gate 04 edit and remains empty now (nothing was staged).
  No push was performed.
- No Gate 04 file overlapped any pre-existing dirty path, so no
  stop-and-ask was triggered.

## Exact source scope

Files added:

- `rag/retrieval/version_resolver.py`
- `rag/generation/evidence_state.py`
- `gates/baselines/GATE_04_RETRIEVAL_SMOKE.json`
- `tests/test_version_resolver.py`
- `tests/test_context_builder_versioning.py`
- `tests/test_evidence_state.py`
- `tests/test_answer_generator_evidence_state.py`
- `tests/test_evidence_trace.py`
- `tests/test_gate04_fixtures.py`

Files modified:

- `rag/retrieval/index_store.py` -- added `ChunkIndexStore.index_version`.
- `rag/retrieval/__init__.py` -- exported `VersionResolver`/`ChunkVersionInfo`.
- `rag/generation/context_builder.py` -- optional `version_resolver`
  param; attaches a `"version"` dict per chunk and `chunk_versions`/`query`
  into `retrieval_debug` when a resolver is wired in.
- `rag/generation/answer_generator.py` -- added `_finalize_response()`
  (citation_verification + evidence_state + generation trace), wired into
  every return path via `_refusal_payload` plus the explicit success/
  fallback branches.
- `app/core/config.py` -- added `get_lifecycle_registry()` (now shared by
  `get_lifecycle_service()`/`get_web_import_service()`) and
  `get_version_resolver()`; wired into `get_context_builder()`;
  `refresh_live_caches()` clears the new caches too.
- `app/api/routes_query.py` -- the `use_reranker=True` branch's ad hoc
  `ContextBuilder` now also receives the version resolver.
- `app/api/routes_agent.py` -- `citations_verified` now reads the real
  `CitationVerifier` result (falls back to the old heuristic only if the
  answer generator does not provide one); `debug` payload gained a
  `generation` trace; response gained `citation_verification`/
  `evidence_state`.
- `app/schemas/query.py` -- added `CitationVerification`, `EvidenceState`,
  `GenerationTrace` models; added optional `citation_verification`/
  `evidence_state`/`generation` fields to `AskResponse`; added
  `citation_verification`/`evidence_state` to `AgentAskResponse`.
- `tests/test_api_documents_lifecycle.py` -- its `_clear_caches()` helper
  updated to also clear the two new cached functions (fixes a real
  regression this caused mid-Phase-4.1; see Phase 4.1 below).

Not touched: `data/manifests/documents_manifest.csv`, `data/chunks/*`,
`data/processed/processed_docs.jsonl`, any Gate 00-03 baseline/result file,
`external_tools/*`, Docker/compose files, `requirements.txt` (no new
dependency), `.env`/`.env.*`, any existing FastAPI route path (`/ask`,
`/agent/ask`, `/retrieve` keep their existing paths; no new route added),
the pre-existing dirty overlay.

## Phased implementation summary

- **Phase 4.1 -- Version-aware retrieval.** `VersionResolver` resolves
  every retrieved chunk's `source_id`/`source_version`/`index_version`/
  `authority_state`/`freshness_state` deterministically, reusing the
  existing lifecycle registry and the existing `load_manifest_rows`
  manifest loader (already used by `AdvancedHybridRetriever`). Legacy
  (non-registry-tracked) documents get `legacy:{checksum[:16]}` derived
  from the manifest's existing `checksum` column; unresolved evidence
  stays `"unknown"`, never guessed. `index_version` is a deterministic
  sha256 of the live chunks file's bytes (or of chunk id/checksum pairs
  in-memory), never a random run id. `freshness_state`/`conflict_key` are
  opt-in via `stale_after`/`conflict_key` manifest-row keys that the real
  37-doc corpus never sets -- so real freshness/conflict resolution stays
  `unknown`/`None`, a deliberate no-op on baseline data. Attached
  additively to each chunk dict inside `ContextBuilder.build()` (the
  single choke point every retriever's output funnels through), never
  touching ranking or per-retriever code. A real regression was found and
  fixed mid-phase: an existing lifecycle test's manual cache-clear helper
  was missing the two new `lru_cache`d functions, leaking a tmp-path
  registry across tests; fixed and reverified green.
- **Phase 4.2 -- Deterministic stale/conflict/evidence states.**
  `resolve_evidence_state()` computes `supported` /
  `insufficient_evidence` / `stale_source` / `source_conflict` with an
  explicit, documented precedence (`insufficient_evidence` >
  `source_conflict` > `stale_source` > `supported`), reasoning only over
  the Phase 4.1 version metadata already attached to cited chunks -- no
  LLM or heuristic text-similarity conflict detection. Wired into
  `AnswerGenerator` via a new `_finalize_response()` helper called from
  every return path. In scope, a real pre-existing bug was fixed:
  `routes_agent.py`'s `citations_verified` field was a presence heuristic
  (`bool(citations) and not refusal`) that never consulted the actual
  `CitationVerifier` result, directly contradicting Gate 04's "distinguish
  citation verification from answer correctness" requirement. It now
  reads the real verification result end to end.
- **Phase 4.3 -- Evidence trace.** Extended the existing
  `retrieval_debug`/`AgentAskResponse.debug` trace surfaces (no new
  route): added the missing `query` field to `retrieval_debug` (it already
  had retriever/backend/top_k/chunk_ids/scores, plus `chunk_versions` from
  Phase 4.1); added a real, measured `generation` trace
  (provider/model/fallback_used/error/latency_ms) wherever a provider call
  actually happens, omitted (not invented) for guardrail refusals that
  never reached a provider. `AskResponse` gained an optional `generation`
  field; `/agent/ask`'s `debug` payload gained the same block alongside
  its existing (unchanged) top-level provider/model/latency_ms.
- **Phase 4.4 -- Controlled regression evaluation.** Four isolated
  `tmp_path` fixtures: (1) retired-version exclusion proven at the live
  retrieval level through the real `LifecycleService` publish/retire cycle
  -- the retired document's chunks are structurally absent from a freshly
  reloaded index and from both hybrid/bm25 retrieval results, not merely
  down-ranked, while the resolver's diagnostic path (direct registry
  access) still correctly reports it `retired`; (2) two active official
  sources sharing a `conflict_key` in a real on-disk manifest CSV (through
  the real `load_manifest_rows` code path) yield `source_conflict`; (3)
  the same real-CSV mechanism with a `stale_after` column yields
  `stale_source`; (4) a manifest shaped exactly like the real corpus (no
  opt-in keys) yields `supported`, with answer/citations/confidence
  byte-identical whether or not a `VersionResolver` is wired in.

## Commands / results

All offline commands used `.venv/Scripts/python.exe` with
`PYTHON_DOTENV_DISABLED=true` and `LLM_PROVIDER=mock`.

- Pre-edit baseline (Phase 0): `compileall` clean; `pytest -q` -- **236
  passed, 0 failed** (matches the historical reference exactly);
  `validate_chunks.py --chunks-dir data/chunks` -- 1036/695/572 rows,
  abnormal 0; `validate_processed_docs.py` -- 37/37, 1.000;
  `verify_manifest.py` -- 37 rows, 0 duplicate checksum groups; retrieval
  smoke reproduced into an OS temp path -- bit-for-bit identical to
  `GATE_03_RETRIEVAL_SMOKE.json` (recall@3 0.7222, recall@5 0.8889,
  recall@10 0.8889, mrr 0.5917, precision@5 0.1889, answerable 18/20).
- Per-phase: `compileall` clean and `git diff --check` clean (only the
  pre-existing `groq_client.py:235` overlay warning, never a Gate 04 file)
  after every phase; full `pytest -q` grew monotonically with each phase's
  new tests only: `236 -> 251 -> 266 -> 271 -> 275 passed, 0 failed`
  (15 + 15 + 5 + 4 = 39 new tests total).
- Final regression, re-run after Phase 4.4:
  - `compileall -q app rag scripts evals frontend tests` -- clean.
  - `pytest -q` (workspace-relative basetemp) -- **275 passed, 0 failed**
    (236 pre-Gate-04 + 39 new: 13 version-resolver, 2 context-builder-
    versioning, 11 evidence-state, 4 answer-generator-evidence-state
    integration, 5 evidence-trace, 4 Gate-04 controlled fixtures).
  - `scripts/validate_chunks.py --chunks-dir data/chunks` -- 1036/695/572
    rows, abnormal 0 -- identical to Gate 00-03.
  - `scripts/validate_processed_docs.py` -- 37/37, success rate 1.000 --
    identical to Gate 00-03.
  - `scripts/verify_manifest.py` -- 37 rows, 0 duplicate checksum groups
    -- identical to Gate 00-03.
  - `git status --short -- data/ gates/baselines/` before writing the new
    smoke artifact -- empty (frozen corpus/manifests/chunks and Gate 00-03
    baselines untouched).
  - `python -m evals.experiments.run_retrieval_eval --chunks
    data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl
    --retriever bm25 --top_k 5 --output
    gates/baselines/GATE_04_RETRIEVAL_SMOKE.json` -- metrics bit-for-bit
    identical to `GATE_03_RETRIEVAL_SMOKE.json` except `latency_ms`
    (timing, never a frozen metric): recall@3 0.7222, recall@5 0.8889,
    recall@10 0.8889, mrr 0.5917, precision@5 0.1889, answerable 18/20.

## Test counts

- Pre-Gate-04 baseline: 236 passed.
- Gate 04 new tests: 39 (13 + 2 + 11 + 4 + 5 + 4 across the six new/phase
  test files listed above).
- Final total: **275 passed, 0 failed**.

## Baseline metric / hash comparisons

- Retrieval smoke (BM25, `dev_qa.jsonl`, top_k 5): recall@3/5/10, MRR,
  precision@5, and answerable-query-count are bit-for-bit identical
  between `GATE_03_RETRIEVAL_SMOKE.json` and the new
  `GATE_04_RETRIEVAL_SMOKE.json`.
- Corpus validators (`validate_chunks`, `validate_processed_docs`,
  `verify_manifest`): identical row counts, abnormal counts, and success
  rates before and after Gate 04.
- `git status --short -- data/ gates/baselines/` empty both before the
  Phase 0 baseline and again just before writing the new Gate 04 smoke
  artifact: the frozen 37-document corpus, its manifest, and its chunk
  files are byte-identical to Gate 00-03 throughout.
- `test_normal_educational_qa_fixture_remains_supported_and_unchanged`
  (Phase 4.4) directly asserts the deterministic answer/citations/
  confidence are byte-identical whether or not a `VersionResolver` is
  wired into `ContextBuilder`, on a manifest shaped exactly like the real
  corpus.

## Fixture coverage

- Active vs. retired version: `tests/test_gate04_fixtures.py::
  test_retired_version_excluded_from_live_retrieval_by_removal_not_reranking`
  (live-retrieval-level, via the real publish/retire cycle) plus
  `tests/test_version_resolver.py::
  test_fully_retired_registry_document_resolves_retired_authority_diagnostically`
  (resolver diagnostic path).
- Conflicting official sources: `tests/test_evidence_state.py`
  (unit-level precedence/edge cases),
  `tests/test_answer_generator_evidence_state.py::
  test_two_conflicting_active_official_sources_yield_source_conflict`
  (end-to-end, synthetic dicts), `tests/test_gate04_fixtures.py::
  test_conflicting_official_sources_fixture_yields_source_conflict_via_manifest_csv`
  (end-to-end, real on-disk manifest CSV).
- Stale source: `tests/test_evidence_state.py` (unit),
  `tests/test_answer_generator_evidence_state.py::
  test_stale_cited_source_yields_stale_source_state_with_valid_citations`,
  `tests/test_gate04_fixtures.py::
  test_stale_source_fixture_yields_stale_source_via_manifest_csv`.
- Ordinary/normal educational QA: `tests/test_answer_generator_evidence_state.py::
  test_normal_educational_qa_is_supported_and_citations_are_verified`,
  `tests/test_gate04_fixtures.py::
  test_normal_educational_qa_fixture_remains_supported_and_unchanged`, and
  the full pre-existing test suite (236 tests) passing unchanged against
  the real 37-doc corpus through the real `/ask` endpoint
  (`tests/test_api_ask.py`, `tests/test_evidence_trace.py`).

## Trace / citation evidence

- `tests/test_evidence_trace.py` structurally asserts, against the real
  `/ask` and `/agent/ask` endpoints on the real corpus: `retrieval_debug`
  contains `query` (verbatim), `retriever`, `backend`, `chunk_ids`,
  `scores`, and `chunk_versions` (each entry with the exact 6-key
  `ChunkVersionInfo` shape); `chunk_ids` and `scores` share the same
  deterministic order and `support_score` is sorted descending;
  `citation_verification`/`evidence_state` are present and
  `evidence_state.state` is one of the four defined states; a non-refusal
  answer carries a `generation` block with `provider`/`model`/
  `fallback_used`/`error`/`latency_ms`; a guardrail refusal has
  `generation: null` (never fabricated) while `citation_verification.is_valid`
  stays trivially `True`.
- Citation verification is independently enforced and never conflated with
  evidence state: `tests/test_answer_generator_evidence_state.py::
  test_stale_cited_source_yields_stale_source_state_with_valid_citations`
  and the Gate 04 fixtures' conflict/stale tests all assert
  `citation_verification.is_valid is True` at the same time as a
  non-`supported` `evidence_state`, proving the two axes are computed and
  reported independently, never merged into one verdict.
- The one pre-existing `citations_verified` assertion in
  `tests/test_api_agent.py` (a case where the provider's citations were
  invalid and the app rebuilt the answer from verified retrieved chunks)
  still passes now that the field reflects the real verifier result
  instead of a heuristic.

## Known limitations and residual risks

- `freshness_state`/`conflict_key` are opt-in manifest-row keys, not a
  column on the real, tracked `documents_manifest.csv`. This was a
  deliberate scope decision (never touch the frozen corpus/manifest
  schema), so the real 37-doc corpus cannot currently surface
  `stale_source`/`source_conflict` on its own; a future gate would need an
  explicit, reviewed decision to add those columns (or an equivalent
  registry-backed mechanism) to the live manifest if real staleness/
  conflict detection on the existing corpus is required.
- `index_version` changes whenever the backing chunks file's bytes change
  (including a publish/retire that only touches an unrelated document,
  since `apply_live_state` rewrites the whole file). This is intentional
  (index-wide identity, not per-document), but it means `index_version`
  alone cannot answer "did *this* document's index entry change" --
  `source_version` is the correct field for that.
- The registry-aware "retired" authority classification in
  `VersionResolver` is diagnostic-only for documents that are ever fully
  retired via the registry, since `apply_live_state` already removes such
  a document's chunks from the live corpus entirely; it cannot be
  exercised through a live `/ask`/`/agent/ask` call, only through direct
  registry access (as the Phase 4.1/4.4 tests do). This is expected, not a
  gap: exclusion is enforced by removal, and the resolver path exists only
  for audit/diagnostic tooling that has direct registry access.
- Generation latency in the trace (`generation.latency_ms`) measures only
  the prompt-build + provider-call (+ optional retry) span inside
  `AnswerGenerator`, not context retrieval or (for `/agent/ask`) the
  tool-calling round trip; `AgentAskResponse.latency_ms` remains the
  full-round-trip measurement and was deliberately left as-is rather than
  overwritten.
- No new dependency was added; no existing FastAPI route, Docker/compose
  file, or provider configuration was touched.

## Files changed (summary)

See "Exact source scope" above for the full list. Nine new files, ten
modified files; the pre-existing dirty overlay (`AGENTS.md`,
`rag/generation/groq_client.py`, five deleted `skills/*/scripts/*.py`
files, the untracked `_agent_ops/` bootstrap layer, `tests/test_groq_rotation.py`)
remains present, untouched, and unstaged.

## Acceptance checklist

- [x] Retired version excluded from normal retrieval --
      `test_retired_version_excluded_from_live_retrieval_by_removal_not_reranking`
      proves structural removal (not down-ranking) at the live-retrieval
      level through the real publish/retire cycle.
- [x] Conflict fixture produces explicit conflict state --
      `test_conflicting_official_sources_fixture_yields_source_conflict_via_manifest_csv`
      and the Phase 4.2 unit/integration tests.
- [x] Index version visible in trace -- `retrieval_debug.chunk_versions`
      (via `/ask`) carries `index_version` for every selected chunk,
      asserted structurally in `tests/test_evidence_trace.py`.
- [x] Citation verifier still enforced -- the real `CitationVerificationResult`
      is threaded through every response path (`_finalize_response`);
      `routes_agent.py`'s previously-heuristic `citations_verified` now
      reflects it; independence from `evidence_state` is directly tested.
- [x] Baseline regression threshold met -- full suite 236 -> 275 (39 new,
      0 regressions after the one mid-Phase-4.1 fix); corpus validators
      and retrieval-smoke metrics identical to Gate 00-03.
- [x] `GATE_04_RESULT.md` written using the required format.

## Next allowed Gate

Gate 05, only in a new explicit session after independently re-verifying
this Gate 04 PASS result and its evidence.

## STOP

No Gate 05 work performed.
