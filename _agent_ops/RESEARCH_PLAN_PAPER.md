# Research Plan — arXiv Paper (Gate 10 track)

**Status:** AUTHORIZED — RE-SCOPED MEASUREMENT PAPER (`DEC-0048`).
**Owner decision:** narrow, research-first paper. VietRAGOps Evolve is the deployed
case study and artifact, not the contribution.
**Recorded:** 2026-09-11.

This file is durable project memory. It records the paper direction the owner
chose, the blocking prerequisites that must be cleared before any result can be
claimed, and the gate sequence that gets there. It supersedes nothing; the thin
`GATE_10.md` phase card still governs the freeze/submission mechanics.

---

## 1. Working title

> **Unreachable Oracles: Ground-Truth Derivability in Synthetic Tool-Drift
> Benchmarks for LLM Agents**

This title is adopted under `DEC-0048`. It names the phenomenon and the
synthetic LLM-agent benchmark scope without claiming an alignment method, a new
benchmark, SOTA, external validation, or generalization beyond the measured
surface. It remains accurate if the reported values move by 10%.

**Superseded 2026-09-11 (`DEC-0048`):** *Pre-Execution Cross-Version Tool
Alignment for LLM Agents under In-Place API Schema Drift.* The title is
superseded because Gate 08 closed RQ3 **NEGATIVE** (`DEC-0023`) and Gate 19-C
cancelled the campaign that could have reopened that alignment claim by power
analysis (`DEC-0047`). The old title is retained here as historical record.

Do **not** use "Invariant Tool-Intent ..." as a title until an ablation shows an
explicit intent representation produces a clear gain. The word *invariant* is a
claim, and it is currently unproven.

## 2. Scientific thesis — one sentence

> Can a declared-information-rights criterion and auditor determine whether
> ground-truth targets in synthetic tool-drift benchmarks for LLM agents are
> derivable, and what measurement and statistical-power consequences follow when
> they are not?

Every section must serve this sentence. The cross-version alignment setting is
the context in which the benchmark defect was found, not the claim of a new
alignment method.

Formally, for declared information rights `I` and an oracle target `g`, define
`Reachable(g | I) = 1` iff the target is derivable from `I`. An item that requires
an absent target field, an unobservable construction convention, or another
unstated value is an unreachable oracle and must be repaired or excluded before
it is used for a capability claim.

## 3. Research questions

| RQ | Question |
|---|---|
| **RQ1 — Criterion** | Can oracle reachability under declared information rights be checked mechanically and independently reproduced? |
| **RQ2 — Measurement** | How often are ground-truth items unreachable across the 12 synthetic drift families, and which mutation families account for the failures? |
| **RQ3 — Control** | Does the same audit find unreachable targets in a hand-verified sample of real MCP/API version pairs? |
| **RQ4 — Validity** | How do repair/exclusion choices change the scoreable sample and its minimum detectable effect, and what does the raw evidence say about the project's prior `::` mechanism claim? |

The earlier alignment-method RQ3 remains a pre-registered **NEGATIVE** result in
Gate 08 (`DEC-0023`). It is disclosed as historical evidence and is not reopened
by this paper.

## 4. Blocking prerequisites — read before planning any experiment

These are facts already established inside this program. They are not opinions
about the topic, and none of them can be worked around by writing carefully.

### 4.1 RQ3 already has a pre-registered NEGATIVE answer

Gate 08 ran the alignment-method experiment and closed **NEGATIVE**; `DEC-0023`
is final. Any new campaign is therefore either (a) a re-run under a repaired
oracle, or (b) a different question. **The prior negative result must be
disclosed in the paper, not quietly superseded.** A pre-registered negative
result with a frozen protocol is an asset — it is evidence the evaluation was not
tuned until it produced a win. Concealing it would be misconduct.

### 4.2 The `tool_replacement` oracle is measurably unreachable (RISK-0021, High/High)

Gate 08 measured that **10 of 35** `tool_replacement` ground-truth argument pairs
name a `new_arg` that is not a field of the new contract any method is shown (for
example `section_ref` in `grant_completion_credential`). Maximum attainable
Argument Mapping recall for that family is **0.7143, not 1.0**. Part of the
failure region Gate 07 identified there is an artifact of its own oracle.
`argument_split` is clean (0/40).

**Consequence:** any first-attempt success number computed on the unrepaired
`tool_replacement` family is invalid and would have to be retracted. Repair or
explicitly exclude the unreachable pairs **before** any baseline campaign.

### 4.3 Five graded cases require an unobservable convention (RISK-0022)

**Superseded historical claim (2026-09-11):** five of 15 graded
`tool_replacement` cases require an argument built by joining two old values with
`::`, and the frozen Gate 07 baselines that "succeeded" there guessed an
unstated convention. The original wording is retained in RISK-0022's history.

**Gate 19-C correction:** the first clause is confirmed, but the mechanism claim
was not. The frozen V4/V4.1 extraction contains 85 effective rows for these five
cases: `0` literal `::` constructions, `3` different-separator constructions,
`82` no-join outputs, and `0` first-attempt successes. Gate 07's family-level
successes therefore occurred on the other cases. Its argument-mapping scorer
compares exact field quadruples, while its first-attempt executor compares the
produced argument dictionary with the frozen expected inputs.

**Consequence:** the audit trail carried an unverified attribution from a
family-level success rate to the hidden cases. Pair-mapping credit must be
reported separately from value construction and first-attempt execution; neither
direction supports a hidden-convention capability claim.

### 4.4 Design-time oracle exposure is on record (RISK-0023)

Ground truth of three graded cases (`G07-G-0073`, `G07-G-0127`, `G07-G-0199`) was
read during Gate 08 method scoping before the held-out discipline was tightened.
Disclose it; do not claim a clean room.

### 4.5 Narrow-claim boundary (RISK-0020)

The `argument_split` first-attempt estimate is below the practical bar but its
Wilson upper bound is `0.9333`, above the `0.90` saturation bar. Keep claims
limited to stable Argument F1 plus an observed execution consequence. Do not
claim stable end-to-end saturation or general model inability.

---

## 5. Positioning against the literature

Verified 2026-09-10 by direct arXiv lookup — these are real papers, not
hallucinated citations:

| Work | What it does | Why it does not close our gap |
|---|---|---|
| **ToolEVO** (ICLR 2025) | Adapts to evolving tools via active interaction, self-reflection, trial-and-error environment feedback | Adapts **by probing**; we forbid probing before the first call |
| **ContDa** (Findings ACL 2026) | Evolving toolsets; relation-guided exploration then documentation update | Also exploration-based; updates docs rather than transferring verified behavior |
| **MCPEvol-Bench** (arXiv 2607.14642, Liu et al., 2026-07-16) | 11 mutation operators over 123 MCP servers; frontier models drop ~13–14 points | Establishes the problem; **do not claim "first benchmark of tool evolution"** |
| **DynamicMCPBench** (arXiv 2607.20531, Kamiński et al., EMNLP 2026) | Trace-grounded, effect-scored, 1,845 tasks, 121 live MCP servers, equivalence sets | Reinforces that **execution effects**, not fixed tool paths, are the right outcome |
| **Reference-free drift benchmark** (IEEE Access 2026) | Schema/policy/toolset drift robustness | Normalizes using a **known bijective drift manifest**; authors state they do not measure autonomous detection + adaptation. **This is the cleanest adjacent gap we occupy.** |
| **Tool Primitives** (arXiv 2609.01736) | Hides raw API schemas behind natural-language wrappers | A reviewer will ask "why not abstract the schema away?" — answer it explicitly |
| **API migration / SE literature** | LLM API mapping, BigBag AST rules, deprecated-API code generation | Source-code migration, not agent-runtime adaptation. Must be cited and distinguished. |

**Honest novelty assessment:** generic "agents must adapt to API drift" is ~4/10
and crowded. The defensible delta is the exact intersection:

```
historical verified trace + new contract + hidden migration
+ no probing + first-attempt execution + NO_EQUIVALENT
```

Distinguish from SE migration on five axes: same deployed capability across
versions (not source→target libraries); structured tool calls (not source code);
first-attempt agent task completion (not compilation); hidden correspondence (not
a known migration setting); and tool + argument + effects + `NO_EQUIVALENT` (not
API→candidate-API ranking). The fifth axis is the one reviewers will find novel.

---

## 6. Additions beyond the base plan

These four are not in the original outline and each is cheap relative to its
value.

### 6.1 Oracle reachability under declared information rights — the theory contribution

Generalize the information-rights comparison table from a figure into a
**checkable criterion**:

> For any agent-migration benchmark, declare the information rights granted to the
> method. Then require that every ground-truth target be **derivable** from those
> rights. A ground-truth item that is not derivable is an unreachable oracle and
> must be repaired or excluded.

RISK-0022 is exactly a violation: the oracle requires `::`, which is outside the
declared rights. RISK-0021 is a second form: the oracle names a field absent from
every visible contract. Give the criterion a name, formalize it, and publish an
audit procedure. Any benchmark author can then apply it.

**Information-rights table to reproduce in the paper:**

| Method | Old schema | Old trace | New schema | Migration map | Probe new API |
|---|---|---|---|---|---|
| Static | yes | no | yes | no | no |
| Direct LLM | yes | optional | yes | no | no |
| ToolEVO | stale | — | via interaction | no | **yes** |
| IEEE normalization | — | controller memory | yes | **known manifest** | at execution |
| **Ours** | yes | **yes** | yes | no | **no, before first call** |
| Oracle | yes | yes | yes | **yes** | no |

### 6.2 Audit a public benchmark with the same criterion — highest leverage experiment

Run the reachability audit on **MCPEvol-Bench** and/or **DynamicMCPBench**. If
unreachable-oracle cases exist there too, the finding moves from "a defect in our
sandbox" to "a defect in the field's current benchmarks." This is mostly analysis,
not compute, and it is the single largest credibility multiplier available.

Do this **before** writing. It determines whether the paper is a single-system
case study or a field-level contribution.

### 6.3 Measure the unobservable-convention guess rate

For cases requiring a convention outside the declared information rights (the
`::` family), measure model success against chance. Success materially above
chance on a convention the model cannot observe is evidence of **training-data
contamination or convention priors**, not capability. Clean, novel, and directly
supported by existing artifacts.

### 6.4 Abstention is currently scored as failure — demonstrate it

Gate 08's policy correctly refused to construct the `::` value, producing an
unconstructible call. Under current scoring that is a failure; under
safety-aware scoring it is the correct behavior. This is concrete evidence for
the `NO_EQUIVALENT` contribution rather than an argument for it. Report
`Coverage(τ)` vs `FirstAttemptSuccess(τ)` vs `UnsafeMigrationRate(τ)`.

### 6.5 Optional — conclusion half-life

This program has a chronological gate log in which several conclusions were
overturned by audit, with `DEC-####` traceability for downstream decisions. If
the RAG measurement failures are included as a secondary case study, quantify how
long each wrong conclusion stood and what it influenced. Almost nobody has this
data. Keep it to an appendix or a short subsection unless the paper is reframed
around measurement validity.

---

## 7. Method — one mechanism only

```
Old tool contract + verified old trace
        -> intent signature
        -> candidate new tools
        -> tool equivalence scorer
        -> argument correspondence
        -> confidence
        -> ALIGN | ABSTAIN | NO_EQUIVALENT
        -> first execution
```

Do not build a mega-agent. If a preliminary gate shows a direct strong LLM already
solves intent mapping, drop the learned scorer and pivot to measurement,
uncertainty, and no-equivalent detection. Method complexity is not a virtue.

## 8. Baselines, metrics, evaluation tiers

**Baselines** — B2 and B5 are the killer comparators:

```
B0  new schema only
B1  old + new schemas
B2  old + new schemas + verified old trace     <- killer
B3  embedding / schema matching
B4  cross-encoder
B5  strong LLM reasoning mapper                <- killer
B6  proposed method
B7  oracle migration map
```

Beating B3/B4 while losing to B2 or B5 means the algorithmic contribution is weak.
Say so if it happens.

**Metrics.** Headline is execution, not mapping:

- Primary: **First-Attempt Task Success**
- Intermediate: `ToolAlignment@1`, `ArgumentMappingF1`, `NoEquivalentF1`
- Safety: `UnsafeMigrationRate = P(wrong semantic mapping is executed)`
- Secondary: end-to-end success, abstention rate, latency, tokens

Never headline alignment accuracy if execution success does not move.

**Evaluation tiers:**

- **Tier A — controlled education sandbox.** Exact gold, deterministic, clean
  v1/v2/v3, split/merge, near-collision, `NO_EQUIVALENT`. Cannot stand alone
  (self-authored).
- **Tier B — external evolution benchmark.** MCPEvol-Bench or a compatible subset.
  Ask *our* question on *their* data; claim no new benchmark.
- **Tier C — 20–50 real version pairs**, human-verified from release notes, Git
  history, OpenAPI diffs, MCP server versions. Firecrawl may collect docs; gold
  must be verified by hand. **Thirty real cases beat five hundred synthetic renames.**

**Split discipline.** Hold out **base tools / API families**, not randomly mutated
instances. The same old tool appearing in train and test under two different
renames is leakage.

---

## 9. Outcome cases — historical method-plan routing

| Case | Result | What to write |
|---|---|---|
| **A** | Strong-LLM baseline 55–65%, method ~75–80%, false migration down on held-out drift | Algorithmic paper. Value ~8–8.5/10. |
| **B** | Alignment +10pp but task success +1–3pp | Diagnostic/method analysis. Do not hype the algorithm. ~6/10. |
| **C** | Method does not win, but a clear discovery (e.g. history helps split/merge and no-equivalent but not simple renames) | Reframe: *"When Do Historical Tool Traces Help? A Controlled Study of LLM Agents under API Schema Drift"*. Still real value. |
| **D** | Baselines saturate at 97–99% | Do not write a method paper. Write the systems/measurement report or change the question. This is a correct scientific outcome. |

These cases belong to the earlier Gate-20-dependent algorithmic plan. They are
not active Gate 10 branches: Gate 20 was cancelled by `DEC-0047`, and Gate 08's
alignment-method result is already **NEGATIVE** under `DEC-0023`.

### Gate 19-C routing outcome (2026-09-11)

This arc lands in **Case Study B / tier (b)**: a single-system measurement case
study with a reusable reachability criterion. The paper route is therefore the
measurement-report branch. It must not claim an algorithmic win, a new
benchmark, SOTA, external validation, or repaired-lane performance, and it must
not turn the frozen Gate 07/08 numbers into repaired-lane evidence.

## 10. Paper structure and page budget

Main text 10–12 pages plus appendix.

| Section | Budget |
|---|---|
| Abstract (~180–220 words) | — |
| 1. Introduction | 1–1.5 pp |
| 2. Related Work (4 groups: evolving tool agents / tool-schema optimization / API migration / MCP evaluation) | 1–1.5 pp |
| 3. Problem Formulation — define *reference-free* and *pre-execution* explicitly | ~1 p |
| 4. Cross-Version Evaluation Setting — drift families, hidden gold, splits, **information rights**, **oracle reachability audit** | 1.5–2 pp |
| 5. Method | 1–1.5 pp |
| 6. Experiments | ~1 p |
| 7. Results & Analysis | 2–3 pp |
| 8. Deployed Case Study: VietRAGOps Evolve | **0.5–1 p, no more** |
| 9. Limitations | 0.5–1 p |
| 10. Conclusion | ~0.3 p |
| Appendix | prompts, mutations, configs, deployment, screenshots |

**Figure 1** is the problem, not the architecture: old trace + new API →
cross-version alignment → argument translation → confidence/abstain → first
execution. **Figure 2** is the information-rights table. Firecrawl, MarkItDown,
Cloud Run and MCP architecture diagrams belong in the appendix.

## 11. Contributions — exactly four

> **First**, we provide a checkable criterion and auditor: **oracle reachability
> under declared information rights**. A ground-truth item is reachable iff its
> target is derivable from the information the method is granted. The auditor is
> implemented, tested, and independently reproduces the `10/35` and `5/15`
> findings it was built to test.

> **Second**, we measure unreachability in a synthetic benchmark: across 12 drift
> families and 310 pair items, 260 are reachable and 50 are unreachable (16.1%).
> The `argument_merge` family is `0/30`, `tool_replacement` retains `15/35`, and
> `argument_split` is `40/40`.

> **Third**, we observe that synthetic drift generation introduces unreachable
> oracles that real API evolution does not in the measured control: 20
> hand-verified real MCP/API version pairs yielded `0/20` unreachable items.

> **Fourth**, we show that repairing an unreachable oracle can shrink a benchmark
> below its own statistical power. After repair, the minimum detectable
> differences are `0.2975` (`argument_split`, `n=40`), `0.4348`
> (`tool_replacement`, `n=15`), and `0.2503` pooled, all above the pre-registered
> meaningful effect of `0.20`.

The paper must also report the required secondary finding, which is not counted
as a fifth contribution: the project's RISK-0022 mechanism claim is contradicted
by the raw frozen artifacts. They show `0/85` literal `::` constructions and `0`
first-attempt successes in the five affected cases; the prior mechanism
attribution was unverified inference.

## 12. Limitations to disclose

Syntactic contracts cannot always establish behavioral equivalence; sandbox drift
may differ from production drift; historical traces may under-specify side
effects; providers update models silently; some migrations intrinsically require
probing or human documentation; `NO_EQUIVALENT` ground truth can be subjective;
the educational domain may limit generality; sample sizes are small and Wilson
intervals are wide; RISK-0020 through RISK-0023 as stated in §4.

## 13. Non-negotiables

- Every numeric claim traces to a frozen artifact. Negative results and
  limitations stay visible. No cherry-picking, no invented significance.
- **Never describe an arXiv preprint as peer-reviewed.**
- Do not claim "first benchmark of tool evolution" — MCPEvol-Bench precedes it.
- Do not claim SOTA on anything; there is no comparable baseline suite.
- Do not present Firecrawl, MarkItDown, MCP, Groq, OpenRouter, or Cloud Run as
  scientific contributions.
- Repair or exclude the RISK-0021 unreachable pairs **before** computing any
  first-attempt number on `tool_replacement`.
- Disclose Gate 08's NEGATIVE result and the RISK-0023 exposure.
- Do not modify frozen Gate 07/08 protocols, baselines, metrics, or datasets to
  make results look better. Repairing a demonstrably unreachable oracle is a
  documented, pre-registered change — silently editing ground truth is not.

## 14. arXiv logistics

- Categories: `cs.CL` primary, cross-list `cs.SE` and/or `cs.AI`.
- **Endorsement is required** for a first-time submitter without an academic
  email address. Plan for it early; it is a common cause of delay.
- Choose a license deliberately (CC BY is usual for reproducibility).
- The public repository is an asset: cite the artifact commit SHA in the paper so
  every number is traceable.

## 15. Gate sequence

| Gate | Purpose | Status |
|---|---|---|
| **Gate 18** | Close RISK-0026, deploy the repaired product lane | approved, next |
| **Gate 19** | Oracle repair (RISK-0021/0022) + reachability audit of a public benchmark (§6.2) + guess-rate measurement (§6.3) | **complete — single-system case-study tier; external validation not established** |
| **Gate 20** | Hostile baseline campaign B0–B7 under the repaired oracle and a frozen protocol | **CANCELLED — DEC-0047; underpowered scoreable surface** |
| **Gate 10** | Freeze and write the re-scoped measurement paper; prepare but do not submit | **AUTHORIZED — RE-SCOPED by DEC-0048; Gate 09 remains unauthorized** |

The highest-value next research action is **not writing and not adding features**.
It is Gate 19: repair the oracle, audit an external benchmark with the
reachability criterion, and quantify the unobservable-convention guess rate. That
result established the tier-(b) measurement route. No new campaign is authorized
to strengthen the paper; the frozen evidence is to be reported honestly.

### Gate 19 outcome (2026-09-11)

Gate 19 delivered the reusable reachability criterion and auditor. On the
frozen V4/V4.1 surface it reproduced `10/35` target-absent
`tool_replacement` pairs, five of 15 graded cases requiring an unobservable
`::` join, and `0/40` unreachable `argument_split` pairs. It also found the
same hidden join in `argument_merge` and separate unadvertised required-field
literal/default risks. The additive V1 oracle retains only 15 reachable
`tool_replacement` argument-pair items and excludes 20 with a per-item
manifest; no Gate 07 or Gate 08 metric was rescored.

The frozen baseline extraction found no literal `::` construction in 85
effective prediction rows for the five affected cases. The separately
authorized 60-request free-only diagnostic probe also emitted `::` at rate
`0` in both hidden strata, with three provider failures; this is diagnostic and
inconclusive, not evidence of contamination or a convention prior.

Path A confirmed public MCPEvol-Bench and DynamicMCPBench releases, but the
obtained records were not old/new contract-pair registers compatible with the
auditor. Path B supplied 20 hand-verified real MCP version pairs; all 20 were
reachable and none was unreachable. External validation of the local defect is
therefore **not established**. The evidence supports **Case Study B / tier (b):
a single-system case study with a reusable criterion**, not a field-level
measurement contribution and not an algorithmic paper.

Gate 20 is cancelled by DEC-0047. The retained surfaces have MDE `0.2975` at
`n=40` for `argument_split`, `0.4348` at `n=15` for `tool_replacement`, and
`0.2503` at pooled `n=55`, all above the pre-registered 0.20 practical effect;
the required per-arm sizes are `90`, `76`, and `87`. Under `DEC-0048`, Gate 10
is the authorized replacement route: write only the tier (b) paper, preserve
the original Gate 07/08 numbers as historical, and disclose that Path B is a
20-pair negative control rather than external validation. Gate 09 and Gate 20
remain unauthorized for this route.
