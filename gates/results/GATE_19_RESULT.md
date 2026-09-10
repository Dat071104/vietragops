# Gate 19 Result — Oracle Reachability, Repair, Guess Rate, and External Evidence

Status: **COMPLETE — Tier (b): single-system case study with a reusable criterion**

Gate 19 does not support a field-level measurement contribution: the public
benchmark paths did not yield an auditor-compatible external old/new oracle
register, and the 20-pair real MCP control sample produced `0` unreachable
items. It does support a reusable criterion and a measured, additive repair of
the local oracle. Gate 20 remains unauthorized; Gate 10 remains blocked.

## O0 — Entry, freeze, and integrity

- Entry `HEAD` and `origin/main`: `bfdbb60a6bed118d058712ccc63471c16c16ecd2`.
- Final local `HEAD`: `6253faa1367d0bf543739de31f4ebb33a416413d`. No push occurred; `origin/main`
  remains `bfdbb60a6bed118d058712ccc63471c16c16ecd2`.
- Entry overlay: exactly 25 pre-existing paths; index empty. No overlay path
  was staged by Gate 19.
- Full suite: **612 passed, 2 warnings** in pytest `489.44s`, using
  `.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider` and an
  external `--basetemp`. The explicit Gate 19 unit file separately passed
  `6 passed`.
- Latest pre-Gate19 OpenRouter account receipt: Gate 18-R observed `4/1000`
  used and `996` remaining for its observed UTC day. Gate 19 records its own
  local diagnostic budget separately and does not fabricate a fresh provider
  account balance.
- Frozen-input manifest: `gates/results/GATE_19_FROZEN_SOURCE_HASHES.json`,
  SHA-256 `e2e7ed915e55b8e2eb57378a3b53ebf106bc8d3c4141c7b6791d652c5c86e115`, covering `134` files:
  `UNCHANGED=134, CHANGED=0, MISSING=0` at O7 verification.
- Protocol: `gates/baselines/GATE_19_PROTOCOL.json`, commit
  `8eb7da69d3d0e4793f43c20cf87bb39fcbecd35f`, SHA-256 `1933f88e543cec81fc5f3625ffcdb6a11f717fea836a623be30cf98a666dede2`.

Key frozen hashes (the complete machine-readable list is in the manifest):

| Artifact | SHA-256 |
|---|---|
| `GATE_07_PROTOCOL_V4.json` | `7a35301f22c780756893470c92034eb882e06b6d48fd0e7b0447776486a94cb1` |
| `GATE_07_PROTOCOL_V4_1_ADDENDUM.json` | `df13ee0791222fdf19f456bae09ed2b4edff0f1e3d0a` |
| `GATE_07_METRICS_V4.json` | `cda1fcc184f39c114a112a0369556ccfd251942029ee5b232529ca53d992ba5f` |
| `GATE_08_PROTOCOL.json` | `ee5bfadfb1fd863ba9ccfdb050df1eea282491c0b81739cc9efd854e8279a036` |
| `GATE_07_RESULT.md` | `e0746f3316eb4f5a6200c60f44746cfb42968bde9bad9e65b3b21d541f2ed461` |
| `GATE_08_RESULT.md` | `b2de815baaf6e76fe74e081db195c6649236e7492c1a03e9a1cb028651ef442a` |
| Gate 07 V4 `llm_results.jsonl` | `c25e760841574ffa0eac2abb5fe7717e71f91533d2ab5be146f0c0794c17f599` |
| Gate 07 V4 raw `llm.jsonl` | `b324e50a8428ff3c684226341584276470197b4cd24a725d73bd513895959200` |
| Gate 08 `decisions.jsonl` | `ddbd0a43e50c492a570c28982d32d44cb1a04d102918969bf17edce79eb96d35` |

The manifest re-verification returned `UNCHANGED=134`, `CHANGED=0`,
`MISSING=0`. Gate 07 and Gate 08 files remained read-only.

## O1 — RISK-0021 characterization

The 35-pair register is independently enumerated below. `Original target` is
`—` where the frozen correct new input does not contain the absent field; the
ground-truth pair still names that field.

| # | Case | Old arg | New tool | New arg | Original target | Status | Action |
|---:|---|---|---|---|---|---|---|
| 1 | `G07-G-0127` | `student_id` | `finalize_paid_registration` | `learner_ref` | `STU-0014` | `REACHABLE` | `RETAIN` |
| 2 | `G07-G-0127` | `course_code` | `finalize_paid_registration` | `section_ref` | `CRS-021::TERM-01` | `UNREACHABLE-CONVENTION-UNOBSERVABLE` | `EXCLUDE` |
| 3 | `G07-G-0127` | `term_id` | `finalize_paid_registration` | `section_ref` | `CRS-021::TERM-01` | `UNREACHABLE-CONVENTION-UNOBSERVABLE` | `EXCLUDE` |
| 4 | `G07-G-0128` | `student_id` | `grant_completion_credential` | `learner_ref` | `STU-0011` | `REACHABLE` | `RETAIN` |
| 5 | `G07-G-0128` | `course_code` | `grant_completion_credential` | `section_ref` | `—` | `UNREACHABLE-TARGET-ABSENT` | `EXCLUDE` |
| 6 | `G07-G-0129` | `room_code` | `confirm_room_booking` | `facility_ref` | `ROOM-004` | `REACHABLE` | `RETAIN` |
| 7 | `G07-G-0129` | `term_id` | `confirm_room_booking` | `section_ref` | `—` | `UNREACHABLE-TARGET-ABSENT` | `EXCLUDE` |
| 8 | `G07-G-0130` | `student_id` | `finalize_paid_registration` | `learner_ref` | `STU-0018` | `REACHABLE` | `RETAIN` |
| 9 | `G07-G-0130` | `course_code` | `finalize_paid_registration` | `section_ref` | `CRS-005::TERM-03` | `UNREACHABLE-CONVENTION-UNOBSERVABLE` | `EXCLUDE` |
| 10 | `G07-G-0130` | `term_id` | `finalize_paid_registration` | `section_ref` | `CRS-005::TERM-03` | `UNREACHABLE-CONVENTION-UNOBSERVABLE` | `EXCLUDE` |
| 11 | `G07-G-0131` | `student_id` | `grant_completion_credential` | `learner_ref` | `STU-0012` | `REACHABLE` | `RETAIN` |
| 12 | `G07-G-0131` | `course_code` | `grant_completion_credential` | `section_ref` | `—` | `UNREACHABLE-TARGET-ABSENT` | `EXCLUDE` |
| 13 | `G07-G-0132` | `room_code` | `confirm_room_booking` | `facility_ref` | `ROOM-008` | `REACHABLE` | `RETAIN` |
| 14 | `G07-G-0132` | `term_id` | `confirm_room_booking` | `section_ref` | `—` | `UNREACHABLE-TARGET-ABSENT` | `EXCLUDE` |
| 15 | `G07-G-0133` | `student_id` | `finalize_paid_registration` | `learner_ref` | `STU-0020` | `REACHABLE` | `RETAIN` |
| 16 | `G07-G-0133` | `course_code` | `finalize_paid_registration` | `section_ref` | `CRS-007::TERM-02` | `UNREACHABLE-CONVENTION-UNOBSERVABLE` | `EXCLUDE` |
| 17 | `G07-G-0133` | `term_id` | `finalize_paid_registration` | `section_ref` | `CRS-007::TERM-02` | `UNREACHABLE-CONVENTION-UNOBSERVABLE` | `EXCLUDE` |
| 18 | `G07-G-0134` | `student_id` | `grant_completion_credential` | `learner_ref` | `STU-0003` | `REACHABLE` | `RETAIN` |
| 19 | `G07-G-0134` | `course_code` | `grant_completion_credential` | `section_ref` | `—` | `UNREACHABLE-TARGET-ABSENT` | `EXCLUDE` |
| 20 | `G07-G-0135` | `room_code` | `confirm_room_booking` | `facility_ref` | `ROOM-012` | `REACHABLE` | `RETAIN` |
| 21 | `G07-G-0135` | `term_id` | `confirm_room_booking` | `section_ref` | `—` | `UNREACHABLE-TARGET-ABSENT` | `EXCLUDE` |
| 22 | `G07-G-0136` | `student_id` | `finalize_paid_registration` | `learner_ref` | `STU-0020` | `REACHABLE` | `RETAIN` |
| 23 | `G07-G-0136` | `course_code` | `finalize_paid_registration` | `section_ref` | `CRS-007::TERM-02` | `UNREACHABLE-CONVENTION-UNOBSERVABLE` | `EXCLUDE` |
| 24 | `G07-G-0136` | `term_id` | `finalize_paid_registration` | `section_ref` | `CRS-007::TERM-02` | `UNREACHABLE-CONVENTION-UNOBSERVABLE` | `EXCLUDE` |
| 25 | `G07-G-0137` | `student_id` | `grant_completion_credential` | `learner_ref` | `STU-0013` | `REACHABLE` | `RETAIN` |
| 26 | `G07-G-0137` | `course_code` | `grant_completion_credential` | `section_ref` | `—` | `UNREACHABLE-TARGET-ABSENT` | `EXCLUDE` |
| 27 | `G07-G-0138` | `room_code` | `confirm_room_booking` | `facility_ref` | `ROOM-013` | `REACHABLE` | `RETAIN` |
| 28 | `G07-G-0138` | `term_id` | `confirm_room_booking` | `section_ref` | `—` | `UNREACHABLE-TARGET-ABSENT` | `EXCLUDE` |
| 29 | `G07-G-0139` | `student_id` | `finalize_paid_registration` | `learner_ref` | `STU-0003` | `REACHABLE` | `RETAIN` |
| 30 | `G07-G-0139` | `course_code` | `finalize_paid_registration` | `section_ref` | `CRS-020::TERM-03` | `UNREACHABLE-CONVENTION-UNOBSERVABLE` | `EXCLUDE` |
| 31 | `G07-G-0139` | `term_id` | `finalize_paid_registration` | `section_ref` | `CRS-020::TERM-03` | `UNREACHABLE-CONVENTION-UNOBSERVABLE` | `EXCLUDE` |
| 32 | `G07-G-0140` | `student_id` | `grant_completion_credential` | `learner_ref` | `STU-0009` | `REACHABLE` | `RETAIN` |
| 33 | `G07-G-0140` | `course_code` | `grant_completion_credential` | `section_ref` | `—` | `UNREACHABLE-TARGET-ABSENT` | `EXCLUDE` |
| 34 | `G07-G-0141` | `room_code` | `confirm_room_booking` | `facility_ref` | `ROOM-009` | `REACHABLE` | `RETAIN` |
| 35 | `G07-G-0141` | `term_id` | `confirm_room_booking` | `section_ref` | `—` | `UNREACHABLE-TARGET-ABSENT` | `EXCLUDE` |

The auditor summary is exact: `tool_replacement` has 35 pairs, 10
`UNREACHABLE-TARGET-ABSENT`, 10 convention-affected pair records, and 15
reachable pairs. `argument_split` has 40 pairs and `0` unreachable.

### Downstream exposure (not a rescore)

| Frozen quantity | Affected surface | Exposure |
|---|---|---:|
| Pair-level `tool_replacement` mapping denominator | 10 target-absent pairs / 35 | 28.57 percentage points; frozen target-absent ceiling `25/35=0.7143` |
| Pair-level `tool_replacement` mapping plus convention records | 20 excluded pair records / 35 under the repaired oracle | Retained pair set has 15/15 reachable; no frozen F1 is restated |
| Case-level first-attempt denominator | Five hidden-join cases / 15 | 33.33 percentage points of the case denominator |
| Strict complete-call repaired case slice | Every one of 15 cases has at least one excluded pair | `0/15` complete cases; no repaired case-level first-attempt score exists in Gate 19 |

The affected frozen headline numbers are Gate 07 `tool_replacement` strongest
Argument F1 `0.3867` and strongest first-attempt `0.5333`, and Gate 08
`gate08_method` Argument F1 `0.1333` and first-attempt `0.0000`. These are
exposure statements only. Gate 07/08 verdicts and metrics were not recomputed.

## O2 — RISK-0022 and additional convention search

The sandbox uses the hidden convention in three code paths:

```python
# research/gate07/sandbox/operations.py
return str(direct).split("::", 1)[0]
return str(section).split("::", 1)[1]
"section_code": f"{course['course_code']}::{_term_id(args)}"
```

The method-facing surface contains old contracts, new contracts, task prose,
and verified old traces. `::` is absent from those surfaces for the affected
cases; it appears only in internal operations code and evaluator-side target
construction. The five graded cases are
`G07-G-0127`, `G07-G-0130`, `G07-G-0133`, `G07-G-0136`, and `G07-G-0139`.

The search covered all 310 argument-pair records across the 12 frozen graded
families, all method-visible contracts/descriptions/schemas/traces, the
ground-truth construction values, and 45 separate new-required-field items.
It found:

- the same hidden `::` join in `argument_merge`: 30/30 pair records across
  15/15 graded cases;
- hidden required-field literals/defaults: 15/15 `added_required_field`
  acknowledgement values and 5/25 `tool_replacement` required-field items;
- no additional hidden separator, encoding, ordering, or unit in the
  argument-pair families beyond the `::` join.

The frozen prediction extraction is in
`gates/results/GATE_19_FROZEN_CONVENTION_AUDIT.json`:

| Baseline arm/model | Cases | `::` | Different separator | No join |
|---|---:|---:|---:|---:|
| `cross_encoder` / `BAAI/bge-reranker-v2-m3@953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` | 5 | 0 | 0 | 5 |
| `embed_name_desc` / `BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181` | 5 | 0 | 0 | 5 |
| `embed_serialized_schema` / `BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181` | 5 | 0 | 0 | 5 |
| `lexical_name` / `deterministic_lexical_name` | 5 | 0 | 0 | 5 |
| `lexical_serialized` / `deterministic_lexical_serialized` | 5 | 0 | 0 | 5 |
| `llm_new_schema_only` / `openai/gpt-oss-120b` | 5 | 0 | 0 | 5 |
| `llm_new_schema_only` / `openai/gpt-oss-20b` | 5 | 0 | 0 | 5 |
| `llm_old_new_direct` / `openai/gpt-oss-120b` | 5 | 0 | 0 | 5 |
| `llm_old_new_direct` / `openai/gpt-oss-20b` | 5 | 0 | 0 | 5 |
| `llm_old_new_direct_v3_legacy` / `openai/gpt-oss-120b` | 5 | 0 | 0 | 5 |
| `llm_old_new_direct_v3_legacy` / `openai/gpt-oss-20b` | 5 | 0 | 0 | 5 |
| `llm_old_new_history` / `openai/gpt-oss-120b` | 5 | 0 | 0 | 5 |
| `llm_old_new_history` / `openai/gpt-oss-20b` | 5 | 0 | 2 | 3 |
| `llm_reasoning` / `openai/gpt-oss-120b` | 5 | 0 | 0 | 5 |
| `llm_reasoning` / `openai/gpt-oss-20b` | 5 | 0 | 1 | 4 |
| `positional_prior` / `deterministic_control` | 5 | 0 | 0 | 5 |
| `random_choice` / `deterministic_control` | 5 | 0 | 0 | 5 |

Across 85 effective rows there were zero literal `::` constructions, three
different-separator constructions, and 82 no-join outputs. This raw observation
does not agree with the Gate 08 prose statement that some baselines succeeded
by guessing `::`; Gate 19 preserves the discrepancy instead of inventing a
hidden output.

## O3 — Criterion and auditor

**Oracle reachability under declared information rights:** For an
agent-migration benchmark, declare information rights `R`. A ground-truth item
is `REACHABLE` iff its target value and every construction step are derivable
from `R` alone. Otherwise it is an unreachable oracle and must be repaired or
excluded before scoring.

For this benchmark, `R` contains old schema, verified old traces, new schema,
and task context. It excludes evaluator-only truth, sandbox internals,
migration maps, new-version trajectories, candidate-order oracle, scoring code,
and pre-execution probing. The full machine-readable declaration is
`research/gate19/information_rights.json`.

The auditor reports exactly three statuses: `REACHABLE`,
`UNREACHABLE-TARGET-ABSENT`, and `UNREACHABLE-CONVENTION-UNOBSERVABLE`. Its
tests cover direct reachability, absent target field, hidden separator, and
rights-field omission. All tests are offline. The criterion detects
underivability, not semantic wrongness: a derivable but incorrect target can
still pass this criterion.

## O4 — Additive exclusion dataset

The pre-registered policy excludes both unreachable classes. It never replaces
the target with a guessed field, separator, format, or default. The new files
are:

- `gates/baselines/GATE_19_TOOL_REPLACEMENT_ORACLE_V1.json` — 15 retained
  reachable pair items;
- `gates/baselines/GATE_19_TOOL_REPLACEMENT_ORACLE_V1_MANIFEST.json` — all 35
  original pair items with original value, status, action, reason, derivation,
  and frozen source references.

The retained pair-level maximum attainable recall is `1.0` because every
retained item is reachable. The strict complete-call case-level slice is empty
because all 15 cases contain at least one excluded pair. No Gate 07 or Gate 08
metric is restated on this set; rescoring belongs to a future Gate 20 protocol.

## O5 — Unobservable-convention guess rate

The chance baseline was frozen before measurement as the nine plausible
separator set `::`, `:`, `|`, `/`, `-`, `_`, `.`, `~`, `,`; uniform
`P(::)=1/9=0.1111`.

Frozen artifacts: 0/85 effective prediction rows contained `::`; 3 used a
different separator and 82 had no join. This is a raw-output observation, not a
new request.

Diagnostic probe: `gates/results/GATE_19_DIAGNOSTIC_PROBE.json` used exactly 60
requests to `nvidia/nemotron-3-super-120b-a12b:free`, no fallback, free-only
catalog guard, `3.2s` minimum interval, and local budget `60/60 used,
0 remaining`. There were 57 valid JSON outputs and 3 provider failures.

| Stratum | Dispatched | Valid JSON | `::` rate, all dispatched | `::` rate, valid JSON | Exact hidden-gold rate, valid JSON |
|---|---:|---:|---:|---:|---:|
| Hidden sandbox `::` | 30 | 28 | 0.0000 | 0.0000 | 0.0000 |
| Hidden arbitrary separator | 30 | 29 | 0.0000 | 0.0000 | 0.1379 |

Both `::` rates are zero. At this sample size the probe gives no evidence of
an output convention prior or training-data contamination. It is diagnostic
only and not a Gate 07/Gate 08 measurement.

## O6 — External evidence

### Path A — public benchmark audit

The [MCPEvol-Bench paper](https://arxiv.org/abs/2607.14642) and its
[public repository](https://github.com/Octobrist/MCPEvol-Bench) were checked.
The repository exposes a 393-record trajectory/task file, and its README points
to the [evol-servers dataset](https://huggingface.co/datasets/anonymous2233/evol-servers).
The obtained task file has SHA-256
`b51d09d93aef94b08a67281a95ee8b4c7d69953816adf6769a996e26274bb023`, but it
contains questions, trajectories, tool calls, and evaluation results rather
than an old/new contract correspondence register. The 3.4 GB server archive
was not downloaded; no per-item O3 audit is claimed.

The [DynamicMCPBench paper](https://arxiv.org/abs/2607.20531),
[code](https://github.com/ITMO-NSS-team/DynamicMCPBench), and
[dataset](https://huggingface.co/datasets/TokenWasteGroup/DynamicMCPBench)
were also checked. The release uses effect checkpoints, equivalence sets,
minefields, and replay traces; it explicitly avoids fixed tool-list scoring.
Its code is Apache-2.0 and data CC BY 4.0, but it is not an old/new contract
pair register for this auditor. No bulk 2.58 GB download was made.

Path A therefore supplies public-release evidence about benchmark design, not
external validation of this oracle defect.

### Path B — real MCP version pairs

`gates/baselines/GATE_19_EXTERNAL_MCP_PAIRS.json` contains 20 hand-verified
parent/new commit pairs from the official
[MCP servers repository](https://github.com/modelcontextprotocol/servers).
The repository license records Apache-2.0 for new code, applicable legacy MIT
contributions, and CC-BY-4.0 documentation provisions. A local clone verified
all 20 commit objects and all 20 changed artifact paths. The derived audit is
`gates/results/GATE_19_EXTERNAL_AUDIT.json`:

| Status | Count |
|---|---:|
| `REACHABLE` | 20 |
| `UNREACHABLE-TARGET-ABSENT` | 0 |
| `UNREACHABLE-CONVENTION-UNOBSERVABLE` | 0 |

This purposive one-repository sample is a negative control for the auditor, not
a prevalence estimate. Thirty carefully verified pairs would be stronger than
this sample, but padding with low-quality cases would be worse; the evidence
does not justify an external field-level claim.

## O7 — Closure and verdict

The hash manifest reverified every recorded Gate 07/08 input unchanged. Gate 19
added no production source, corpus, manifest, chunk store, embedding, golden
set, GCP, deployment, IAM, Secret Manager, or paid provider state. RISK-0021
and RISK-0022 were updated with measured characterizations; RISK-0045 and
RISK-0046 record the additional convention/default findings. DEC-0046 records
the criterion and exclusion policy. RISK-0023 remains disclosed: three graded
ground-truth cases were read during Gate 08 scoping before held-out discipline
was tightened.

**Final verdict:** **Tier (b), a single-system case study with a reusable
criterion.** The criterion and additive repair are supported locally. The
diagnostic probe does not show a convention prior, and the external sample did
not contain unreachable items. The evidence does not support Tier (a) external
field-level measurement or an algorithmic contribution. Gate 20 must not begin
without a new authorization and protocol over the additive oracle.
