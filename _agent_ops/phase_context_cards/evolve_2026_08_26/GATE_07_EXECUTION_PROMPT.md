# Gate 07 Execution Prompt — Falsification-First Scientific Gate-0

> **Current status (2026-08-29):** This is the historical execution prompt.
> Gate 07 has since been completed by the committed V4.1 remediation and
> closed with a narrow GO for `argument_split` and `tool_replacement`. Do not
> treat the pending checklists, old HEAD references, or this prompt as a new
> execution authorization. The authoritative result is
> `gates/results/GATE_07_RESULT.md`; Gate 08 remains forbidden.

Copy everything below into one Codex (Luna 5.6 Max) implementation session.

---

## Mission

Execute **Gate 07 only**: try to *falsify* the need for a new cross-version tool
alignment method, before any such method is built. A negative result (`STOP`) is
a successful gate. This prompt is not permission to start Gate 08, and not
permission to implement the proposed intent/alignment model.

Working directory:

    D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps

Python interpreter for **application/repository** commands:

    .venv\Scripts\python.exe

Python interpreter for the **isolated research baseline** (Phase 7.4 and its
offline checks):

    external_tools\research_baselines\.venv\Scripts\python.exe

Never install research dependencies into `VietRagOps\.venv`; the two
interpreters are a hard contamination boundary.

(Gate 00 recorded a false "pytest unavailable" blocker by using a system Python.
Do not repeat it. `.venv` is Python 3.13.9 and has the full test stack.)

At prompt creation the repository was on `main` at `0561d54`, matching
`origin/main`, with a pre-existing dirty overlay. Treat that as a historical
observation only. Re-verify it in Phase 7.0; never assume HEAD alone identifies
the baseline.

---

## Non-negotiable boundaries

- Run Gate 07 and nothing after it. End immediately after `GATE_07_RESULT.md`.
- **Do not implement the proposed intent model, alignment method, or any
  "our method" arm.** Gate 07 evaluates *baselines only*. If you find yourself
  designing something that could win, you have left the gate.
- **Do not cherry-pick.** The case manifest and metric definitions are frozen in
  Phase 7.2 *before* the headline run. Selecting, dropping, or reweighting cases
  after seeing scores is a protocol violation — report it as such rather than
  doing it.
- **Do not treat a provider failure as a wrong answer.** 429, timeout, auth, and
  network failures are a separate outcome class with their own counters. They
  never enter accuracy numerators or denominators without an explicit,
  pre-registered exclusion rule.
- **Research fallback is disabled.** Every live model call in this gate uses
  `ProviderRouter(mode="research")`, which never falls back to Ollama. Product
  `development`/`demo` fallback must not touch a single research number.
- Do not read, print, copy, log, or commit secret values. Do not open `.env`,
  `.env.firecrawl.local`, or any credential file to read a value. You may read
  *variable names* and non-secret config values only where a phase requires it.
- Do not construct quota-evasion behavior. Multi-key Groq rotation already
  exists in this repo and is authorized; use it through the existing client with
  its existing 429 cooldown/backoff/round-robin. Do not add new key sources, new
  accounts, or new pools.
- Do not reset, restore, clean, stash, amend, rebase, force-push, or `git add .`.
  Never stage the pre-existing dirty overlay (`AGENTS.md`, five
  `skills/*/scripts/*.py` deletions, `tests/test_groq_rotation.py`, the untracked
  `_agent_ops/` bootstrap layer). Stage explicit filenames only.
- Do not push. Committing per phase is authorized by this prompt; pushing is not.
- Do not write paper prose, an abstract, related work, or any arXiv-shaped text.
- Do not modify the frozen Gate 06 artifacts (see "Gate 06 is frozen" below).
- Use ordinary, descriptive commit messages. No tool or agent branding, no
  co-author trailers naming an AI.

---

## Start-up and evidence rules

1. Run:

       .venv\Scripts\python.exe _agent_ops\tools\session_start.py --root .

2. Read, in this order, and nothing more until you need it:

       AGENTS.md
       _agent_ops/SESSION_BRIEF.md
       _agent_ops/OPERATING_RULES.md
       _agent_ops/CURRENT_TASK.md
       _agent_ops/phase_context_cards/evolve_2026_08_26/README.md
       _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07.md
       gates/results/GATE_06_RESULT.md
       ..\VietRAGOps_Evolve_Research_Gate_Pack_2026-08-26\gates\GATE_07_SCIENTIFIC_GATE0.md
       ..\VietRAGOps_Evolve_Research_Gate_Pack_2026-08-26\01_MASTER_SCOPE_AND_RESEARCH.md
       ..\VietRAGOps_Evolve_Research_Gate_Pack_2026-08-26\07_RISKS_AND_KILL_CRITERIA.md

3. Read `_agent_ops/REPO_MAP.md` before searching source. Use
   `_agent_ops/tools/explore.py --symbol/--impact` instead of broad grepping.
   Every edge there is tagged `exact`/`heuristic`/`ambiguous`/`weak`; the last
   three are leads to confirm by reading code, never facts.

4. Maintain `_agent_ops/CURRENT_TASK.md` **throughout**, not at the end. Record
   exact files touched, commands run, failures, dead ends with their evidence,
   and the next concrete step. That file is what survives a context compaction.

5. Separate facts, inferences, and blockers in every note and in the result. A
   failed command is evidence. Never substitute a different command to
   manufacture a pass.

6. Never claim a test passed unless you ran it and read its output.

---

## Gate 06 is frozen

`research/gate0/` is committed evidence for a passed gate, pinned by 111 tests.
Gate 07 builds a **new sibling package** `research/gate07/`.

Allowed:

- Import and reuse `research.gate0.contracts` (`ToolContract`,
  `PublicToolContract`, `validate_contract`, `schema_hash`).
- Import and reuse `research.gate0.evaluator.capability.EvaluatorCapability`.
- Read `research.gate0.drift.families` family constants.
- Reuse the *design patterns* of `gate0/sandbox/store.py` (in-memory only,
  frozen fixture, `reset()`, `state_hash()`).

Forbidden without an explicit stop-and-report:

- Editing any file under `research/gate0/`.
- Adding tools/entities to `gate0/sandbox/api_v{1,2,3}.py` or
  `gate0/sandbox/store.py` — this changes `state_hash()` and breaks the frozen
  Gate 06 manifest and its determinism tests.
- Editing `gate0/drift/manifest.py` — the 10 graded cases and 2 held-out cases
  are frozen evidence.

**One narrowly-scoped exception**, and only if you need it: `evaluate_mapping`
and `evaluate_adapted_call` in `research/gate0/evaluator/evaluator.py` resolve
cases through `_case_by_id`, which iterates `build_case_manifest()` only —
so a Gate 07 case id raises `KeyError` today. You may make a **purely additive**
refactor that injects a case resolver with the Gate 06 manifest as its default,
*if and only if* you then prove test-neutrality by running the full suite and
showing all 111 Gate 06 tests plus the other 319 still pass unchanged. If that
proof fails, revert it and give `research/gate07/` its own evaluator that reuses
the scoring arithmetic rather than the module. State which path you took.

---

## Team use and subagents

The root agent owns: user communication, git, `_agent_ops/` writes, evidence
merge, and every final decision. Subagents receive a compact capsule, never
write `_agent_ops/`, and all source changes go through **one writer lane**.

**Subagents must be Codex-native.** Any spawned worker is a native Codex
subagent of this session. Do **not** spawn work through an Antigravity plugin,
an Antigravity-hosted agent, or any other external agent runtime dressed up as a
subagent. Antigravity's only role in this gate is the four bounded read-only AGY
audit jobs described below — it is an outside reviewer, never a lane of the
implementation team. If native Codex subagents are unavailable, run the phase
sequentially and say so; never substitute an external runtime and never claim
sequential work was parallel.

Per-phase concurrency, decided by real write-target independence:

| Phase | Mode | Reason |
|---|---|---|
| 7.0 | solo | Entry gate; a single sequential verification chain. |
| 7.1 | solo writer + 1 read-only auditor | One frozen dataset, one writer. |
| 7.2 | solo | Protocol freeze is a single atomic decision. |
| 7.3 | solo writer + 1 read-only auditor | One harness, one writer. |
| 7.4 | **parallel (up to 3)** | Lexical / embedding / cross-encoder arms write to three disjoint output files and share no state. |
| 7.5 | **sequential — never parallel** | All LLM arms share one Groq rate-limit ledger (`ROUTER_STATE_DB`, `REQUEST_LEDGER`, soft RPM/TPM/RPD accounting). Parallel processes corrupt that accounting and produce fake 429s. One runner process, internal concurrency only through the existing client. |
| 7.6 | solo | Single metrics writer. |
| 7.7 | solo writer + Antigravity blind annotator | Independence is the point of the audit. |
| 7.8 | solo + 1 read-only consistency auditor | One decision owner. |

Reading that table: the three parallel lanes in Phase 7.4 are **native Codex
subagents**. The "read-only auditor" / "blind annotator" in Phases 7.1, 7.3,
7.7, and 7.8 is the **single AGY worker** for that phase — one at a time, never
two at once. So the maximum concurrency anywhere in this gate is either three
Codex subagents (Phase 7.4 only) or one AGY worker, never both at the same time.

### Antigravity workers (Gemini 3.7 Flash High)

Advisory only, read-only, two turns each, small bounded scope. They must not
edit source, ops records, results, git, or credentials. **Independently verify
every load-bearing claim they make** before it enters a result file. If a worker
is unavailable, blocked, or unauthenticated, record `AGY_UNAVAILABLE` once with
the phase and continue — never block a phase on it.

**Single lane, one at a time.** At most **one** AGY worker runs at any moment in
this entire gate. Never fan out AGY jobs, never run two AGY workers
concurrently, and never run an AGY worker alongside another AGY worker from a
different phase. Start it, take its two turns, close it, verify its claims, and
only then move on. An AGY job is also never a dependency of a Codex subagent —
the two never run interleaved on the same artifact.

Four authorized jobs, one per listed phase, executed strictly in this order:

- **AGY-1 (Phase 7.1)** — dataset balance and duplication audit. Given the
  public case manifest *without* the oracle: report family balance, near-duplicate
  case pairs, cases whose candidate lists are trivially solvable by string
  overlap alone, and any case that looks artificial rather than realistic.
- **AGY-2 (Phase 7.3)** — prompt-leakage audit. Given the frozen baseline prompt
  templates and one rendered example per arm: report anything that leaks the
  answer, leaks `tool_id`, leaks family labels, or gives one arm information the
  arm's declared information rights do not permit.
- **AGY-3 (Phase 7.7)** — blind second-pass annotation on the stratified
  ambiguity sample. It must never receive the oracle. Its labels are compared
  against the oracle by the root agent to produce a disagreement rate.
- **AGY-4 (Phase 7.8)** — result-consistency audit. Given `GATE_07_RESULT.md`
  and the raw artifact directory: report every number in the result that it
  cannot reproduce from the raw files.

---

## Phase 7.0 — Entry gate (blocking, no Gate 07 edits allowed until it passes)

Gate 06 entry-gate discipline found two disqualifying gaps that a less careful
session would have papered over. Do the same here, and report `GATE_07_BLOCKED`
rather than proceeding if any item fails.

Checklist:

- [ ] `git rev-parse HEAD`, branch, and `git ls-remote origin main` recorded.
      Confirm whether local HEAD and `origin/main` still agree.
- [ ] `git merge-base --is-ancestor fed31c3 HEAD` succeeds — the Gate 06 commit
      is a real ancestor of HEAD.
- [ ] `git status --short` recorded in full. Every entry classified as
      pre-existing overlay vs. anything new. If anything unexpected appears,
      stop and report rather than absorbing it.
- [ ] `git diff --cached --name-only` is empty.
- [ ] `git diff --check` recorded (exit code and any warning).
- [ ] `gates/results/GATE_06_RESULT.md` exists and its status line reads `PASS`.
- [ ] Full suite reproduced as the pre-Gate-07 baseline:
      `.venv\Scripts\python.exe -m pytest -q` with `PYTHON_DOTENV_DISABLED=true`
      and `LLM_PROVIDER=mock`. Record the exact pass/fail counts. The expected
      figure is 430 passed; if it differs, that difference is a finding, not a
      rounding error.
- [ ] `.venv\Scripts\python.exe -m compileall -q app rag scripts evals frontend tests research`
      clean.
- [ ] Ops-record staleness check: `SESSION_BRIEF.md` and `CURRENT_TASK.md`
      record `Last Verified Commit fed31c3` while HEAD is later. Reconcile them
      against real git state and record the correction.
- [ ] Provider reachability recorded **without spending quota**: Ollama
      `/api/tags` model list, and whether Groq credentials are present as
      *variable names only* (never a value).

**Dependency setup — decision already made by the user, do not re-open it.**

`.venv` has **no** `torch`, `sentence_transformers`, or `transformers`. Gate 07
needs a name/description embedding baseline, a serialized-schema embedding
baseline, and a **cross-encoder** baseline. Verified constraints behind the
decision, so you do not waste time rediscovering them:

- **Groq has no embeddings or reranker endpoint.** It serves chat completions
  only. No amount of `.env` tuning creates one. Groq covers the LLM arms and
  nothing else in this list.
- **Ollama has no reranker endpoint.** It can serve embeddings, but it
  structurally cannot ever produce the cross-encoder arm.
- `01_MASTER_SCOPE_AND_RESEARCH.md` §8 requires *both* an embedding baseline and
  a cross-encoder baseline for the final evaluation, so a setup that skips the
  cross-encoder only defers the same work to Gate 09.

**The chosen setup:** real `sentence-transformers` + CPU `torch`, with
`BAAI/bge-m3` as the bi-encoder and `BAAI/bge-reranker-v2-m3` as the
cross-encoder. Same model family for both arms deliberately — the only
difference between the two is the scoring mechanism (bi-encoder vs. cross-encoder),
not the training corpus, so the comparison is not confounded.

**Install it in an isolated venv, NOT in `VietRagOps/.venv`.** This is a hard
requirement, not a preference:

    external_tools\research_baselines\.venv

`rag/retrieval/dense_retriever.py::_SentenceTransformerBackend` activates
through `importlib.import_module("sentence_transformers")`. Today that import
fails and the product falls back to `_SparseSemanticBackend`. Installing
sentence-transformers into the app venv makes that import succeed and can switch
the product onto dense retrieval — which would move the retrieval-smoke numbers
(`recall@3 0.7222`, `recall@5 0.8889`, `mrr 0.5917`) that Gates 00–06 compare
**bit-for-bit as frozen evidence**. Changing them while installing a research
dependency destroys your own baseline and looks like a regression.

Follow the precedent already recorded in `_agent_ops/THIRD_PARTY_TOOLING.md`:
MarkItDown lives in `external_tools/markitdown/.venv` and explicitly "does not
alter `VietRagOps/.venv` or `requirements.txt`". Do the same here — outside the
application Git root, no change to `requirements.txt`, no new app dependency.

Checklist for this setup:

- [ ] Isolated venv created under `external_tools/research_baselines/`, never
      staged as application code.
- [ ] `VietRagOps/.venv` unchanged — prove it by re-running the retrieval smoke
      after the install and showing the metrics are still bit-for-bit identical
      to `gates/baselines/GATE_04_RETRIEVAL_SMOKE.json`.
- [ ] `requirements.txt` untouched.
- [ ] Model revisions pinned (exact HF revision hash, not just the model name)
      and recorded in `_agent_ops/THIRD_PARTY_TOOLING.md` as new rows, with the
      same pin/verification discipline used for MarkItDown and Firecrawl.
- [ ] Models downloaded once, then run offline (`local_files_only=True`) so the
      baseline is reproducible without network.
- [ ] Offline arms invoke the isolated interpreter as a subprocess; the app venv
      never imports `sentence_transformers`.

**Contamination warning — a failed check blocks the research run.** Installing
`sentence-transformers` or `torch` into `VietRagOps\.venv` activates
`rag/retrieval/dense_retriever.py::_SentenceTransformerBackend` and can change
the frozen Gate 00–06 retrieval-smoke numbers. Before installing, record the
smoke metrics and the `requirements.txt`/application-venv state. After the
isolated install, rerun the exact smoke with the application `.venv` and prove
the load-bearing metrics remain bit-for-bit identical to
`gates/baselines/GATE_04_RETRIEVAL_SMOKE.json` (latency may differ). If they do
not, stop and report contamination; do not reinterpret it as a product
regression and do not repair it by changing the baseline. The research venv
and downloaded model files stay outside the application Git root and are never
staged. The application `.venv` must not import the research packages, and all
offline arms must be launched through the isolated interpreter with
`local_files_only=True` after download.

**Sequencing.** The LLM arms are what actually decide this gate
(`07_RISKS_AND_KILL_CRITERIA.md` §1 names strong direct LLM saturation as the
scientific killer; embedding saturation is not the killer). So run lexical + LLM
arms first. If the LLM arms already saturate, the gate reaches `STOP` and the
embedding/cross-encoder arms only confirm it. Set the isolated venv up early
anyway — it is ~30 minutes of work and the paper needs those arms regardless —
but do not let a model download block Phase 7.5.

**Asymmetry to keep in mind, and to state in the result:** weak baselines cannot
invalidate a `STOP`. If even a weak baseline saturates, a stronger one certainly
would. Weak baselines invalidate only a `GO`. Report which arms were strong and
which were not, and never let a weak arm carry a `GO`.

Cross-encoder honesty rule: an LLM prompted to score old/new tool pairs is **not**
a trained cross-encoder. If one is ever used as a stand-in, label it
`llm_pairwise_scorer` everywhere and never report it as a cross-encoder baseline.

Record this setup in `_agent_ops/DECISION_LOG.md` as a new `DEC-00NN` before any
Phase 7.1 work, including the isolated-venv rationale above.

**Phase 7.0 exit:** no commit (no files changed beyond ops records, which are
committed with Phase 7.1). Report entry-gate `PASS` or `GATE_07_BLOCKED`.

---

## Phase 7.1 — Gate-0 dataset (150–300 cases)

Covers source-pack Phase 7.1.

Gate 06 froze **10 graded cases**. Gate 07 needs **150–300**. This is the
largest gap in the gate and the phase most likely to be faked by generating
noise. Every case must be derived from a real, executed contract pair in a real
sandbox — never authored as free text.

Build `research/gate07/` as follows (respect the ~400-line file / ~50-line
function ceiling from `OPERATING_RULES.md`, and split along responsibility
boundaries, naming the boundary you used):

    research/gate07/__init__.py
    research/gate07/sandbox/          # extended education domain, own store
    research/gate07/dataset/          # operators, generator, frozen manifest
    research/gate07/protocol/         # freeze record + checksums (Phase 7.2)
    research/gate07/baselines/        # arms (Phases 7.4, 7.5)
    research/gate07/metrics/          # aggregation (Phase 7.6)
    research/gate07/runner/           # execution + checkpointing (Phase 7.5)
    research/gate07/oracle/           # expanded hidden ground truth

Checklist:

- [ ] Extend the sandbox tool surface enough to support 150–300 *non-redundant*
      cases. Gate 06 has ~6–8 tools per version; target roughly 25–40 tools per
      version across several education subdomains (courses, enrollment,
      timetabling, advising, assessment, finance, credentials). All identifiers
      stay synthetic; no real institution, person, or record.
- [ ] The Gate 07 store is **in-memory only** — no `open()`, no `Path()`, no DB,
      no network client. Add a source-scan test proving it, mirroring
      `tests/test_gate06_sandbox_versions.py`.
- [ ] `reset()` is byte-for-byte reproducible; `state_hash()` proves it across
      repeated resets, fresh instances, and separate subprocess invocations.
- [ ] Cover **all twelve** drift families from
      `01_MASTER_SCOPE_AND_RESEARCH.md` §6 — the nine Gate 06 families plus the
      three it did not implement:
      **D3** multiple simultaneous renames, **D9** one old tool → multiple new
      tools, **D10** multiple old tools → one generalized new tool.
      D9/D10 mean the ground-truth mapping is no longer 1:1; design the oracle
      and metric shapes for that *before* generating cases, not after.
- [ ] Every case is generated by a **frozen-seed deterministic operator**, then
      *executed* against the real sandbox to confirm the contract pair exists and
      behaves as the case claims. Regenerating the dataset from the seed must
      reproduce it byte-for-byte.
- [ ] Family balance is deliberate and recorded. No family is so rare that its
      metric is noise (state the minimum-per-family floor you chose and why).
      Include a meaningful `no_equivalent` share — forced-mapping safety is a
      headline metric, not a rounding case.
- [ ] Include semantic near-collisions and hard negatives of the
      `request_enrollment` kind from `01_MASTER_SCOPE_AND_RESEARCH.md` §7: a
      plausible new tool that *creates a request* but does not perform the old
      operation. A safe aligner must call these non-equivalent.
- [ ] Hold out a disjoint set (target ~15–20% of cases) covering at least two
      families, structurally separate from the graded manifest, disjoint by
      `case_id`, and untouched by any Phase 7.4/7.5 run.
- [ ] Public/method-facing surface leaks nothing: no `tool_id`, no family label,
      no operator name, no seed on anything a baseline can see. Extend the Gate 06
      oracle-boundary test style (static AST scan + runtime introspection) to the
      Gate 07 harness.
- [ ] Expanded ground truth lives in `research/gate07/oracle/`, gated behind a
      real `EvaluatorCapability` check, same discipline as Gate 06 — and
      documented with the same honesty about what "hidden" does and does not
      mean (an import/execution boundary, not cryptographic secrecy).
- [ ] Tests for everything above. Do not move to Phase 7.2 with a red suite.

**AGY-1** runs here (dataset balance/duplication audit, oracle withheld).
Verify its claims yourself before acting on them.

**Commit when green** (explicit filenames only):

    feat(gate-07): extended education sandbox and Gate-0 case generator

---

## Phase 7.2 — Freeze the protocol (must precede any headline run)

Covers the source pack's "Freeze before running" block. **Nothing in Phases
7.4–7.6 may run before this phase is committed.** If a headline number is
produced before the freeze commit exists, that number is disqualified.

Write `gates/baselines/GATE_07_PROTOCOL.json` — machine-readable, stable,
readable JSON — containing at minimum:

- [ ] schema/version, creation time, git HEAD at freeze time.
- [ ] Dataset: case count, per-family counts, held-out counts, generator seed,
      and a **SHA-256 checksum of the canonicalized graded manifest**.
- [ ] Held-out manifest checksum, recorded separately.
- [ ] Ground-truth checksum (canonicalized oracle content), so a later silent
      edit is detectable.
- [ ] Every baseline arm: `arm_id`, human description, and an explicit
      **information rights** declaration — exactly which of {old contract, new
      contracts, verified old traces, task description, candidate list} that arm
      receives. Arms must differ *only* by declared information.
- [ ] Prompt templates: full text, each with a `prompt_id` and version. Never
      edit a prompt after freeze; add a new versioned id and say why.
- [ ] Exact model IDs, pinned per arm. The repo's configured Groq tiers are
      `qwen/qwen3.6-27b` (RAG/default), `openai/gpt-oss-120b` (strong),
      `openai/gpt-oss-20b` (dev), `llama-3.3-70b-versatile` (versatile); local
      Ollama has `qwen3:8b`, `qwen3.5:4b`, `qwen2.5:7b`, `qwen3:4b`,
      `qwen2.5:3b`, `gemma3:4b`. Verify this list live; do not trust this prompt.
      **Never silently substitute one model for another** — a substitution is a
      new arm with a new `arm_id`.
- [ ] Decoding parameters per arm: temperature, seed, max output tokens.
      Determinism claims must match what the provider actually guarantees; if a
      provider does not guarantee reproducibility, say so rather than implying it.
- [ ] Timeout and retry policy, stated numerically, plus the 429/backoff policy
      the existing Groq client already implements.
- [ ] Metric definitions, written as formulas precise enough to reimplement:
      Tool Alignment@1, Tool Alignment@k, Argument Mapping Precision/Recall/F1,
      False Alignment Rate, No-Equivalent Accuracy, First-Attempt Task Success.
      Define **exactly** how D9/D10 many-to-many mappings score.
- [ ] Exclusion rules, pre-registered: what counts as a provider failure, what
      is retried and how many times, what is excluded from accuracy and how it is
      reported separately. Write this now — writing it after seeing results is
      cherry-picking.
- [ ] Decision thresholds for `GO` / `REFORMULATE` / `STOP`, committed **before**
      any result is seen, derived from the source pack's GO criteria and
      `07_RISKS_AND_KILL_CRITERIA.md` §1–§2. State the numeric bar for
      "saturates" and for "stable, practically meaningful failure region".

Checklist:

- [ ] The JSON parses and every referenced local artifact exists.
- [ ] A test recomputes the dataset checksum from the live manifest and asserts
      it matches the frozen value — so drift is caught mechanically, not by memory.
- [ ] No credentials, no raw provider responses, no environment dump in the file.

If a pre-headline audit discovers leakage or another protocol defect, do not
edit the already-frozen protocol in place. Record the defect as a decision,
create a versioned protocol amendment with a new checksum, prove that zero
headline runs used the superseded record, and commit the amendment before any
headline run.

**Commit:**

    docs(gate-07): freeze Gate-0 protocol, dataset checksum and decision rule

---

## Phase 7.3 — Baseline harness and information rights

Covers the harness half of source-pack Phase 7.2.

Checklist:

- [ ] One `BaselineArm` interface: takes a method-facing task, returns a
      `ProposedMapping`-shaped prediction plus a raw-output record. Arms never
      touch the oracle; enforce with a static AST scan test.
- [ ] The harness enforces each arm's declared information rights *mechanically*.
      An arm that declares no-traces must be structurally unable to read traces,
      not merely trusted not to.
- [ ] Every arm can emit `NO_EQUIVALENT`. An arm that cannot abstain will score
      artificially badly on no-equivalent cases and artificially well elsewhere;
      that asymmetry must not be introduced silently.
- [ ] Raw output retention: every call writes provider, model, `prompt_id`,
      rendered prompt, raw response, latency, token usage, and typed outcome to
      an append-only artifact under `gates/artifacts/gate07/raw/`. Retained raw
      outputs are an acceptance requirement, not a nicety.
- [ ] Confirm `gates/artifacts/` (or your chosen path) is gitignored if the raw
      volume is large, and record where the artifacts live plus their checksums
      in the result. Never commit raw provider dumps that may contain quota or
      key metadata.
- [ ] Deterministic offline arms are tested end-to-end with mock providers.
- [ ] A test proves `ProviderRouter(mode="research")` never falls back: simulate
      a typed Groq failure and assert a terminal outcome with Ollama uninvoked.

**AGY-2** runs here (prompt-leakage audit).

**Commit:**

    feat(gate-07): baseline arm harness with enforced information rights

---

## Phase 7.4 — Offline baselines (lexical, embedding, cross-encoder)

Covers the non-LLM half of source-pack Phase 7.2. **Parallel-eligible: up to 3
subagents**, one per arm family, writing to three disjoint result files.

Arms required (exact set depends on the Phase 7.0 dependency decision):

- [ ] `lexical_name` — normalized string similarity over tool names only.
- [ ] `lexical_serialized` — similarity over the serialized schema text.
- [ ] `embed_name_desc` — name + description embedding, nearest tool.
- [ ] `embed_serialized_schema` — serialized-schema embedding, nearest tool.
- [ ] `cross_encoder` — trained cross-encoder pairwise scoring with
      `BAAI/bge-reranker-v2-m3`, launched through the isolated research venv.

Checklist:

- [ ] Record which backend actually ran for each arm (real model vs. fallback),
      per arm, in the results file. `dense_retriever.py` already models this
      honest-backend-reporting pattern — reuse it.
- [ ] Each arm produces a prediction for **every** graded case. No silent skips.
- [ ] Held-out cases are **not** run in this phase.
- [ ] Runs are reproducible: rerunning an offline arm produces identical output.
      Prove it for at least one arm.
- [ ] If a chosen model cannot be downloaded or loaded, that is a recorded
      blocker for that arm — not a reason to substitute a weaker one silently.

**Commit:**

    feat(gate-07): lexical, embedding and cross-encoder Gate-0 baselines

---

## Phase 7.5 — LLM baselines under research mode

Covers the LLM half of source-pack Phase 7.2. **Sequential only — never
parallel.** All arms share one Groq rate-limit ledger; concurrent processes
corrupt that accounting and fabricate 429s.

Arms required, differing only by information rights:

- [ ] `llm_new_schema_only` — new contracts only.
- [ ] `llm_old_new_direct` — old + new contracts.
- [ ] `llm_old_new_history` — old + new contracts + verified old traces.
- [ ] `llm_reasoning` — reasoning-style prompt, same rights as `llm_old_new_direct`.

Run each across at least two pinned models where quota permits (a strong tier and
a mid tier). Each model is its own `arm_id`.

Checklist:

- [ ] `mode="research"` on every call. Assert it in the runner, do not assume it.
- [ ] Budget estimated **before** the run and recorded: cases × arms × models =
      total calls, with a projected token cost. Report the estimate to the user
      before starting if it exceeds what the frozen protocol anticipated.

**Pre-registered rate-limit budget table — complete before the Phase 7.2
freeze and before any live call.** Values must come from the frozen manifest,
the pinned model/prompt configuration, and non-secret router/provider limits;
never read or record key values.

| Budget line | Value to freeze | Calculation / guard |
|---|---:|---|
| Graded cases (`N`) | exact integer | Frozen Phase 7.2 manifest; held-out cases excluded. |
| LLM arms (`A`) | `4` | `N × A × M` base calls; all arms run sequentially. |
| Pinned models (`M`) | exact integer and model IDs | At least two where quota permits; no silent substitution. |
| Base calls | exact integer | `N × A × M`. |
| Retry budget (`R`) | exact integer | Maximum attempts are `base calls × (R + 1)`; no post-freeze increase. |
| Input-token budget | per arm/model + total | Sum of frozen prompt estimates; record actual usage separately. |
| Output-token budget | per arm/model + total | Frozen `max_tokens`/completion estimate; record actual usage separately. |
| Per-key ceilings | configured RPM/TPM/RPD/TPD | Use the existing authorized key pool and client cooldown/backoff; no new keys or accounts. |
| Pool/org ceilings | configured RPM/TPM/RPD/TPD | Planned demand must remain below every applicable ceiling with the declared safety reserve. |
| Request timeout | exact seconds | Frozen per-call timeout; timeout is a typed provider failure, never a wrong answer. |
| Ledger identity | path + checksum | Record the `ROUTER_STATE_DB`/`REQUEST_LEDGER` location and schema; one runner process owns it. |

Do not start the run if any ceiling, reserve, token estimate, retry value, or
ledger identity is blank/unknown. Stop before the next request when the
ledger reaches a ceiling or the declared reserve; report the resulting typed
provider failures separately from accuracy. A quota stop is not permission to
change the manifest, add a key source, or rerun completed cases.
- [ ] Checkpoint/resume: a crash or a quota stop must not lose completed cases
      and must not silently re-run them into a different result.
- [ ] Response caching keyed by (`arm_id`, `model`, `prompt_id`, `case_id`) so a
      resume is free and a rerun is verifiable.
- [ ] Typed failures counted separately by kind (`rate_limited`, `timeout`,
      `auth_failure`, `network_failure`, `provider_error`). These are **never**
      wrong answers.
- [ ] Retry policy exactly as frozen in Phase 7.2. If a case still fails after
      the frozen retry budget, it is excluded by the pre-registered rule and
      reported in a separate failure table with its count.
- [ ] Malformed model output (unparseable mapping) is its own outcome class,
      distinct from both provider failure and wrong answer. Record the parse
      failure rate per arm.
- [ ] Local Ollama arms: `qwen3:8b` measured at ~100–110 s per full prompt on
      this machine (`RISK-0015`). A full 150–300 case sweep is therefore
      multi-hour per arm. Either scope local models to a **bounded pre-registered
      subset** or exclude them, and say which — do not start an unbounded sweep.
- [ ] Held-out cases are **not** run in this phase.

**Commit:**

    feat(gate-07): research-mode LLM baseline runner with typed failure accounting

---

## Phase 7.6 — Metrics and stratified analysis

Covers source-pack Phase 7.3.

Checklist:

- [ ] Implement every frozen metric exactly as defined in Phase 7.2:
      Tool Alignment@1, Tool Alignment@k, Argument Mapping Precision/Recall/F1,
      False Alignment Rate, No-Equivalent Accuracy, First-Attempt Task Success.
- [ ] **First-attempt success** is measured by actually executing the predicted
      adapted call against a fresh sandbox and classifying the real outcome —
      reuse the `evaluate_adapted_call` approach from Gate 06
      (`succeeded` / `precondition_failed` / `malformed_call` / `wrong_tool`).
      It is not inferred from mapping correctness.
- [ ] Report every metric **stratified by drift family**, not only in aggregate.
      An aggregate number hides exactly the failure region the gate exists to find.
- [ ] Report uncertainty: bootstrap confidence intervals (or an equivalent stated
      method) per family. A 12-case family with a wide CI is not a failure region.
- [ ] Provider-failure and parse-failure counts reported alongside every accuracy
      number, never folded into it.
- [ ] Produce the **failure-region table**: for each family × arm, the score and
      whether it survives *all* baselines. The GO question is whether a region
      survives the strongest arm, not the average arm.
- [ ] Ablation actually required by the kill criteria: `llm_old_new_history` vs.
      `llm_old_new_direct`. If removing verified old traces does not hurt, the
      "transfer previously verified behavior" story is weak
      (`07_RISKS_AND_KILL_CRITERIA.md` §2). Report this delta explicitly with its
      CI — it is a headline number, not an appendix.
- [ ] All metric code is unit-tested against hand-computed fixtures. A metric bug
      here silently decides the gate.
- [ ] Write `gates/baselines/GATE_07_METRICS.json` with all raw numbers.

**Commit:**

    feat(gate-07): stratified Gate-0 metrics with uncertainty and history ablation

---

## Phase 7.7 — Ambiguity audit

Required by the source acceptance checklist ("Ambiguous cases audited") and by
`07_RISKS_AND_KILL_CRITERIA.md` §4. Its purpose is to test whether the apparent
"hard region" is real difficulty or annotation noise.

Checklist:

- [ ] Draw a **stratified sample** across families, weighted toward cases where
      strong arms disagree with each other or with the oracle. Record the exact
      sampling rule and its seed.
- [ ] **AGY-3** annotates the sample blind — no oracle, no family label, no arm
      predictions. Only the public task.
- [ ] Compute the disagreement rate between the blind annotation and the oracle.
      A high rate on a "hard" family means that family is ambiguous, not hard —
      and a GO built on it is invalid.
- [ ] Manually inspect every case where the blind annotator and the oracle
      disagree. For each: is the oracle wrong, is the case genuinely ambiguous,
      or did the annotator err? Record the adjudication per case.
- [ ] If the oracle is wrong for a case, **do not silently fix it after seeing
      results.** Record the error, quantify its effect, and report the corrected
      and uncorrected numbers side by side. Post-hoc oracle repair that only ever
      moves results in the favorable direction is a protocol violation.
- [ ] Record the ambiguity rate per family. Any family above the threshold frozen
      in Phase 7.2 cannot support a GO on its own.

**Commit:**

    docs(gate-07): stratified ambiguity audit and oracle adjudication record

---

## Phase 7.8 — Decision, result, and STOP

Covers source-pack Phase 7.4.

Apply the thresholds frozen in Phase 7.2 — as written, not as reinterpreted
after seeing numbers. Allowed decisions are exactly `GO`, `REFORMULATE`, `STOP`.

`GO` requires **all** of:

- [ ] A stable, practically meaningful failure region that survives the strongest
      trivial and LLM baselines.
- [ ] That region is not mostly annotation ambiguity (Phase 7.7 evidence).
- [ ] It maps to downstream **first-attempt** failure, measured by real execution.
- [ ] It plausibly benefits from information or mechanism not already given to
      the baselines — state which, concretely.

`REFORMULATE` triggers include: direct alignment saturates but no-equivalent or
uncertainty handling remains hard; only split/merge drift remains; history helps
only under a narrower condition.

`STOP` triggers include: strong direct LLM mapping effectively saturates
realistic cases; hard cases are mostly artificial; history provides no useful
signal; errors are generic planning/state failures rather than correspondence
failures.

Write `gates/results/GATE_07_RESULT.md` in the established gate format:

    Status: GO | REFORMULATE | STOP | BLOCKED
    Entry-gate verification
    Commit / tree state
    Protocol freeze (checksums, when frozen, at which commit)
    Dataset summary (counts, family balance, held-out)
    Baseline arms and information rights
    Commands / runs executed
    Results (stratified tables + uncertainty)
    History ablation
    Ambiguity audit
    Provider-failure accounting
    Decision with quantitative evidence
    Known limitations
    Acceptance checklist
    Next allowed Gate
    STOP: No next-Gate work performed.

Source acceptance checklist — reproduce it and tick each with its evidence:

- [ ] Protocol frozen before headline run.
- [ ] Dataset checksum recorded.
- [ ] Baseline prompts versioned.
- [ ] Research fallback disabled.
- [ ] Raw outputs retained.
- [ ] Ambiguous cases audited.
- [ ] Decision written with quantitative evidence.
- [ ] `GATE_07_RESULT.md` written.
- [ ] No paper prose written.

Also required:

- [ ] State plainly which of the claims in `07_RISKS_AND_KILL_CRITERIA.md` §11
      (claims blacklist) the evidence does **not** support. Do not claim novelty
      over ToolEVO, ContDa, or MCPEvol-Bench.
- [ ] If the decision is `STOP` or `REFORMULATE`, say so directly and completely.
      That is a successful gate. Do not soften it, do not add a "but with more
      work" escape hatch, and do not propose Gate 08.
- [ ] Gate 08 is allowed **only** on an explicit `GO`. On `REFORMULATE`/`STOP`
      the next step is a newly approved research plan, not Gate 08.

**AGY-4** runs here (result-consistency audit) before the final commit.

**Commit:**

    docs(gate-07): record scientific Gate-0 decision and evidence

---

## Ops records — required writes

These are working memory, not paperwork. Update them **during** the work.

| File | When | What |
|---|---|---|
| `_agent_ops/CURRENT_TASK.md` | continuously | Files touched, commands, failures, dead ends with evidence, next concrete step. Overwrite; never append. |
| `_agent_ops/IMPLEMENTATION_LOG.md` | each phase | Append one entry per phase: what was built, commands run, real counts, what failed and why. |
| `_agent_ops/DECISION_LOG.md` | 7.0, and any real fork | `DEC-00NN` for the dependency decision, the evaluator-refactor path taken, D9/D10 metric shape, and any exclusion rule. |
| `_agent_ops/RISK_REGISTER.md` | as found | New `RISK-00NN` for anything discovered (quota ceilings, ambiguity rates, oracle errors). `RISK-0015` (Ollama latency) is already open and relevant to Phase 7.5. |
| `_agent_ops/SESSION_BRIEF.md` | 7.0 and 7.8 | Current state + `Last Verified Commit`. Correct the stale `fed31c3` reference. |
| `_agent_ops/PROJECT_CONTEXT_CARD.md` | 7.8 | A Gate 07 section matching the Gate 05/06 sections' depth. |
| `_agent_ops/REPO_MAP.md` + `code_index.json` | 7.1 and 7.8 | Regenerate — `research/gate07/` is a large new surface. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07.md` | 7.8 | Status line updated to the real outcome. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/README.md` | 7.8 | Gate table row 07 updated. |
| `_agent_ops/PHASE_ROADMAP.md` | 7.8 | Row 07 status. Note its "Program State" header is stale (`PRE-GATE`) — correct it. |

Regenerate the map and index with:

    .venv\Scripts\python.exe _agent_ops\tools\build_code_index.py --root . --output _agent_ops\code_index.json --force
    .venv\Scripts\python.exe _agent_ops\tools\generate_repo_map.py --root . --output _agent_ops\REPO_MAP.md --force

Print the **Closure Receipt** from `_agent_ops/SESSION_PROTOCOL.md` before the
final report. Every row resolves to *updated, with what* or *not needed, with
why*. Silently omitting a row is a protocol violation.

---

## Per-phase commit discipline

For every phase:

1. Run the relevant tests; run the full suite before any commit.
2. `git status --short` and `git diff --check` before staging.
3. Stage **explicit filenames only**. Never `git add .`. Never stage the
   pre-existing overlay.
4. Inspect `git diff --cached --name-only` and the staged diff before committing.
5. Commit with the message given in the phase.
6. `git status --short` after the commit.
7. Do **not** push. Pushing needs separate explicit authorization.

If a phase does not pass, do not commit it. Record the failure in
`CURRENT_TASK.md` and the implementation log, and report it.

---

## Final response format

Return a compact handoff:

1. Gate 07 decision (`GO` / `REFORMULATE` / `STOP` / `BLOCKED`) and the
   quantitative reason.
2. Commit ids and the exact files in each.
3. Protocol freeze: checksum, freeze commit, and proof it preceded the headline run.
4. Dataset: final counts and family balance.
5. Headline results table, stratified by family, with uncertainty.
6. History ablation delta and what it implies about the research claim.
7. Ambiguity rate and any oracle corrections, with before/after numbers.
8. Provider-failure accounting, separate from accuracy.
9. Every unchecked acceptance item with its evidence.
10. Closure Receipt.
11. The only next allowed action.

Do not claim a decision based on a helper's report, a historical result, setup
completion, or a partial run. STOP after the handoff.
