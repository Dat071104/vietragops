# Gate 19-C Result - Register contradiction, scoreable surface, and Gate 20 decision

Date: 2026-09-11
Status: CANCEL Gate 20 under DEC-0047; tier (b) single-system case study retained.

## Decision summary

Gate 20 is cancelled mechanically. Under the committed protocol, the retained surfaces cannot detect the pre-registered absolute 0.20 arm difference with 80% power: argument_split MDE is 0.2975 at n=40, tool_replacement MDE is 0.4348 at n=15, and the pooled MDE is 0.2503 at n=55. The strict complete-call surface for tool_replacement is actually 0/15 cases.

The replacement route is a separately authorized Gate 10 tier-(b) measurement paper. Gate 10 work was not performed here. Gate 08 DEC-0023 remains final and negative; no result in this arc overturns RQ3.

## Protocol and C0 entry

Protocol: gates/baselines/GATE_19C_PROTOCOL.json, commit 4e7a58f, SHA-256 53dcca2889b4f99bf61e0351228c019c56719482084a14cf0cee96e3666fc20e.

C0 matched:

- HEAD and origin/main: d80959824ee2059d0d0eb1cbfcb0f90681147e2d;
- exactly 25 user-owned overlay paths; index empty;
- .venv\Scripts\python.exe -m pytest --basetemp <external-temp>: 612 passed, 2 warnings;
- provider, cloud, deployment, secret, source, corpus, manifest, chunk store, embedding, golden-set, Gate 07, Gate 08, and Gate 19 frozen-data calls/mutations: zero.

The machine-readable C0 inventory records 99 protocol-surface hashes, 30 V3 raw-artifact hashes, and 17 V4 raw-artifact hashes. The two raw addenda were committed before extraction: 002f668 and 09f6b13.

| C0 receipt | SHA-256 |
|---|---|
| gates/baselines/GATE_19C_PROTOCOL.json | 53dcca2889b4f99bf61e0351228c019c56719482084a14cf0cee96e3666fc20e |
| gates/baselines/GATE_19C_C0_RAW_HASH_ADDENDUM.json | 126a919308b735b2ebd6bec7bf69ba895b40fd1b6edb0e6330c44944b52b8542 |
| gates/baselines/GATE_19C_C0_V4_HASH_ADDENDUM.json | eb641a6f08597e5952d37b69825712cbd56e3f3821b13a122f2b2d6a34d7f928 |
| gates/results/GATE_19_FROZEN_SOURCE_HASHES.json | e2e7ed915e55e8d2eb57378a3b53ebf106bc8d3c4141c7b6791d652c5c86e115 |

At C5, all 146 recorded C0 file hashes matched: UNCHANGED=146, CHANGED=0, MISSING=0. The hash inventory includes every file read by this gate; no secret value was read or recorded.

## C1 - RISK-0022 resolution

### Frozen targets and raw output

| Case | Frozen expected section_ref |
|---|---|
| G07-G-0127 | CRS-021::TERM-01 |
| G07-G-0130 | CRS-005::TERM-03 |
| G07-G-0133 | CRS-007::TERM-02 |
| G07-G-0136 | CRS-007::TERM-02 |
| G07-G-0139 | CRS-020::TERM-03 |

Gate 19-C extracted 85 effective V4/V4.1 prediction rows: 0 literal :: constructions, 3 different-separator constructions, and 82 no-join rows. The exact non-empty constructions are:

| Case | Baseline arm | Raw value/transform | Frozen target | Gate 07 first-attempt score | Outcome |
|---|---|---|---|---:|---|
| G07-G-0136 | llm_old_new_history / 20b | "CRS-007-TERM-02" | CRS-007::TERM-02 | 0 | precondition_failed |
| G07-G-0139 | llm_old_new_history / 20b | join delimiter "-", order 1; join delimiter "-", order 2 | CRS-020::TERM-03 | 0 | malformed_call |
| G07-G-0136 | llm_reasoning / 20b | "${course_code}-${term_id}" | CRS-007::TERM-02 | 0 | precondition_failed |

For completeness, the exact Gate 07 first-attempt score matrix for every baseline arm and affected case is below. 0 is a scored non-success; N/A is the frozen structural non-applicability/no-score case. No cell is 1.

| Baseline arm | 0127 | 0130 | 0133 | 0136 | 0139 |
|---|---:|---:|---:|---:|---:|
| cross_encoder / offline | 0 | 0 | 0 | 0 | 0 |
| embed_name_desc / offline | 0 | 0 | 0 | 0 | 0 |
| embed_serialized_schema / offline | 0 | 0 | 0 | 0 | 0 |
| lexical_name / offline | 0 | 0 | 0 | 0 | 0 |
| lexical_serialized / offline | 0 | 0 | 0 | 0 | 0 |
| llm_new_schema_only / 120b | N/A | N/A | N/A | N/A | N/A |
| llm_new_schema_only / 20b | N/A | N/A | N/A | N/A | N/A |
| llm_old_new_direct / 120b | 0 | 0 | 0 | 0 | 0 |
| llm_old_new_direct / 20b | 0 | 0 | 0 | 0 | 0 |
| llm_old_new_direct_v3_legacy / 120b | N/A | N/A | N/A | N/A | N/A |
| llm_old_new_direct_v3_legacy / 20b | N/A | N/A | N/A | N/A | N/A |
| llm_old_new_history / 120b | 0 | 0 | 0 | 0 | 0 |
| llm_old_new_history / 20b | 0 | 0 | 0 | 0 | 0 |
| llm_reasoning / 120b | 0 | 0 | 0 | 0 | 0 |
| llm_reasoning / 20b | 0 | 0 | 0 | 0 | 0 |
| positional_prior / control | 0 | 0 | 0 | 0 | 0 |
| random_choice / control | 0 | 0 | 0 | 0 | 0 |

### Scoring code and conclusion

The mapping scorer uses exact argument-name quadruples only:

~~~python
# research/gate07/metrics/scoring.py:56-59
predicted_args = _argument_pairs(prediction.get("argument_mapping", prediction.get("argument_pairs", [])))
correct_args = expected_args & predicted_args
precision = len(correct_args) / len(predicted_args) if predicted_args else (1.0 if not expected_args else 0.0)
recall = len(correct_args) / len(expected_args) if expected_args else 1.0
~~~

That scorer can give mapping credit for naming section_ref; it does not prove a value was constructed. First-attempt execution is stricter:

~~~python
# research/gate07/metrics/execution.py:154-173
expected_inputs = dict(zip(truth.correct_new_tool_names, case.new_inputs))
...
if args != expected_inputs[tool_name]:
    return FirstAttemptResult(..., "wrong_arguments", ...)
~~~

The evidence supports (b) reported successes were on other cases, and consequently (c) RISK-0022's mechanism claim was an unchecked inference. It does not support (a) for first-attempt success: that path required the exact expected input. The more precise finding is a split metric: the mapping scorer was lenient about values, while execution scoring was exact, and the audit trail attributed family-level success to the hidden cases without raw-case verification.

The paper consequence is material: replace the lucky :: guessing claim with an evidence-backed audit-trail/scorer distinction. Hidden-convention cases cannot be used as capability evidence in either direction.

## C2 - All-family scoreable surface

The auditor was rerun over all 12 drift families and matched the frozen Gate 19 pair audit exactly (310 items). The required-field audit also matched exactly (45 items).

| Family | Graded cases | Designed pairs | Reachable | Target absent | Convention unobservable | Retained pair items | Pair loss | Strict complete-call cases | Case loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| added_required_field | 15 | 40 | 40 | 0 | 0 | 40 | 0.00% | 0/15 | 100.00% |
| argument_merge | 15 | 30 | 0 | 0 | 30 | 0 | 100.00% | 0/15 | 100.00% |
| argument_rename | 15 | 20 | 20 | 0 | 0 | 20 | 0.00% | 15/15 | 0.00% |
| argument_split | 15 | 40 | 40 | 0 | 0 | 40 | 0.00% | 15/15 | 0.00% |
| multiple_old_to_one_new | 15 | 30 | 30 | 0 | 0 | 30 | 0.00% | 15/15 | 0.00% |
| multiple_simultaneous_renames | 15 | 40 | 40 | 0 | 0 | 40 | 0.00% | 15/15 | 0.00% |
| no_equivalent | 15 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| one_old_to_multiple_new | 15 | 30 | 30 | 0 | 0 | 30 | 0.00% | 15/15 | 0.00% |
| output_restructure | 15 | 15 | 15 | 0 | 0 | 15 | 0.00% | 15/15 | 0.00% |
| semantic_near_collision | 15 | 15 | 15 | 0 | 0 | 15 | 0.00% | 15/15 | 0.00% |
| tool_rename | 15 | 15 | 15 | 0 | 0 | 15 | 0.00% | 15/15 | 0.00% |
| tool_replacement | 15 | 35 | 15 | 10 | 10 | 15 | 57.14% | 0/15 | 100.00% |

no_equivalent has no argument-pair items, so pair columns are N/A; its separate no-equivalent metric is not a reachability-pair claim. The requested known figures are confirmed: argument_split 0/40 unreachable; tool_replacement retains 15/35 pair items; argument_merge is 30/30 unreachable.

### Hidden boolean/literal defaults

| Family | Hidden or relevant required value | Classification |
|---|---|---|
| added_required_field | consent_ack=true (5), honor_code=true (5), payment_ack=true (5) | item-unreachable; not derivable |
| tool_replacement | grant_completion_credential.approval_status="approved" (5/25 required-field items) | item-unreachable; not derivable |
| argument_split | period_ref required-field items (5/5) | derivable by identity; not a blocker |
| tool_replacement | other period_ref, payment_status, course_ref, and room approval_status items (20/25) | derivable; not a blocker |

The 15 boolean acknowledgement items and five credential approved items are not derivable from declared rights. The 5 argument-split required-field items and 20 other tool-replacement required-field items are derivable; they do not create an additional blocker. Because complete-call scoring requires every field, added_required_field and tool_replacement both retain 0/15 strict cases.

No family besides argument_split has enough clean, powered, full-call surface for a comparative claim in this gate. tool_replacement has 15 pair items but zero complete cases and fails the power rule; other families are either pair-only/untouched or do not meet the pre-registered repaired-lane claim boundary.

## C3 - Power analysis

The frozen decision rule used a two-sided two-sample normal approximation for independent proportions, equal n per arm, no continuity correction, alpha 0.05, target power 0.80, and practical absolute difference 0.20. The baseline anchor is the strongest applicable direct LLM versus strongest applicable offline/control arm under the frozen Gate 07 rule; pooled p_bar is retained-n weighted. The alternative is symmetric around p_bar: p_low=p_bar-d/2, p_high=p_bar+d/2.

| Surface | Retained n/arm | Baseline p_bar | MDE | Power at Delta=0.20 | Required n/arm | Wilson width at p_bar |
|---|---:|---:|---:|---:|---:|---:|
| argument_split | 40 | 0.3667 | 0.2975 (29.7 pp) | 0.4578 | 90 | 0.2862 |
| tool_replacement | 15 | 0.2667 | 0.4348 (43.5 pp) | 0.2300 | 76 | 0.4105 |
| pooled_retained | 55 | 0.3394 | 0.2503 (25.0 pp) | 0.6029 | 87 | 0.2429 |

| Surface | Observed baseline arm | Rate | Wilson 95% interval | Full width |
|---|---|---:|---|---:|
| argument_split | direct - llm_old_new_history/openai/gpt-oss-120b | 11/15 = 0.7333 | [0.4805, 0.8910] | 0.4105 |
| argument_split | offline - lexical_name/deterministic_offline | 0/15 = 0.0000 | [0.0000, 0.2039] | 0.2039 |
| tool_replacement | direct - llm_reasoning/openai/gpt-oss-20b | 8/15 = 0.5333 | [0.3012, 0.7519] | 0.4507 |
| tool_replacement | offline - lexical_name/deterministic_offline | 0/15 = 0.0000 | [0.0000, 0.2039] | 0.2039 |

At n=15, even the 0/15 Wilson interval has full width 0.2039, already wider than the entire pre-registered 0.20 practical-effect band; the observed nonzero arms are wider still (0.4105 and 0.4507). That is the power decision for the n=15 surface.

To reach the meaningful effect at 80% power would require 90 items per arm for argument_split, 76 for tool_replacement, and 87 for the pooled set. Manufacturing synthetic cases risks manufacturing more unreachable/default-dependent oracles; extending Path B is the safer evidence direction, but its 20 clean version pairs are not themselves enough to reach these item counts if each yields one scoreable item. The exact pairs-to-items conversion must be measured rather than invented.

## C4 - Gate 20 recommendation

CANCEL. The committed decision rule fails for argument_split, tool_replacement, and the pooled set. The pooled set cannot rescue the family-level failure, and strict tool_replacement complete-call n is zero. Provider budget should not be spent on B0-B7 under this surface.

The replacement recommendation is a separately authorized Gate 10 tier-(b) paper containing:

1. the declared-information-rights reachability criterion and reusable auditor;
2. the measured synthetic benchmark defect class, including argument_merge 30/30 unreachable, contrasted with Path B 0/20 unreachable in this sample;
3. the corrected RISK-0022 finding: raw evidence supports an unverified register mechanism claim, not :: guessing capability.

This remains a single-system case study. Path A was not audit-compatible, Path B is a negative control rather than external prevalence validation, and RQ3 remains NEGATIVE under DEC-0023.

## C5 - Integrity and closure

Post-change final suite observed 612 passed, 2 warnings in 528.54s with the external --basetemp. Frozen-input SHA-256 re-verification is recorded above as UNCHANGED=146, CHANGED=0, MISSING=0.

Updated records:

- DEC-0047 in _agent_ops/DECISION_LOG.md;
- corrected RISK-0022 plus C2 figures in RISK-0021/RISK-0045/RISK-0046 and new RISK-0047;
- _agent_ops/IMPLEMENTATION_LOG.md;
- _agent_ops/RESEARCH_PLAN_PAPER.md (§4, §9, §15);
- current-state pointers in CURRENT_TASK.md, SESSION_BRIEF.md, and PROJECT_CONTEXT_CARD.md.

No frozen artifact was modified. No push was made; owner approval remains required.

## Limitations

The power calculation is a planning analysis over retained argument-pair item counts, while first-attempt execution is case-level; this mismatch is reported explicitly and makes the strict tool_replacement conclusion more conservative, not less. The two-arm normal approximation is not a substitute for a future paired design analysis if Gate 20 were ever reconsidered. The 20-pair Path B sample is purposive and cannot establish field prevalence.

## Reproducibility

The analysis code is research/gate19c/analysis.py. It is offline and writes only the caller-selected output path. Re-run:

~~~powershell
.venv\Scripts\python.exe -m research.gate19c.analysis --repo-root . --output <external-analysis.json>
~~~
