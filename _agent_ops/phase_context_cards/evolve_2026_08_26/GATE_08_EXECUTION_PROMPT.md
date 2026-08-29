# Gate 08 Execution Prompt — Cross-Version Alignment Method

> **Authorization:** Gate 07 closed on 2026-08-29 with a **narrow V4.1 GO** for
> `argument_split` and `tool_replacement` only. `GATE_07_RESULT.md` states the
> only allowed next step is "a separately approved follow-on research plan".
> This prompt **is** that approval, and it is bounded by the narrow GO.
> It is not permission to start Gate 09.

Working directory:

    D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps

Repository interpreter: `.venv\Scripts\python.exe`
Research-baseline interpreter: `external_tools\research_baselines\.venv\Scripts\python.exe`

The two interpreters remain a hard contamination boundary. Gate 08 needs only
the repository interpreter, because it re-uses Gate 07's frozen offline results
instead of recomputing embeddings.

---

## Mission

Implement **one** principal cross-version alignment mechanism, justified by the
Gate-0 failure that Gate 07 actually measured, then evaluate it against the
frozen Gate 07 baselines with the required ablations. End immediately after
`gates/results/GATE_08_RESULT.md`.

## Frozen scope — decided before any Gate 08 number exists

| Set | Cases | Role |
|---|---|---|
| graded `argument_split` | 15 | primary claim |
| graded `tool_replacement` | 15 | primary claim |
| graded `no_equivalent` | 15 | abstention / false-alignment safety control |
| held-out, all 12 families | 36 | calibration only, never scored as a result |

Rationale: Gate 07's GO is narrow. Evaluating the new method on families whose
failure region was never established would manufacture a claim the gate did not
earn. The surface is frozen in `GATE_08_PROTOCOL.json` **before** the run, so it
is a pre-registration, not a post-hoc selection.

## Non-negotiable boundaries

- Run Gate 08 and nothing after it.
- **Preserve Gate-0 and Gate 07 exactly.** Do not modify `research/gate0/`,
  `research/gate07/dataset/`, `research/gate07/oracle/`,
  `research/gate07/sandbox/`, or any `gates/baselines/GATE_07_*.json`. Gate 08
  code lives under `research/gate08/`. Read-only reuse of Gate 07 scoring,
  execution, harness, ledger, and artifact writers is required, not optional.
- **Do not re-run Gate 07 baselines.** They are frozen evidence. The
  `direct frontier-LLM mapper` ablation is satisfied by the existing V4.1
  `llm_old_new_history` rows; say so explicitly rather than re-spending.
- **Information rights must be identical across fair comparisons.** Every arm
  declares its rights through the existing `project_task` mechanism. A method
  arm that reads a field it did not declare is a protocol violation.
- **No hidden migration ground truth.** `research/gate08/method/` must never
  import `research.gate07.oracle`. A test enforces this.
- **No pre-first-call trial and error.** Phase 8.6 executes exactly once per
  case, after the pre-execution decision is already recorded.
- **No moving test cases into calibration after a failure.** The calibration
  split is the held-out manifest, fixed in Phase 8.0.
- **No product-specific heuristics.** Nothing keyed to a case id, a family
  name, or a specific tool name may enter the method.
- Provider failures are their own outcome class. They never become wrong
  answers.
- `ProviderRouter(mode="research")` only. No Ollama fallback.
- Do not read, print, or commit secret values.
- Do not `git add .`, reset, stash, amend, rebase, or force-push. Stage explicit
  filenames. Never stage the pre-existing dirty overlay.
- Do not push.
- No paper prose, abstract, related work, or arXiv-shaped text.
- Ordinary descriptive commit messages. No AI branding or co-author trailers.

## Cost control

Hard cap `$1.20`, enforced in code by the same reserve/settle budget Gate 07
used. Pinned models: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`. Expected spend
is well under `$0.40`; the cap is a stop, not a target. Abort and checkpoint on
cap or daily quota rather than degrading the protocol.

---

## Phase 8.0 — Preflight and freeze

Do:

1. `.venv\Scripts\python.exe _agent_ops\tools\session_start.py --root .`
2. Confirm the live Gate 07 dataset digests still match the frozen V4 protocol
   via `preflight_headline_run`. A mismatch stops the gate.
3. Build `gates/baselines/GATE_08_PROTOCOL.json`: method interface digest,
   arm/ablation list with explicit information rights, evaluation surface,
   calibration split, metric definitions, thresholds, model pins, cost cap,
   and `git_head_at_freeze`.
4. Commit the protocol **before** any method run.

Checklist:

- [ ] `session_start.py` run and read.
- [ ] Gate 07 dataset digests re-verified live.
- [ ] `GATE_08_PROTOCOL.json` written with a method-interface digest.
- [ ] Protocol committed; commit sha recorded.
- [ ] Gate 08 preflight passes against the committed protocol.

## Phase 8.1 — Intent signature

Extract, from the old contract plus verified old traces, a structured signature:
`operation`, `primary_entity`, `target_entity`, `preconditions`, `effects`,
`required_semantics` (per old argument: semantic role plus observed value
shape), `output_semantics`.

One LLM call per case per variant, temperature 0, strict JSON, parsed by an
explicit validator. A parse failure is a typed outcome, never a guess.

Checklist:

- [ ] `IntentSignature` dataclass frozen and digested.
- [ ] Validator rejects malformed or out-of-vocabulary signatures.
- [ ] Signature never contains a candidate tool name it was not shown.
- [ ] Raw request/response retained append-only.

## Phase 8.2 — Candidate retrieval

Score every public candidate against the signature. Retrieval must be able to
return an empty or low-scoring set; it must never force a match.

Checklist:

- [ ] Ranked candidates with numeric scores retained for every case.
- [ ] Empty/low-confidence retrieval is representable and observed.
- [ ] No positional information used.

## Phase 8.3 — Correspondence scoring

Estimate equivalence per candidate on named dimensions: operation, entity,
effect kind, precondition compatibility, output-semantics coverage.
Deterministic given the signature.

Checklist:

- [ ] Per-dimension sub-scores retained, not only a total.
- [ ] Deterministic: the same signature yields the same score.

## Phase 8.4 — Argument alignment

Map old arguments onto new required fields using semantic roles and the value
shapes observed in verified traces. Emit an explicit `value_transform`
(`identity` / `split` / `join` / `literal`) compatible with Gate 07's executor.
Report new-only required fields that no old argument covers.

Checklist:

- [ ] Split evidence comes from an observed trace value, not from a family label.
- [ ] Missing/new required semantics reported per case.
- [ ] Emitted mapping validates against the Gate 07 V4 prediction contract.

## Phase 8.5 — Confidence and abstention

Combine correspondence and alignment completeness into a calibrated confidence.
Emit exactly one of `ALIGN`, `NO_EQUIVALENT`, `ABSTAIN`. Thresholds are fitted
**only** on the 36 held-out calibration cases and frozen before scoring.

Checklist:

- [ ] Thresholds fitted on held-out only; fitted values recorded in the result.
- [ ] All three verdicts reachable and observed.
- [ ] `NO_EQUIVALENT` supported end to end.

## Phase 8.6 — First adapted execution

Execute once per case through Gate 07's `evaluate_first_attempt`, after the
pre-execution decision is recorded. First-attempt success is reported as its own
metric, separate from mapping quality.

Checklist:

- [ ] Exactly one execution attempt per case.
- [ ] Decision recorded before execution.
- [ ] First-attempt metric reported separately.

## Phase 8.7 — Required ablations

All six, each runnable by flag:

| Ablation | How |
|---|---|
| no history | signature built without verified traces |
| schema only | new contracts and task description only |
| no intent abstraction | raw contracts/traces into 8.2-8.4, no signature |
| no preconditions/effects | signature with those fields removed |
| no calibration | forced `ALIGN`, abstention disabled |
| direct frontier-LLM mapper | frozen Gate 07 V4.1 `llm_old_new_history` rows |

Checklist:

- [ ] Six ablations runnable and run.
- [ ] Each ablation's information rights declared and enforced.
- [ ] The reused ablation is labelled as reused, not re-collected.

## Phase 8.8 — Metrics and result

Reuse Gate 07 scoring and intervals. Report per family: Tool Alignment@1,
Argument Mapping F1, False Alignment Rate, No-Equivalent Accuracy, abstention
rate, first-attempt success, each with `n` and a 95% interval, against the
frozen Gate 07 strongest baseline for the same family.

Checklist:

- [ ] Method interface frozen.
- [ ] Information rights documented.
- [ ] No-equivalent supported.
- [ ] Calibration/abstention implemented.
- [ ] Required ablations runnable.
- [ ] First-attempt metric separate.
- [ ] Raw decisions/traces retained.
- [ ] `GATE_08_RESULT.md` written.
- [ ] Result states plainly whether the method beat the frozen baseline, and by
      how much, including when it did not.

## Honesty rules

- A negative Gate 08 is a valid Gate 08. Do not tune until the method wins.
- Never claim a test passed without running it and reading the output.
- Separate fact, inference, and blocker in the result.
- If the method underperforms the frozen baseline, report that as the headline.

## Exit

Write `gates/results/GATE_08_RESULT.md`, update the `_agent_ops/` records
required by `SESSION_PROTOCOL.md`, print the Closure Receipt, and STOP.
