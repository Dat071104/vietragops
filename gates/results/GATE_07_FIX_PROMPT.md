# Task prompt for the fixing agent — Gate 07 v3 audit remediation

You are working in the repository `VietRAGOps` (Windows, PowerShell, Python 3.13).
Project root: `d:/Project cua Dat/VietRAGOps/ROOT`. Gate 07 code lives under
`VietRagOps/research/gate07/`, artifacts under `VietRagOps/gates/`.

An independent audit of the Gate 07 v3 result (`gates/results/GATE_07_RESULT.md`,
`Status: GO`) found that the published failure mechanism is **not supported by the
gate's own raw records**. Your job is to remediate the protocol and re-run, not to
defend the existing conclusion.

## Non-negotiable constraints

- **Gate 08 remains forbidden.** Do not open, plan, or reference Gate 08 work.
- Do not touch the pre-existing untracked overlay (`AGENTS.md`, the deleted skill
  scripts, `tests/test_groq_rotation.py`, pre-existing `_agent_ops/` entries).
- Never `git add .` — stage explicit files only. Do not push.
- Never claim a test or a run passed unless it actually ran; paste the output.
- The v3 protocol is frozen (`GATE_07_PROTOCOL_V3.json`, SHA-256
  `c9b27e936be76ee1070db70714d9e75509c1f22d637160138db890bf1cc4b1f9`, freeze commit
  `2721c45`). **Every fix below changes measurement semantics, so it requires a new
  `GATE_07_PROTOCOL_V4.json` freeze plus a fresh headline run.** Do not mutate v3
  artifacts in place; v3 stays on the record as audited-and-superseded.
- Until V4 completes, the Gate 07 verdict must read
  **SUSPENDED — evidence does not support the stated mechanism**, not GO.

## Audit findings you must treat as established (evidence included)

### F1 — The load-bearing 0.000 is an abstention artifact, not an alignment failure

In `gates/artifacts/gate07/v3/llm_results_batch1_corrected.jsonl`, arm
`llm_old_new_direct` / `openai/gpt-oss-120b`, family `argument_split`:
**12 of 13 evaluable responses are `{"abstain": true, "selected_tool_names": [],
"argument_pairs": []}`.** The 13th (`G07-G-0087`) selected a wrong tool.

Because `metrics/scoring.py::score_prediction` sets `predicted_tools = frozenset()`
on abstention, `tool_alignment_at_1` and `argument_f1` are **0.000 by
construction**. Because `metrics/execution.py::evaluate_first_attempt` returns
`malformed_call` with `"no selected tool for an equivalent task"` when `selected`
is empty, `first_attempt_task_success = 0.000` is likewise **abstention, not a bad
argument split**. Confirm this yourself before changing anything.

That one behaviour produces the other near-zero families too — it is a single
finding reported as four:

| arm (gpt-oss-120b)    | argument_split | added_required_field | argument_merge | tool_replacement | no_equivalent |
|-----------------------|----------------|----------------------|----------------|------------------|---------------|
| `llm_new_schema_only` | 3 abstain / 11 select | 1 / 11 | 11 / 1 | 4 / 9 | 14 / 1 |
| `llm_old_new_direct`  | **12 / 1**     | **15 / 0**           | **14 / 1**     | **15 / 0**       | 15 / 0 |
| `llm_old_new_history` | 12 / 2         | 14 / 1               | 15 / 0         | 14 / 0           | 15 / 0 |
| `llm_reasoning`       | 12 / 1         | 15 / 0               | 15 / 0         | 15 / 0           | 15 / 0 |

Root cause is the shared instruction block in
`research/gate07/protocol/prompts.py::COMMON`:

> "Use only the information explicitly included below. Do not assume hidden
> identifiers or a migration guide. You may abstain when no candidate is
> behaviorally equivalent."

For `argument_split`, no public contract states that `subject_area` and
`catalog_number` are the two halves of `course_code`. Splitting `"CRS-026"` into
`"CRS"` + `"026"` **is** assuming a hidden identifier convention. Under a literal
reading of that instruction, abstention is the compliant answer. The gate scores
instruction-compliance as total capability failure.

### F2 — Three independent disconfirmations of the published mechanism

The report states the mechanism is `old course_code -> new subject_area +
catalog_number`. All three of these contradict it:

1. **Less information scores higher.** `llm_new_schema_only` — which never sees the
   old contract, and which the protocol calls the weakest arm — reaches
   `tool_alignment_at_1 = 0.786` on `argument_split`; `llm_old_new_direct` reaches
   `0.000`. Adding the old contract *causes* the abstention. That is an instruction
   interaction, not a capability limit.
2. **The model demonstrably performs the split.** `llm_old_new_history`, case
   `G07-G-0075`, emits exactly
   `[["get_course_contact","course_code","get_course_contact_parts","subject_area"],
   ["get_course_contact","course_code","get_course_contact_parts","catalog_number"]]`
   — a perfect decomposition, `argument_f1 = 1.0`.
3. **The ambiguity audit points the same way.** Samples `A013`/`A014`/`A015` are
   `argument_split`. The annotator received the *same* payload (old contracts +
   verified traces + new contracts — see `ambiguity_public_sample.json`) and
   selected the correct `*_parts` tool with `abstain: false` on all three. The
   report cites `0/3` disagreement as *support* for GO; it is in fact evidence that
   the task is unambiguous and that the graded abstention is a prompt artifact.

### F3 — Positional answer key in the candidate list (a leak class Bug A and Bug C never covered)

`research/gate07/dataset/operators.py::_candidate_names` returns
`tuple(correct + pool[...])` — the correct tool names are prepended and never
shuffled into the pool. Verified: **198 of 198 answerable cases place the correct
tool(s) in the leading slot(s) of `candidate_new_tool_names`**, and that list is
rendered verbatim into every prompt and handed to every offline arm.

Consequences:

- `tool_alignment_at_3` / `tool_alignment_at_5` are **1.000 for every arm on every
  family by construction** — they read 1.000 on `argument_split` where the model
  abstained. They measure candidate ordering, not the model.
  (`baselines/llm.py` builds `ranked = selected + remaining candidates in order`.)
- A trivial "always select `candidate[0]`" arm would score
  `tool_alignment_at_1 = 1.000` on all 11 answerable families. It was never run.
  Its absence undermines the gate's central "no baseline solves this" framing.
- Every offline arm's Tool@1 is contaminated by order-preserving tie-breaks.

Bug A and Bug C covered serialized values and prose leakage. **Ordering leakage was
never tested for.**

### F4 — First-attempt success cannot observe an argument-split error

`metrics/execution.py::_adapt_input` hard-codes the very transformations these
families are supposed to test:

```python
if field in {"subject_area", "catalog_number"} and "-" in str(candidates[0]):
    pieces = str(candidates[0]).split("-", 1)
    result[field] = pieces[0] if field == "subject_area" else pieces[1]
elif field in {"section_ref", "section_code", "class_ref"} and len(candidates) >= 2:
    ...  # performs the merge on the model's behalf
```

The harness performs the split and the merge for the model; the model only has to
*name* the pair. So "it causes real first-attempt execution failure" is
unsupported: the 12 failures are `malformed_call` from abstention, and a selecting
model would have had its split done for it. A wrong split is currently
unobservable.

### F5 — Every boundary confidence interval is degenerate

`metrics/scoring.py::_summary` bootstraps by resampling the observed vector. An
all-zero vector can only resample to zero, so `0.000 [0.000, 0.000]` is
arithmetically guaranteed rather than evidential; the same holds for
`1.000 [1.000, 1.000]` and the `lexical 1.000` cells. The GO rule in
`decision_thresholds.stable_failure_region` requires "bootstrap 95% upper bound
still below the saturation bar" — a condition that **cannot fail** whenever the
mean is 0.000. At 0/13, a Wilson upper bound is near 0.23 and Clopper–Pearson near
0.25.

### F6 — Non-random missingness concentrated in the load-bearing family

`argument_split` carries 10 `provider_error` records — roughly 2.5x every other
family, most of which have about 4 — and the headline arm reports `n=13` of 15.
Across the run, 233 of 1440 records (16%) were excluded (41 HTTP-400, 176 typed
rate-limit stops, 16 parse failures). No imputation-sensitivity analysis was run on
the headline number.

## What to deliver

Work in this order. Stop and report if any step contradicts a finding above.

**Step 0 — Reproduce the audit.** Independently confirm F1, F3, and F5 from the
committed v3 artifacts and print the actual command output. Do not proceed on
assertion alone.

**Step 1 — Abstention-decoupled protocol (the decisive experiment).**
Change the response contract so that abstention no longer destroys the alignment
signal. Required shape:

```json
{"best_candidate_tool_names": ["..."],
 "argument_mapping": [{"old_tool": "", "old_arg": "", "new_tool": "", "new_arg": ""}],
 "equivalence_verdict": "equivalent | equivalent_under_stated_convention | not_equivalent",
 "confidence": 0.0}
```

- `best_candidate_tool_names` is **always required** and must be non-empty for an
  answerable task; `argument_mapping` is always required alongside it.
- Score `tool_alignment_at_1` and `argument_mapping_f1` on
  `best_candidate_tool_names`.
- Report abstention as a **separate** `abstention_rate` metric, and score
  `no_equivalent_accuracy` off `equivalence_verdict == "not_equivalent"` so the
  `no_equivalent` family stays measurable.
- Reword `COMMON` so that "do not assume hidden identifiers" no longer forbids the
  derivation the task requires. State explicitly that a candidate may require
  deriving an argument value from a value already held, that such a derivation is
  permitted and must be declared, and that `equivalence_verdict` — not silence — is
  where doubt gets recorded.
- Keep the current prompt as a retained arm (`llm_old_new_direct_v3_legacy`) so the
  abstention delta is measured rather than asserted.

Re-run `argument_split`, `added_required_field`, `argument_merge`,
`tool_replacement`, and `no_equivalent` at minimum; prefer all 12 families.

**This step decides the gate.** If `argument_mapping_f1` for `argument_split`
stays below 0.75 under forced selection, the failure region is real and the GO can
be re-earned on honest ground. If it rises, the v3 GO is void and must be retracted
in `GATE_07_RESULT.md` and `DECISION_LOG.md`.

**Step 2 — Close the positional leak.**
Shuffle the correct tools into the candidate pool using a per-case seeded
permutation derived from the existing case seed; record the permutation in the
evaluator-only oracle, never in the public task. Add a test asserting the
correct-tool index distribution is approximately uniform across cases and that no
family concentrates it at index 0. Add a **mandatory `positional_prior` control
arm** (always select `candidate[0]`) plus a random-choice arm to the arm set; the
gate must beat both before any family may be called a failure region.

**Step 3 — Repair or retire the rank metrics.**
`tool_alignment_at_3` / `at_5` currently measure candidate order. Either require
the model to emit a genuine `ranked_tool_names` and score that, or delete both
metrics from the protocol and the report. Do not leave them published as they are.

**Step 4 — Correct the interval estimator.**
Use Wilson (default) or Clopper–Pearson intervals for proportion-valued metrics.
Keep the bootstrap only for genuinely continuous per-case scores, and make
`_summary` refuse to emit a zero-width interval — a degenerate vector must surface
as degenerate. Restate `decision_thresholds` against the new estimator and recheck
whether the GO rule still discriminates.

**Step 5 — Make first-attempt measure what it claims.**
Move the derivation out of `_adapt_input`: the prediction must supply the value
transform (an explicit `value_transform` per mapped argument, or the literal
constructed argument values), and the harness must execute what the model actually
supplied. Add a negative test proving a wrong split is now scored as a failure — it
cannot be today. If you decline this step, delete every first-attempt claim about
argument-split from the result document.

**Step 6 — Baseline definition and missingness.**

- Redefine "strongest baseline" empirically: the max over arms per family per
  metric, not fixed a priori by information rights.
- Exclude structurally incapable arms from a metric instead of counting their 0.000
  as a baseline failure. `llm_new_schema_only` never sees old tool or argument
  names, so it *cannot* emit a correct `argument_mapping` pair; its 0.000 Arg F1 is
  not evidence about the task.
- Recompute the headline under best-case and worst-case imputation of the excluded
  records, and publish the range.
- Investigate why `argument_split` draws about 2.5x the HTTP-400s — start with
  prompt token length per family — and report whether the drops are
  content-correlated.

## Output contract

1. Step 0 reproduction evidence (actual command output).
2. Root-cause classification per finding: real bug / measurement artifact /
   expected behaviour, with the evidence for each.
3. For Step 1, the new response contract and prompt design **before** you run
   anything, plus a token and cost estimate for the re-run — wait for approval
   before spending provider budget.
4. `GATE_07_PROTOCOL_V4.json` with a fresh freeze-ledger entry; v3 untouched.
5. Updated `GATE_07_RESULT.md` recording v3 as superseded, with the corrected
   verdict and the abstention delta stated numerically.
6. New and updated tests: ordering-leak test, degenerate-interval test,
   wrong-split negative test, abstention-decoupling test.
7. Full test suite output (the v3 baseline was 481 passed, 2 warnings, 0 failed).
8. `DECISION_LOG.md` entries for the suspension/retraction and for the V4 protocol.
9. `IMPLEMENTATION_LOG.md` phase evidence, and a Closure Receipt with one line per
   memory file.

## Conclusions you must not draw

- Do not conclude "the model cannot split arguments." The raw records contain a
  perfect split (`G07-G-0075`, history arm) and three independent annotators who
  did it without hesitation.
- Do not repair the numbers by re-scoring v3 predictions under new rules. Those
  predictions were produced under the old instruction; they must be re-collected.
- Do not treat a lower score under a fixed prompt as a capability finding until the
  `positional_prior` control and the forced-selection arm have both been run.
