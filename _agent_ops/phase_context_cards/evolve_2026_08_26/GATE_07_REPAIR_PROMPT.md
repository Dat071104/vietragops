# Gate 07 Repair and Re-Run Prompt

> **Current status (2026-08-29):** This repair prompt has been executed and is
> superseded by V4.1. The authoritative result is
> `gates/results/GATE_07_RESULT.md` with narrow GO regions
> `argument_split` and `tool_replacement`; do not rerun this prompt or infer
> current status from its historical `d9045ca`/`BLOCKED` text. Gate 08 remains
> forbidden.

Copy everything below into one Codex (Luna 5.6 Max) session.

This supersedes the Phase 7.1–7.8 execution order in
`GATE_07_EXECUTION_PROMPT.md` for the repair run. All of that prompt's
**Non-negotiable boundaries**, **Start-up and evidence rules**, **Gate 06 is
frozen**, **Team use and subagents**, **Ops records**, and **Per-phase commit
discipline** sections still apply verbatim. Read it first.

Working directory: `D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps`
Interpreter: `.venv\Scripts\python.exe`
HEAD at prompt creation: `d9045ca` (Gate 07 BLOCKED). Re-verify; do not assume.

---

## What actually broke — three confirmed bugs

The BLOCKED result blamed the freeze-order violation. That is real but it is the
**third** bug in a chain, not the cause. Independent verification of the
committed tree at `d9045ca` found the following. Reproduce each yourself before
fixing it; do not take this section on trust.

### Bug A — fail-open seed sanitization (root cause, STILL PRESENT in v2)

`research/gate07/dataset/operators.py:93`:

```python
return f"synthetic-{name}-{seed}"
```

`_field_value` special-cases known field names, then **falls through to a
default that prints the raw generator seed**. `session_date` is handled;
`session_day` is not, so it falls through. A second, independent channel renders
the seed into task *description prose* for `multiple_old_to_one_new` cases:
`"...task represented by these operations for the synthetic record 20350827."`

Measured on the **current committed v2 dataset**:

| Split | Leaking cases | Families affected |
|---|---|---|
| Graded | **20 / 180** | `multiple_old_to_one_new` (15), `multiple_simultaneous_renames` (5) |
| Held-out | **4 / 36** | `multiple_old_to_one_new` (3), `multiple_simultaneous_renames` (1) |

Why this is severe, not cosmetic — the seed is invertible:

```python
seed = GENERATOR_SEED + family_index * 10000 + (variant + 100*held_out) * 101 + lineage_index
# therefore:  (seed - 20260827) // 10000  ==  family_index
```

Verified: family index 11 → seed `20370827` → recovers `11` exactly. So the
leaked text hands a baseline the **drift family label**, the single most
valuable hidden label in the experiment.

Why the v2 audit missed it: the audit searched for the literal base constant
`20260827` and for field *names*. Every leaked value is a *derived* seed
(`20280929`, `20350827`, …) which never contains the base string. **The audit
searched for the wrong token.** So the v2 amendment — the very change that
caused the freeze-order violation — did not even fix the problem it was made for.

### Bug B — freeze order is prose, not a machine guard (proximate cause)

`research/gate07/protocol/freeze.py:97`:

```python
def build_protocol(cases, git_head: str, model_ids, ...)
```

`git_head` is a **caller-supplied string**. Nothing verifies it is a real
revision, that the working tree is clean, or that the protocol file is
committed. Grepping `runner/llm.py`, `runner/artifacts.py`, and
`baselines/offline_runner.py` for git/dirty/uncommitted state checks returns
**zero hits**.

So "the freeze commit must precede every headline run" existed only as prose in
the execution prompt, enforced by the agent remembering it. When Bug A forced a
mid-flight v2 amendment, nothing mechanically stopped the run from starting.

### Bug C — the anti-leak test checks the wrong surface

`tests/test_gate07_oracle_boundary.py:42`:

```python
assert not {field.name for field in fields(task)} & {"family", "seed", "lineage_key"}
```

This asserts the task dataclass has no *attribute* named `family`/`seed`/
`lineage_key`. It never inspects **values**. The leak is textual — inside string
values and description prose — so this test passes green while 24 cases leak.

This one traces to the original execution prompt, which told you to "extend the
Gate 06 oracle-boundary test style (static AST scan + runtime introspection)".
That was correct for Gate 06, whose leak risk was a structural `tool_id`
attribute. It is the wrong surface for Gate 07, whose leak risk is textual. Fix
the test, and treat that prompt instruction as superseded by this document.

---

## Repair boundaries

- The v2 results stay **DISQUALIFIED**. Do not rehabilitate them, do not merge
  them into new numbers, do not cite them as evidence. They remain as audit
  artifacts only.
- Do not delete `gates/results/GATE_07_RESULT.md`. The BLOCKED record is honest
  history. It gets superseded by a new result, not erased.
- Do not touch `research/gate0/` (Gate 06 frozen evidence).
- Everything in Phases R4–R10 is a fresh v3 lineage. No v2 artifact feeds it.
- Gate 08 remains forbidden regardless of outcome.

---

## Phase R0 — Entry gate

- [ ] `git rev-parse HEAD`, branch, `git status --short`, `git diff --check`,
      `git diff --cached --name-only` recorded. The 21-entry pre-existing
      overlay stays untouched and unstaged.
- [ ] Full suite baseline: `.venv\Scripts\python.exe -m pytest -q` with
      `PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock`. Record exact counts.
- [ ] **Reproduce Bug A yourself.** Serialize all graded + held-out public tasks
      and scan for every value in `{r.seed for r in case_requests()}`. Confirm
      the 20/180 and 4/36 figures, or report what you actually measured.
- [ ] **Reproduce Bug B yourself.** Confirm no runner performs any git-state
      check before a headline run.
- [ ] **Reproduce Bug C yourself.** Confirm the boundary test passes green on
      the leaking dataset.
- [ ] Record the v2 LLM budget already consumed (1,440 records claimed) from
      `gates/artifacts/gate07/` ledgers. This constrains Phase R7.

No commit. Report `REPAIR_ENTRY_PASS` or `REPAIR_BLOCKED`.

---

## Phase R1 — Fix Bug A: fail-closed sanitization + non-invertible seed

Two independent fixes. Do both; either alone is insufficient.

**R1a — make the renderer fail closed.**

- [ ] `_field_value` must never fall through to a seed-bearing default. Replace
      the fallback with an explicit `raise` on an unrecognized field name, so a
      new field is a loud test failure instead of a silent leak.
- [ ] Enumerate every field name reachable from every lineage and give each one
      an explicit deterministic renderer. Prove the enumeration is complete by a
      test that walks all lineages and asserts no field raises.
- [ ] Remove the seed from all description/prose builders. Grep the whole
      `research/gate07/` tree for f-strings interpolating a seed into any string
      that can reach a public surface.

**R1b — make the seed non-invertible (defence in depth).**

- [ ] Replace the arithmetic seed with a non-invertible derivation, e.g.
      `int.from_bytes(sha256(f"{family}:{variant}:{lineage}:{held_out}".encode()).digest()[:6], "big")`.
      Keep it fully deterministic and reproducible from the same inputs.
- [ ] After this change, `(seed - BASE) // 10000` must no longer recover
      `family_index`. Add a test asserting no simple arithmetic relation
      survives: seeds sorted by family must not be monotonic or evenly spaced.
- [ ] Rationale: R1a stops today's leak; R1b makes any *future* leak
      non-catastrophic. A leaked opaque integer reveals nothing.

Commit: `fix(gate-07): fail-closed field rendering and non-invertible case seeds`

---

## Phase R2 — Fix Bug C: value-level leak test

- [ ] New test that serializes **every** graded and held-out public task and
      asserts the rendered text contains: no value from the full seed set, no
      family name from the 12-family list, no `tool_id`, no lineage key, no
      operator name, and no `held_out` indicator.
- [ ] It must scan **values and prose**, not attribute names. Assert on the
      serialized JSON string, not on the dataclass.
- [ ] Add a deliberate-leak negative test: inject a seed into one task, assert
      the detector **fails**. A leak test that cannot fail is not a test.
- [ ] Keep the existing attribute-level assertion as well — it is not wrong,
      merely insufficient.

Commit: `test(gate-07): value-level public-surface leak detection`

---

## Phase R3 — Fix Bug B: mechanical freeze-order guard

- [ ] Add a preflight in `research/gate07/protocol/` that a runner **must** call
      before any headline run, which hard-fails unless all hold:
      - the protocol file path exists and is **tracked** in git;
      - `git status --porcelain <protocol_path>` is empty (not dirty, not
        untracked);
      - the recorded `git_head_at_freeze` equals a real revision that is an
        ancestor of current `HEAD`;
      - the live dataset digest recomputes to the frozen digest.
- [ ] `build_protocol` must derive `git_head` itself rather than trusting a
      caller-supplied string, or must validate the string against real git.
- [ ] Wire the preflight into **both** the offline runner and the LLM runner.
      A run that skips it must be impossible, not merely discouraged.
- [ ] Tests: a dirty protocol file blocks the run; an uncommitted protocol file
      blocks the run; a digest mismatch blocks the run; a clean committed
      protocol permits it.

Commit: `feat(gate-07): mechanical freeze-order preflight for headline runs`

---

## Phase R4 — Regenerate dataset v3

- [ ] Regenerate all 216 cases under the fixed renderer and new seed derivation.
      Keep 180 graded / 36 held-out and 15/3 per family across all 12 families.
- [ ] Run the Phase R2 leak test. It must be green on the real dataset.
- [ ] Confirm byte-for-byte regeneration determinism from the same inputs.
- [ ] Re-verify the sandbox is still in-memory only and `state_hash()` reset
      reproducibility still holds.
- [ ] Record new graded / held-out / ground-truth digests.

Commit: `feat(gate-07): regenerate leak-free v3 case dataset`

---

## Phase R5 — Freeze protocol v3 **and commit before anything runs**

This is the phase that failed last time. The order is not negotiable.

- [ ] Write `gates/baselines/GATE_07_PROTOCOL_V3.json` with everything the
      original Phase 7.2 checklist requires, plus the v3 digests from R4.
- [ ] Declare v1 and v2 superseded and disqualified inside the v3 file, with the
      reason. Lineage stays visible.
- [ ] **Commit it. Then run the R3 preflight and show it passes.** Paste the
      preflight output into the implementation log.
- [ ] Only after that commit exists may Phase R6 begin. If you find yourself
      amending the protocol mid-run, **stop the run**, commit the amendment, and
      restart the affected arms from scratch. Never continue on an uncommitted
      amendment — that is exactly what produced BLOCKED.

Commit: `docs(gate-07): freeze v3 protocol, digests and supersession record`

---

## Phase R6 — Re-run offline arms

- [ ] Preflight must pass at run start; record its output alongside results.
- [ ] Five arms: `lexical_name`, `lexical_serialized`, `embed_name_desc`,
      `embed_serialized_schema`, `cross_encoder` (BGE-M3 + BGE reranker via the
      isolated `external_tools/research_baselines/.venv`).
- [ ] Confirm `VietRagOps/.venv` still has no `sentence_transformers` import
      path active, and the retrieval smoke still matches
      `gates/baselines/GATE_04_RETRIEVAL_SMOKE.json` bit-for-bit.
- [ ] Graded cases only. Held-out untouched.

Commit: `feat(gate-07): v3 offline baseline results`

---

## Phase R7 — Re-run LLM arms

- [ ] Preflight passes at run start.
- [ ] Four arms × two models, `ProviderRouter(mode="research")`, single
      sequential process, existing Groq client and key pool.
- [ ] **Budget first.** v2 already spent ~1,440 records. Per-key limits are
      8K TPM / 200K TPD for `gpt-oss-120b`, `gpt-oss-20b`, `qwen3.6-27b`.
      Compute projected tokens before starting and state whether the sweep fits
      inside the remaining daily headroom. If it does not, split across days and
      say so — do not start a sweep you cannot finish.
- [ ] Send only the case's candidate subset, not the whole 39-tool surface, and
      declare that as an information-rights property identical across all arms.
- [ ] Typed failures counted separately; parse failures their own class; neither
      enters accuracy.
- [ ] Checkpoint/resume and cache keyed by
      (`arm_id`, `model`, `prompt_id`, `case_id`).

Commit: `feat(gate-07): v3 research-mode LLM baseline results`

---

## Phase R8 — Metrics

- [ ] All frozen metrics, stratified by all 12 families, with bootstrap CIs.
- [ ] First-attempt success by real sandbox execution, not inferred.
- [ ] `llm_old_new_history` vs `llm_old_new_direct` ablation with CI.
- [ ] Failure-region table: family × arm, survives-all-baselines flag.
- [ ] Write `gates/baselines/GATE_07_METRICS.json`.

Commit: `feat(gate-07): v3 stratified metrics and history ablation`

---

## Phase R9 — Ambiguity audit (AGY unavailable — use the fallback)

The AGY workers were unavailable last run and the audit never happened, which is
an unmet acceptance requirement. Do not let that repeat.

- [ ] Try the AGY blind annotator once. Single lane, read-only, oracle withheld.
- [ ] If unavailable, record `AGY_UNAVAILABLE` and use this fallback: a **local
      blind annotator** — a separate process given only the public task, using a
      pinned local Ollama model, with no oracle in its context, on a stratified
      sample. It is weaker than an independent reviewer; label it as such.
- [ ] Compute disagreement rate vs. oracle. Adjudicate every disagreement:
      oracle wrong / genuinely ambiguous / annotator wrong.
- [ ] Any oracle correction gets before-and-after numbers reported side by side.
      Never a silent post-hoc fix.

Commit: `docs(gate-07): v3 ambiguity audit and adjudication`

---

## Phase R10 — Decision and result

- [ ] Apply the R5-frozen thresholds as written.
- [ ] Write `gates/results/GATE_07_RESULT.md` — supersede the BLOCKED record in
      place, keeping a short lineage section: v1 seed leakage → v2 incomplete
      fix + freeze violation → BLOCKED → v3 repair. Honest history, not erased.
- [ ] Tick the full source acceptance checklist with evidence.
- [ ] State which claims from `07_RISKS_AND_KILL_CRITERIA.md` §11 the evidence
      does not support.
- [ ] `STOP` / `REFORMULATE` are successful outcomes. Do not soften them and do
      not propose Gate 08.

Commit: `docs(gate-07): record v3 scientific Gate-0 decision`

---

## Final handoff

1. Decision and quantitative reason.
2. The three bugs, each with your own reproduction evidence and the fix.
3. Proof the v3 freeze commit preceded every headline run (preflight output).
4. Leak test result on the real v3 dataset.
5. Metrics stratified by family with CIs.
6. History ablation delta.
7. Ambiguity rate, annotator used, any oracle corrections before/after.
8. Provider-failure accounting and budget consumed.
9. Closure Receipt.
10. Only next allowed action.

Do not push. STOP after the handoff.
