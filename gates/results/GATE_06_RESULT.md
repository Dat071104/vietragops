# Gate 06 Result

Status: PASS

This is an infrastructure gate. It builds deterministic tooling for a
later scientific Gate-0; it makes no research/scientific claim, contains
no alignment/migration method, and no evaluation of any method was run.

## Entry-gate re-verification (before any Gate 06 edit)

An earlier attempt in this same session ran the mandatory entry gate
first and found two disqualifying gaps against actual repository state:
(1) the bounded local `qwen3:8b` Ollama smoke required by the entry gate
had never actually succeeded (Gate 05 only had an incidental timeout);
(2) Gate 05 had never been committed. It correctly reported
`GATE_06_BLOCKED` and performed no Gate 06 edits. The user then
explicitly authorized closing both gaps.

Both were closed in this session, evidenced in
`gates/results/GATE_05_RESULT.md` (corrected) and
`_agent_ops/DECISION_LOG.md` (DEC-0013): a real bounded local `qwen3:8b`
smoke succeeded via the actual Groq-failure-triggered development-mode
fallback path (`latency_ms: 105656.945`, grounded/correct answer,
citation verified), and the Gate 05 slice was committed separately from
the pre-existing dirty overlay (commit `81589e2`).

Re-verification against the committed state then confirmed:

- `git merge-base --is-ancestor 82d2797 HEAD` and `... 81589e2 HEAD` both
  succeeded -- Gate 04 and the new Gate 05 commit are both ancestors of
  HEAD.
- `git status --short`: only the pre-existing dirty overlay (`AGENTS.md`,
  five `skills/*/scripts/*.py` deletions, `tests/test_groq_rotation.py`,
  the untracked `_agent_ops/` bootstrap layer), unambiguous, no overlap
  with the Gate 05 slice.
- `git diff --cached --name-only`: empty (nothing left staged after the
  Gate 05 commit).
- `git diff --check`: exit 0, clean.
- `_agent_ops/phase_context_cards/evolve_2026_08_26/README.md`,
  `PROJECT_CONTEXT_CARD.md`, `DECISION_LOG.md`, `RISK_REGISTER.md`, and
  `REPO_MAP.md` were all updated in this session to agree with actual
  Gate 04/05 git state (including correcting a stale "Gate 04 ...
  uncommitted" label to reflect its real committed-and-pushed status).

Result: **entry gate PASS.** Gate 06 work proceeded.

## Commit / tree state

- Starting revision for Gate 06 work: `81589e2` (the Gate 05 commit made
  earlier in this session).
- The pre-existing dirty overlay (`AGENTS.md`, five
  `skills/*/scripts/*.py` deletions, `tests/test_groq_rotation.py`, the
  untracked `_agent_ops/` bootstrap layer) remained present, untouched,
  and unstaged throughout Gate 06 work.
- Gate 06 added **only new files** -- no existing tracked file was
  modified by Gate 06 itself (`git diff --check` on the working tree is
  clean with zero warnings, unlike Gate 04/05 which always carried the
  one pre-existing `groq_client.py` EOF warning -- that file was not
  touched in this phase).
- No reset, restore, clean, stash, `git add .`, amend, or rebase was
  used. No push was performed. No commit of the Gate 06 slice has been
  made yet -- pending explicit user authorization, per the same
  git-discipline convention Gate 05 followed.

## Exact source scope

Files added (all new):

- `research/__init__.py`, `research/gate0/__init__.py`
- `research/gate0/contracts/__init__.py`, `research/gate0/contracts/contract.py`
- `research/gate0/sandbox/__init__.py`, `research/gate0/sandbox/store.py`,
  `research/gate0/sandbox/api_v1.py`, `research/gate0/sandbox/api_v2.py`,
  `research/gate0/sandbox/api_v3.py`
- `research/gate0/drift/__init__.py`, `research/gate0/drift/families.py`,
  `research/gate0/drift/manifest.py`
- `research/gate0/oracle/__init__.py`, `research/gate0/oracle/ground_truth.py`
- `research/gate0/evaluator/__init__.py`, `research/gate0/evaluator/capability.py`,
  `research/gate0/evaluator/evaluator.py`
- `research/gate0/traces/__init__.py`, `research/gate0/traces/models.py`,
  `research/gate0/traces/capture.py`
- `research/gate0/harness/__init__.py`, `research/gate0/harness/method_facing.py`
- `tests/test_gate06_contract_model.py` (19 tests)
- `tests/test_gate06_sandbox_versions.py` (19 tests)
- `tests/test_gate06_drift_manifest.py` (10 tests)
- `tests/test_gate06_oracle_boundary.py` (17 tests)
- `tests/test_gate06_traces.py` (9 tests)
- `tests/test_gate06_evaluator.py` (33 tests)
- `tests/test_gate06_product_isolation.py` (4 tests)

**111 new tests total.**

Files modified: none (source). Ops-only: `_agent_ops/DECISION_LOG.md`
(DEC-0014), `_agent_ops/IMPLEMENTATION_LOG.md`, `_agent_ops/REPO_MAP.md`
(regenerated).

Not touched: `data/manifests/documents_manifest.csv`, `data/chunks/*`,
`data/processed/processed_docs.jsonl`, any Gate 00-05 baseline/result
file, `app/*`, `rag/*`, `external_tools/*`, Docker/compose files,
`requirements.txt` (no new dependency), `.env`/`.env.*`, any existing
FastAPI route, the `/mcp` surface, the pre-existing dirty overlay.

## Design decision (full detail in DEC-0014)

- **Module boundary**: new top-level `research/gate0/` package -- a
  research/evaluation-owned module, not product routes, chosen over
  reusing the existing top-level `tools/` (already used for an unrelated
  script) or nesting under `rag/`/`app/`.
- **Sandbox state**: entirely in-memory (`EducationSandboxStore`), never
  touching any filesystem path -- the strongest available form of
  "cannot reach a product path" is touching no path at all.
- **Public/oracle split**: `ToolContract` (internal, has `tool_id`) vs.
  `PublicToolContract` (`.to_public()`, structurally lacks `tool_id` --
  a missing attribute, not a naming convention). `tool_id` is the one
  field that would trivially leak cross-version correspondence if
  exposed, so it never appears on anything method-facing.
- **What "hidden" means**: an execution/import-access boundary enforced
  by tests (static AST scan of the harness module for any oracle
  reference, plus runtime introspection), not cryptographic secrecy
  against a developer with unrestricted repository access -- documented
  explicitly, not overclaimed.
- **Deterministic seed/reset**: `EducationSandboxStore.reset()` restores
  a deep copy of a frozen fixture; `state_hash()` (canonical JSON +
  SHA-256) makes reset-reproducibility and cross-instance isolation
  directly, deterministically testable. Each `DriftCase` also carries a
  fixed `seed` field for future extensibility.

## Phased implementation summary

- **Phase 6.1 -- Tool contract model.** `ToolContract` represents stable
  `tool_id`, `version`, `name`/`description`, `input_schema`/
  `output_schema` (a minimal JSON-schema-subset validator: `type`,
  `properties`, `required`), structured `Precondition`/`Effect` tuples
  (never prose-only), and a deterministic `schema_hash` (canonical JSON
  + SHA-256 over version/name/schemas/preconditions/effects --
  deliberately excluding `description`, which is prose, not schema).
  `validate_contract` rejects malformed identities/names, missing/
  dangling schema fields, unknown precondition/effect kinds, precondition
  targets that reference neither a real input field nor a `state:`-
  prefixed sandbox check, non-JSON-serializable detail/expected values,
  and contradictory effects (`no_mutation` + a mutating kind on the same
  target). 19 tests prove identical contracts hash identically,
  meaningful changes (name/schema/preconditions/effects) alter the hash,
  a description-only change does not, and `tool_id` survives a rename
  while `schema_hash` still changes.
- **Phase 6.2 -- Deterministic fictional education API versions.** Three
  versions (`EducationApiV1/V2/V3`) over one in-memory
  `EducationSandboxStore`, with entirely synthetic identifiers
  (`CRS-*`/`STU-*`/`PROG-*`/`TERM-*`). Every tool's preconditions/effects
  are exercised through real execution (e.g. enrolling into a 0-seat
  course really raises `SandboxStateError`; a real enrollment really
  decrements `seats_available` and is visible in `store.enrollments`).
  `reset()` + `state_hash()` prove byte-for-byte reproducibility across
  repeated resets and fresh store instances; a source-scan test proves
  `store.py` never calls `open()`/`Path()`/touches a DB or network
  client, so sandbox writes structurally cannot reach a product path.
- **Phase 6.3 -- Drift-family matrix.** All 9 required families
  represented, each derived from a real, executed contract pair, not
  authored around a planned method (frozen 10-case manifest in
  `research/gate0/drift/manifest.py`):
  tool rename (`search_course`->`find_module`), argument rename
  (`check_prerequisite`'s args), added required field (`consent_ack`),
  output restructure (`get_timetable`'s nested v2 shape), no-equivalent
  (`submit_leave_request`, confirmed absent at both v1->v2 and v1->v3),
  argument split (`module_code`->`subject_area`+`catalog_number`),
  argument merge (`course_code`+`semester`->`section_code`), tool
  replacement (`create_enrollment`->`finalize_registration`, a genuinely
  new `tool_id` with an added payment precondition, not a rename), and
  semantic near-collision (`find_module` vs. the free-text decoy
  `browse_catalog`, added in v3, different `tool_id`, different
  preconditions/effects). Two additional held-out cases (an
  advisor-note-lineage tool rename and a second argument-merge instance)
  are structurally separate from the graded manifest
  (`held_out_cases()`), disjoint by `case_id`, and untouched by any test
  other than the disjointness check.
- **Phase 6.4 -- Evaluator-only migration ground truth.**
  `MigrationGroundTruth` records, for all 10 graded cases, the exact
  correct new tool (or `None` for no-equivalent), the full old-arg ->
  new-arg(s) mapping (supporting split/merge/dropped-argument shapes),
  new-only required fields, the expected effect kind, and (for the
  output-restructure case) an explicit output-field remapping --
  gated behind `get_ground_truth(case_id, capability)`, which raises
  `PermissionError` for anything that is not a real `EvaluatorCapability`
  instance. `MethodFacingHarness` (`research/gate0/harness/
  method_facing.py`) is the *only* interface a method is ever given:
  it has zero import of `research.gate0.oracle` anywhere in its source
  (proved by AST scan), its task object exposes only
  `PublicToolContract`s (no `tool_id`) plus verified old traces, and
  calling an unknown tool through it fails safely rather than reaching
  internal state.
- **Phase 6.5 -- Verified old successful traces.** `build_verified_
  traces_for_version` runs 4 real, successful calls per version (v1 and
  v2, the two "old" sides used by the graded manifest) on one continuous
  store, each trace recording tool identity/version/schema hash,
  normalized input, precondition outcome, real output, real
  before/after `state_hash`, and a deterministic sequence number.
  Replaying every trace's `normalized_input` against a freshly reset
  store reproduces identical outputs and `state_hash_after` at every
  step. `build_failed_trace_for_version` captures one deliberately
  failing call (`verified=False`, `error` populated, `output=None`),
  kept structurally distinct from the verified set.
- **Phase 6.6 -- Deterministic evaluator and anti-leakage tests.**
  `evaluate_mapping` scores tool selection, argument-pair precision/
  recall (exact set arithmetic over expanded old-arg -> new-arg(s)
  pairs), no-equivalent handling, and effect-kind agreement against the
  real sandbox contract -- returning a structured
  `MappingEvaluationResult` with an explicit `failure_reasons` tuple
  (`wrong_tool_selected`, `missed_no_equivalent`, `false_no_equivalent`,
  `argument_pair_missed:*`, `argument_pair_spurious:*`,
  `effect_kind_mismatch`), never a heuristic confidence score.
  `evaluate_adapted_call` actually attempts a predicted call against a
  fresh sandbox and classifies the real outcome
  (`succeeded`/`precondition_failed`/`malformed_call`/`wrong_tool`).
  Both require a real `EvaluatorCapability`. No LLM, network call, or
  semantic matcher exists anywhere in the evaluator (source-scanned).

## Commands / test counts

All offline commands used `.venv/Scripts/python.exe` with
`PYTHON_DOTENV_DISABLED=true` and `LLM_PROVIDER=mock`.

```bash
python -m compileall -q app rag scripts evals frontend tests research
python -m pytest -q
python scripts/validate_chunks.py --chunks-dir data/chunks
python scripts/validate_processed_docs.py data/processed/processed_docs.jsonl
python scripts/verify_manifest.py data/manifests/documents_manifest.csv
python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5 --output <tmp>
git diff --check
git status --short -- data/ gates/
```

- Pre-Gate-06 baseline (reproduced): **319 passed, 0 failed.**
- Gate 06 new tests: 19 (contract model) + 19 (sandbox versions) + 10
  (drift manifest) + 17 (oracle boundary) + 9 (traces) + 33 (evaluator) +
  4 (product isolation) = **111 new tests.**
- Final full suite: **430 passed, 0 failed.**
- `compileall`: clean, including `research/`.
- Corpus validators: 1036/695/572 rows abnormal 0; 37/37 processed docs
  (1.000); 37 manifest rows, 0 duplicate checksum groups -- identical to
  the Gate 04/05 baseline.
- Retrieval smoke: recall@3 0.7222, recall@5 0.8889, recall@10 0.8889,
  mrr 0.5917, precision@5 0.1889, answerable 18/20 -- bit-for-bit
  identical to `gates/baselines/GATE_04_RETRIEVAL_SMOKE.json` (only
  `latency_ms` differs).
- `git diff --check`: clean (exit 0).
- `git status --short -- data/ gates/`: empty (Gate 06 result file
  itself aside).

## Known limitations

- The capability check (`EvaluatorCapability`) is a real runtime
  `isinstance` check, not a security boundary against a hostile importer
  with full repository access -- documented explicitly in
  `oracle/ground_truth.py` and DEC-0014, matching the entry contract's
  own instruction not to overclaim secrecy against a source-level
  repository owner.
- `evaluate_adapted_call`'s `output_expectation_met` checks required
  output *keys* only (structural), not exact value equality -- sufficient
  for infrastructure verification; a later Gate-0 method evaluation may
  want stricter value-level checks.
- The two held-out cases share the same underlying tool lineage
  (advisor-note) rather than covering additional families; they exist to
  prove the graded/held-out separation mechanism works, not to hold out
  a large reserve.
- `DriftCase.seed` is a frozen field for future extensibility; the
  current 10 cases need no randomness (everything is explicitly
  enumerated), so no test exercises seed-driven generation.

## Acceptance checklist

- [x] v1/v2/v3 reset reproducibly -- `test_reset_is_byte_for_byte_
      reproducible` and `test_repeated_reset_plus_identical_inputs_are_
      deterministic` (both parametrized over all 3 versions).
- [x] >= 8 drift families -- all 9 represented
      (`test_manifest_covers_all_nine_families`).
- [x] Semantic near-collision cases -- `GATE06-CASE-009`, plausibly
      confusable (`find_module` vs. `browse_catalog`) with distinct
      preconditions/effects, scored explicitly wrong when confused.
- [x] No-equivalent cases -- `GATE06-CASE-005`/`010`, a forced
      nearest-tool guess is scored wrong, not accepted as correct.
- [x] Ground truth hidden from evaluated model -- 17-test oracle-boundary
      suite (static AST scan + runtime introspection + capability-gated
      accessor rejecting non-capability callers).
- [x] Verified old traces available -- real executed traces for v1/v2,
      replay-after-reset reproduces identical results, failed traces
      stay distinguishable.
- [x] Task evaluator deterministic -- pure set arithmetic and real
      sandbox execution, zero LLM/network calls, repeatable across 5
      in-process resets and across separate subprocess invocations.
- [x] `GATE_06_RESULT.md` written using the required format.

## Next allowed Gate

Gate 07, only in a new explicit session after independently re-verifying
this Gate 06 PASS result and its evidence, and only after this Gate 06
slice is committed (pending separate explicit user authorization, per
the same git-discipline convention Gate 05 followed).

## STOP

No Gate 07 work performed.
