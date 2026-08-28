# Gate 07 Result — Scientific Gate-0

Status: **GO**

## Current decision summary

The v3 `GO` is retracted and v3 is superseded for scientific interpretation.
The fresh V4 collection re-establishes a narrow scientific `GO` for the
`argument_split` family under forced selection, explicit value transforms,
shuffled candidates, corrected intervals, and supplied-value first-attempt
execution. This is not a broad claim about all drift families.

The decisive V4 evidence is: strongest observed applicable forced-selection
Argument F1 `0.500 [0.125,0.875]` (history / `openai/gpt-oss-120b`, n=8),
best-case imputation `0.733`, and first-attempt success `0.500` with the same
best-case `0.733`. The strongest complete offline Argument F1 is `0.167`.
The forced-selection carrier beats the `positional_prior` Tool@1 `0.400` and
the `random_choice` Tool@1 `0.200` controls on the family. The V4 argument-split
sample retains 0/3 ambiguity disagreements.

V4 missingness is reported, not hidden: across the five LLM arms and two
models, 1016/1800 records succeeded, 60 were parse failures, 180 were typed
provider errors, and 544 were rate-limited. Three 20b arms had no successful
records and are not treated as baseline failures; their imputation ranges are
published as `[0,1]`. In the `argument_split` slice, excluded records had mean
input estimate 1599.0 tokens versus 1518.5 for successes (+80.5); this is an
unadjusted screening signal, not a causal content claim. The GO is therefore
limited to the observed applicable arms and this synthetic family.

The abstention delta is measured with a fresh retained legacy collection on
the V4 shuffled tasks, not by rescoring v3. For direct 120b / argument_split,
v3 was 12/13 abstentions (92.31%); V4 legacy was 8/13 (61.54%), a delta of
`-30.77` percentage points. The V4 forced direct arm supplied a best candidate
on all four evaluable responses (0/4 explicit abstentions), while its mapping
and execution scores remain reported with n=4.

No conclusion is drawn that a model cannot split arguments: V4 history contains
successful split mappings, and the result is only that the corrected forced
selection baseline remains below the predeclared practical threshold on this
family.

## V4 freeze and retained receipts

- Protocol: `GATE_07_PROTOCOL_V4.json`, SHA-256
  `7a35301f22c780756893470c92034eb882e06b6d48fd0e7b0447776486a94cb1`.
- Freeze commit: `206b18b823c3fa581dc6cadd32073ba4ec981b05`; freeze-ledger
  receipt: `GATE_07_PROTOCOL_V4_FREEZE_LEDGER.json`.
- V4 metrics report: `GATE_07_METRICS_V4.json`, SHA-256
  `cda1fcc184f39c114a112a0369556ccfd251942029ee5b232529ca53d992ba5f`;
  independent regeneration produced the same SHA.
- Fresh LLM results/raw/request-ledger SHA-256 values are respectively
  `50b4aa776227231fafce7def344b5f4d6bec6a15b8adc81a54f622cca92ef14a`,
  `1b726623cf00d49a6b25be03babe68f1f70115ea4f4021de5cbb0f81aa2f56e1`, and
  `9833115bd87c23fa94e2fcacb36302e04dfad4b85f1d515708c99b9929c263a9`.
- Full suite: **489 passed, 2 warnings, 0 failed** under Python 3.13.9
  with `-p no:cacheprovider` and an explicit writable basetemp.

## Step 0 audit reproduction and finding classification

The independent v3 reproduction command produced:

```text
F1 target records=15 evaluable=13 abstain=12 select=1
F3 answerable total=198 leading-correct=198 non-leading=0
F3 first-correct-index={0:198}
F5 argument_split F1 mean=0.0 ci95=[0.0,0.0] n=13
F5 first-attempt mean=0.0 ci95=[0.0,0.0] n=13
F5 _summary([0.0]*13) => ci95=[0.0,0.0]
F5 _summary([1.0]*15) => ci95=[1.0,1.0]
```

| Finding | Classification | Evidence-based interpretation |
|---|---|---|
| F1 | Real prompt/contract bug plus measurement artifact | Literal v3 instructions made abstention compliant; 12/13 empty predictions forced Tool@1, Arg F1, and first-attempt zeros. |
| F2 | Expected behavior under the literal prompt; invalid capability inference | History `G07-G-0075` exactly matched the split oracle, and A013/A014/A015 annotator outputs selected the correct split tools without abstaining. |
| F3 | Real dataset/prompt ordering leak | All 198 answerable cases placed the correct tool at index 0; v3 @3/@5 therefore measured order rather than ranking quality. |
| F4 | Real evaluator implementation bug | The v3 harness split `course_code` and joined section inputs before execution; V4 executes only supplied values/transforms. |
| F5 | Real interval-estimator bug and measurement artifact | Resampling a constant vector necessarily produced a zero-width interval; V4 uses Wilson for proportions and flags continuous degeneracy. |
| F6 | Real non-random missingness risk | V3 had 10 `argument_split` provider errors; V4 reports typed failures and best/worst imputation instead of treating exclusions as wrong answers. |

## Historical v3 result — audited and superseded

The superseded v3 report claimed a scientific `GO` from `argument_split`, with
Argument F1 `0.000 [0.000,0.000]` and first-attempt success
`0.000 [0.000,0.000]` for the strong direct arm. Those numbers remain
historical audit evidence only. V3 predictions were not re-scored under V4.

## Historical v3 entry-gate verification

- R0 verified HEAD `d9045ca0c68e90bdbbcb28c14f40d69ed094790a` on `main`,
  `fed31c3` as an ancestor, empty index, and clean `git diff --check` apart
  from pre-existing overlay line-ending warnings. Gate 06 result was
  `Status: PASS`.
- The required suite baseline was reproduced with
  `PYTHON_DOTENV_DISABLED=true LLM_PROVIDER=mock`: sandbox attempt 355 passed /
  114 Windows temp permission errors; normal-filesystem rerun **469 passed,
  2 warnings, 0 failed**. The final repair suite reached **481 passed, 2
  warnings, 0 failed**. Compileall was clean.
- The pre-existing overlay stayed untouched, unstaged, and uncommitted:
  `AGENTS.md`, five deleted skill scripts, `tests/test_groq_rotation.py`, and
  the pre-existing `_agent_ops/` overlay entries. No Gate 06 file was changed.
- `git ls-remote origin main` returned `SEC_E_NO_CREDENTIALS`; remote SHA is
  therefore unknown. No push was attempted or authorized.

## Commit / tree state

Gate 07 repair commits, in execution order:

| Commit | Scope |
|---|---|
| `4d8ef60` | R1 fail-closed rendering, non-invertible seeds, regenerated manifests |
| `1e2ea8a` | R2 value-level public-surface leak detector and opaque lineage IDs |
| `9d425d3` | R3 mechanical freeze preflight wired to both runners |
| `a02f213` | R4 v3 dataset receipt and byte-stability test |
| `2721c45` | R5 committed v3 protocol freeze and v3 ledger identity |
| `2010dd5` | Post-freeze preflight receipt |
| `457638a` | R6 offline baseline receipt |
| `0b1b7dd`, `72f7fdf`, `8015916`, `bbd1d13`, `3327368`, `48b4ee1` | Pre-registered quota split and setup/accounting corrections |
| `d19410a` | R7 first-window checkpoint |
| `f31ac05` | R7 research-mode LLM baseline receipt |
| `9940786` | R8 metrics, CIs, first-attempt execution, history ablation |
| `58efdf9` | R9 blind ambiguity audit and adjudication |
| `this commit` | R10 result commit, after the AGY-4 availability decision and local consistency audit |

No result or raw provider dump was pushed. The working tree contains only the
pre-existing overlay plus the currently edited result/ops files until the R10
commit below.

## Protocol freeze

- Frozen file: `gates/baselines/GATE_07_PROTOCOL_V3.json`.
- Protocol file SHA-256:
  `c9b27e936be76ee1070db70714d9e75509c1f22d637160138db890bf1cc4b1f9`.
- The protocol records frozen HEAD
  `a02f2131a306c761034f79d4b5fa0cb60cbe8613`; it was committed at
  `2721c45` before any v3 headline run.
- The post-commit preflight passed with current HEAD `2721c45`, frozen ancestor
  `a02f2131`, and both v3 dataset digests equal to the live recomputation.
- R6 preflight passed at `2010dd5`; R7 first-window preflight passed at
  `bbd1d13`; R7 full-resume preflight passed at `48b4ee1`. All are descendants
  of the freeze commit. R8 and R9 only consumed retained v3 artifacts.
- No v3 headline run started before the protocol commit. The first two R7
  setup failures occurred before router/provider construction and consumed no
  provider quota; they are retained as diagnostics only.

## Dataset summary

- Fresh v3 lineage: **216 total**, **180 graded**, **36 held-out**.
- Each of the 12 families has 15 graded and 3 held-out cases.
- Graded manifest digest:
  `sha256:2f82956b7200836fa23aaca51d04b13b2013bb543e7aac0418f6f4944bb31dbe`.
- Held-out manifest digest:
  `sha256:e438087fb9a92c38a1028b0f7dc917ec080274c10dfd7af3543fe7bba3336378`.
- Graded ground-truth digest:
  `sha256:09e33dc8090d2929abe34e489ec71ac2ba324fd7eee03c8d51b93acc84cf201b`.
- All-case ground-truth digest:
  `sha256:0652903090172890c50166d60054c913b2c57d07992bc0076e7b834c826e28f1`.
- The sandbox is synthetic and in-memory only. Every case has real executed
  contract receipts; reset/state-hash reproducibility remains green.
- Held-out cases were generated and hashed but not sent to R6 or R7.

## The three repaired bugs

### Bug A — fail-open seed sanitization

R0 serialized all 216 method-facing tasks and found **20/180 graded** and
**4/36 held-out** seed leaks: graded 15 `multiple_old_to_one_new` and 5
`multiple_simultaneous_renames`; held-out 3 and 1. The direct probe
`_field_value("session_day", 20370827)` returned
`synthetic-session_day-20370827`, and `(20370827-20260827)//10000 == 11`.

R1 replaced the seed-bearing fallback with an explicit `KeyError`, added an
explicit renderer for every reachable input field, removed seed interpolation
from task prose, and replaced arithmetic seeds with deterministic SHA-256
derivation over family/variant/opaque-lineage/held-out inputs. Renderer
completeness and non-arithmetic seed tests passed.

### Bug B — freeze order was prose only

R0 searched the three headline runner files and found no Git/revision/dirty
checks. R3 added `preflight_headline_run`, which fails unless the protocol is
tracked, path-clean, its recorded revision resolves and is an ancestor of
current HEAD, and live graded/held-out digests match. Both offline and LLM
runner entry points call it before task loading/model/router work. Temporary
Git-repository tests covered dirty, untracked, digest-mismatch, and clean
committed cases.

### Bug C — anti-leak test checked attributes, not values

R0 reproduced the old boundary test as green (**1 passed**) on the leaking
dataset. R2 added a serialized-JSON detector over all 216 public tasks for the
full seed set, 12 family labels, tool IDs, lineage IDs, generator operator
names, and held-out markers, plus a deliberate seed-injection negative test.
The existing attribute-level assertion remains.

## Baseline arms and information rights

- `lexical_name`: normalized name-only similarity.
- `lexical_serialized`: normalized serialized-schema similarity.
- `embed_name_desc`: BGE-M3 name + description embedding.
- `embed_serialized_schema`: BGE-M3 serialized-schema embedding.
- `cross_encoder`: trained `BAAI/bge-reranker-v2-m3` cross-encoder.
- `llm_new_schema_only`: new contracts, task description, candidate list.
- `llm_old_new_direct`: old + new contracts, task description, candidate list.
- `llm_old_new_history`: old + new contracts + verified old traces, task
  description, candidate list.
- `llm_reasoning`: old + new contracts, task description, candidate list, with
  the reasoning-style prompt.

All LLM arms ran on pinned `openai/gpt-oss-120b` and
`openai/gpt-oss-20b`. Prompts received only each case's candidate subset, not
the full 39-tool surface. Every live call used `ProviderRouter(mode="research")`;
no Ollama fallback entered a research number. No proposed alignment/intent
method was implemented or run.

## Commands and retained artifacts

- R0: required session start, Git/state checks, full suite, compileall, Bug A/B/C
  reproductions, and v2 ledger accounting.
- R4/R6: v3 generator, public leak test, deterministic regeneration, exact BM25
  retrieval smoke, lexical/BGE/cross-encoder offline runners.
- R7: sequential research-mode runner with checkpoint/cache key
  `(arm_id, model, case_id, prompt_id)`, v3 router/request ledgers, and raw
  output retention.
- R8: `research.gate07.metrics.report` recomputed all numbers from v3 outputs,
  with 2,000 bootstrap samples and fresh sandbox first-attempt execution.
- R9: AGY-3 blind audit on a public-only stratified sample.

The tracked receipts are [`GATE_07_DATASET_V3.json`](../baselines/GATE_07_DATASET_V3.json),
[`GATE_07_OFFLINE_RESULTS_V3.json`](../baselines/GATE_07_OFFLINE_RESULTS_V3.json),
[`GATE_07_LLM_RESULTS_V3.json`](../baselines/GATE_07_LLM_RESULTS_V3.json),
[`GATE_07_METRICS.json`](../baselines/GATE_07_METRICS.json), and
[`GATE_07_AMBIGUITY_AUDIT_V3.json`](../baselines/GATE_07_AMBIGUITY_AUDIT_V3.json).
All raw v3 files remain ignored under `gates/artifacts/gate07/v3/`; their
checksums are recorded in the receipts. The v2 raw directory is audit-only and
does not feed any v3 file.

## Results

Metrics below are means with deterministic bootstrap 95% CIs. Provider and
parse failures are excluded from accuracy and shown separately. `n` is the
evaluable success count for that arm/model.

| Arm / model | n | Tool Alignment@1 | Argument F1 | No-Equivalent Accuracy | First-Attempt Success | parse / provider / rate failures |
|---|---:|---:|---:|---:|---:|---:|
| lexical_name | 180 | 0.733 [0.672,0.800] | 0.619 [0.548,0.688] | 0.000 (15) | 0.456 [0.383,0.528] | 0 / 0 / 0 |
| lexical_serialized | 180 | 0.667 [0.600,0.739] | 0.586 [0.515,0.654] | 0.000 (15) | 0.411 [0.339,0.483] | 0 / 0 / 0 |
| embed_name_desc | 180 | 0.822 [0.767,0.878] | 0.646 [0.579,0.708] | 0.000 (15) | 0.461 [0.389,0.533] | 0 / 0 / 0 |
| embed_serialized_schema | 180 | 0.644 [0.578,0.711] | 0.536 [0.463,0.606] | 0.000 (15) | 0.400 [0.328,0.472] | 0 / 0 / 0 |
| cross_encoder | 180 | 0.650 [0.583,0.722] | 0.552 [0.481,0.620] | 0.000 (15) | 0.372 [0.300,0.439] | 0 / 0 / 0 |
| new_schema_only / 120b | 156 | 0.744 [0.673,0.808] | 0.191 [0.132,0.255] | 0.933 (15) | 0.173 [0.115,0.231] | 6 / 18 / 0 |
| new_schema_only / 20b | 168 | 0.792 [0.732,0.851] | 0.198 [0.140,0.261] | 1.000 (15) | 0.173 [0.119,0.226] | 3 / 9 / 0 |
| old_new_direct / 120b | 178 | 0.590 [0.517,0.663] | 0.612 [0.541,0.684] | 1.000 (15) | 0.590 [0.522,0.663] | 1 / 1 / 0 |
| old_new_direct / 20b | 176 | 0.659 [0.591,0.733] | 0.650 [0.583,0.720] | 1.000 (15) | 0.585 [0.511,0.653] | 1 / 3 / 0 |
| old_new_history / 120b | 178 | 0.562 [0.489,0.640] | 0.579 [0.507,0.650] | 1.000 (15) | 0.551 [0.483,0.624] | 0 / 2 / 0 |
| old_new_history / 20b | 171 | 0.690 [0.620,0.760] | 0.678 [0.608,0.749] | 1.000 (12) | 0.614 [0.544,0.684] | 1 / 8 / 0 |
| reasoning / 120b | 173 | 0.497 [0.416,0.572] | 0.519 [0.445,0.595] | 1.000 (15) | 0.497 [0.422,0.572] | 4 / 3 / 0 |
| reasoning / 20b | 7 | 1.000 [1.000,1.000] | 1.000 [1.000,1.000] | NA | 1.000 [1.000,1.000] | 0 / 0 / 173 |

The full 13-arm × 12-family table, all metrics, all CIs, per-case metrics, and
failure-region flags are in `GATE_07_METRICS.json`. The row-level summary below
focuses on the strongest direct LLM and the strongest offline Argument-F1 arm.

| Family | Direct 120b Tool@1 | Direct 120b Arg F1 | Direct 120b First | Best offline Arg F1 | Blind disagreement | Stable load-bearing region |
|---|---:|---:|---:|---:|---:|---|
| tool_rename | 0.933 [0.800,1.000] | 0.978 [0.933,1.000] | 0.933 [0.800,1.000] | lexical_name 1.000 [1.000,1.000] | 0/3 | no |
| argument_rename | 0.933 [0.800,1.000] | 0.933 [0.800,1.000] | 0.933 [0.800,1.000] | lexical_name 0.667 [0.400,0.867] | 0/3 | no |
| multiple_simultaneous_renames | 1.000 [1.000,1.000] | 1.000 [1.000,1.000] | 1.000 [1.000,1.000] | embed_name_desc 0.167 [0.067,0.300] | 0/3 | no |
| added_required_field | 0.000 [0.000,0.000] | 0.000 [0.000,0.000] | 0.000 [0.000,0.000] | lexical_name 1.000 [1.000,1.000] | 0/3 | no |
| argument_split | 0.000 [0.000,0.000] | 0.000 [0.000,0.000] | 0.000 [0.000,0.000] | lexical_name 0.167 [0.067,0.300] | 0/3 | **yes: F1 + first attempt** |
| argument_merge | 0.067 [0.000,0.200] | 0.067 [0.000,0.200] | 0.067 [0.000,0.200] | lexical_name 1.000 [1.000,1.000] | 0/3 | no |
| output_restructure | 0.600 [0.333,0.800] | 0.600 [0.333,0.867] | 0.600 [0.333,0.867] | lexical_name 1.000 [1.000,1.000] | 2/3 | no: ambiguity > 0.20 |
| tool_replacement | 0.000 [0.000,0.000] | 0.000 [0.000,0.000] | 0.000 [0.000,0.000] | lexical_name 0.000 [0.000,0.000] | 0/3 | no |
| one_old_to_multiple_new | 0.467 [0.200,0.733] | 0.689 [0.489,0.867] | 0.467 [0.200,0.733] | lexical_name 0.667 [0.667,0.667] | 3/3 | no: ambiguity > 0.20 |
| multiple_old_to_one_new | 1.000 [1.000,1.000] | 1.000 [1.000,1.000] | 1.000 [1.000,1.000] | lexical_serialized 0.933 [0.800,1.000] | 0/3 | no |
| semantic_near_collision | 1.000 [1.000,1.000] | 1.000 [1.000,1.000] | 1.000 [1.000,1.000] | embed_name_desc 1.000 [1.000,1.000] | 0/3 | no |
| no_equivalent | 1.000 [1.000,1.000] | 1.000 [1.000,1.000] | 1.000 [1.000,1.000] | cross_encoder 0.467 [0.200,0.733] | 0/3 | no |

The failure-region structure is explicit in the metrics JSON. Its
`survives_all_baselines` flag is intentionally false for every family because
the weak offline arms force mappings on `no_equivalent`; the GO rule instead
asks whether a region survives the strongest direct LLM and strongest offline
baseline on the same load-bearing metric. `argument_split` meets that rule on
Argument F1 and first-attempt success. Weak arms do not carry the decision.

## History ablation

Paired comparison uses only cases with successful predictions from both arms
of the same model:

| Model | Paired n | History - direct Tool@1 | History - direct Arg F1 | History - direct First-Attempt |
|---|---:|---:|---:|---:|
| `openai/gpt-oss-120b` | 176 | -0.0284 [-0.0682,0.0114] | -0.0341 [-0.0739,0.0019] | -0.0398 [-0.0795,-0.0057] |
| `openai/gpt-oss-20b` | 167 | +0.0299 [-0.0060,0.0659] | +0.0279 [-0.0180,0.0758] | +0.0240 [-0.0120,0.0659] |

History does not provide a stable useful signal: the strong model is slightly
worse with history, while the mid model's small positive deltas include zero.
The GO is therefore not a claim that verified traces broadly solve alignment;
it targets the independently observed argument-split failure region.

## Ambiguity audit

- AGY-3: `gemini-3.7-flash-high`, two turns, read-only, public-only input;
  local Ollama fallback was not used.
- Sample: 36 cases, three per family. Rule and hashes are frozen in
  `GATE_07_AMBIGUITY_AUDIT_V3.json`.
- Overall case-level selected-tool/abstain disagreement: **5/36 = 13.89%**.
- Per-family: `output_restructure` 2/3, `one_old_to_multiple_new` 3/3, all
  other families 0/3.
- A020/A021 and A026 are genuinely ambiguous; A025/A027 are annotator-wrong.
  No oracle correction was made, so no before/after correction numbers exist.
- The two non-zero families exceed the frozen 0.20 ambiguity threshold and are
  excluded from the GO support. `argument_split` has 0/3 disagreements.

## Provider-failure accounting and budget

- Frozen budget: 1,440 base calls, retry budget 2, maximum 4,320 attempts,
  projected input 1,907,062 tokens, maximum output 737,280, 20% reserve.
- v2 consumed 1,440 disqualified ledger records; this constrained the first
  R7 window. DEC-0018 pre-registered seven canonical cases, 56 calls, before
  any v3 request.
- R7 v3 output: 1,440 unique cache keys and raw records; 1,207 success, 16
  parse failures, 41 HTTP-400 provider errors, and 176 local typed rate-limit
  stops (165 pool TPM, 11 org TPM). None of the 233 failure outcomes enters
  accuracy.
- The first 56 dotenv-disabled setup rows made no network calls and are kept
  in explicit setup-diagnostic backups; they are not counted as R7 provider
  usage. The declared v3 ledger contains only actual corrected attempts.
- Provider output-token usage is unavailable from the existing client; the
  ledger records the frozen per-attempt reservation and typed outcomes.

## Decision with quantitative evidence

Apply the R5-frozen thresholds literally:

1. **Stable failure region:** `argument_split` has 15 graded cases. On
   Argument F1, direct 120b is 0.000 and best offline is 0.167; both upper
   CIs are below the 0.90 saturation bar and both are far below the 0.75
   practical-failure bar. First-attempt success is 0.000 for both. The
   same family has Tool@1 0.000 for direct, but Tool@1 is not used as the
   shared metric because name-only offline arms can still select the tool
   while failing the split argument mapping.
2. **Not mostly ambiguity:** the blind sample has 0/3 disagreements for
   `argument_split`; the two ambiguous families are explicitly excluded.
3. **Downstream consequence:** first-attempt execution against a fresh sandbox
   is 0/13 for direct 120b and 0/15 for the strongest offline F1 arm.
4. **Concrete unavailable mechanism:** the load-bearing gap is composing one
   old argument into two new fields before first execution. The baselines only
   compare supplied text/contracts and do not receive a migration map,
   successful new-version trajectory, or trial-and-error feedback.

Therefore the frozen GO predicate is satisfied for this targeted region. The
evidence does not support a broad claim about all drift families: direct LLMs
solve rename, many-old-to-one-new, semantic-collision, and no-equivalent cases
well on this controlled set, while history adds no stable broad signal.

## Claims not supported

This result does **not** support claims that this is the first system for
changing APIs, the first evolving-tool benchmark, or the first evaluation of
evolving MCP/tool systems. It does not establish novelty over ToolEVO, ContDa,
or MCPEvol-Bench; schema similarity is not behavioral equivalence; deployment
is not proof of production readiness; Firecrawl output is not authoritative;
and arXiv status is not peer review.

## Known limitations

- The headline dataset is a synthetic education sandbox; no public/real API
  evolution dataset was included in this Gate-0 repair.
- Held-out cases were not run, as required by the frozen R6/R7 protocol.
- The blind audit has only three cases per family and is advisory, although it
  directly audited every sampled disagreement. The local fallback was not
  needed because AGY-3 was available.
- 176 rate-limited rows reduce evaluable coverage for the reasoning 20b arm to
  seven cases; that arm is not used as a strong decision carrier.
- The quota-free Groq model-list probe returned HTTP 403, so live model-list
  verification remains unverified; exact pinned model IDs and chat outcomes
  are recorded honestly.
- The remote Git SHA could not be checked because of `SEC_E_NO_CREDENTIALS`.
- The capability-gated oracle is an execution/import boundary, not
  cryptographic secrecy from a repository owner.

## Result-consistency audit

AGY-4 was attempted once as the authorized external consistency audit, but the
platform rejected transmission of raw v3 LLM artifacts/result data to the
external worker as unacceptable risk. This is recorded as
`AGY_UNAVAILABLE` for R10; no workaround or indirect disclosure was attempted,
and no independent AGY-4 claim is made.

A local read-only consistency audit then recomputed the live v3 dataset
digests, all v3 receipt hashes, 1,440 result/raw/ledger rows, 1,440 unique
cache keys, zero held-out rows, the complete 13-arm × 12-family metrics report,
and the 5/36 ambiguity rate. It also regenerated the metrics report from raw
v3 artifacts and obtained the same SHA-256
`489af74bb048e9434236c5898e3b4ae19ef76a35ef09d9b3d9c361d9736006ca`.
Local audit status: **LOCAL_CONSISTENCY_PASS**. This local check validates
bookkeeping and reproducibility; it is not an independent external audit.

## Acceptance checklist

- [x] Protocol frozen before headline run — `2721c45`, preflight receipts above.
- [x] Dataset checksum recorded — v3 receipt and protocol digests above.
- [x] Baseline prompts versioned — `gate07-llm-*-v1` in v3 protocol.
- [x] Research fallback disabled — every LLM arm used research mode; no
  Ollama fallback entered a number.
- [x] Raw outputs retained — 1,440 v3 raw records and hashes recorded.
- [x] Ambiguous cases audited — AGY-3 sample, disagreement, and adjudication
  receipt above.
- [x] Decision written with quantitative evidence — this result and metrics
  JSON.
- [x] `GATE_07_RESULT.md` written — this R10 commit.
- [x] No paper prose written.
- [x] v1/v2 results remain explicitly superseded/disqualified and do not feed
  v3.
- [x] Gate 06 frozen — `research/gate0/` untouched.
- [x] Gate 08 forbidden by the repair boundary.
- [ ] AGY-4 independent external result-consistency audit — **AGY_UNAVAILABLE**:
  platform blocked raw-artifact transmission; no independent claim is made.
- [x] Local read-only result-consistency audit — `LOCAL_CONSISTENCY_PASS`,
  receipt/hash/count/metric recomputation described above.

## Next allowed action

No Gate 08 work was performed or authorized. After the R10 commit, the only
allowed next step is a separately approved follow-on research plan that may
address the targeted pre-execution argument-split question. This Gate stops
here.

## Historical v2 BLOCKED record (retained below; disqualified and not evidence)

## Blocking reason

The pre-headline seed-leakage correction was represented by
`gates/baselines/GATE_07_PROTOCOL_V2.json`, but that amendment was not
committed before the v2 offline and LLM runs began. The last committed
protocol was v1 at `355daf0`; the v2 headline run started from
`3b6770f673523f093e9e3ff54c0133a2f24c7413` plus an uncommitted amendment.
The execution prompt requires the protocol freeze commit to precede every
Phase 7.4/7.5 headline run. A commit after the fact cannot repair that proof.

Therefore the v2 results are preserved as **DISQUALIFIED** audit artifacts.
This gate makes no scientific `GO`, `REFORMULATE`, or `STOP` decision.

## Entry-gate verification

- `HEAD`: `0561d54d5f623c0a913f222007f86a7f08ea3d66` at Phase 7.0; branch
  `main`; `git ls-remote origin main` matched exactly.
- `git merge-base --is-ancestor fed31c3 HEAD`: exit 0.
- The complete pre-existing 21-entry dirty overlay remained untouched and
  unstaged; the index was empty; `git diff --check` was clean.
- Gate 06 result existed with `Status: PASS`.
- Required baseline: **430 passed, 2 warnings** after rerunning the exact
  command with filesystem access; compileall exit 0.
- Ollama `/api/tags` succeeded. Groq configuration was inspected by variable
  names only at entry; no secret value is in this file.

## Commit / tree state

Valid preceding Gate 07 commits:

- `44be141` — extended sandbox and 216-case generator.
- `355daf0` — protocol v1 freeze.
- `bcdaca5` — rights-enforced baseline harness and raw artifact boundary.
- `3b6770f` — offline baseline code and metric support.

The v2 amendment and Phase 7.5 runner changes were present in the working tree
but not committed at headline start. No push was performed. Raw artifacts and
ledgers remain under ignored `gates/artifacts/gate07/`.

## Protocol freeze and amendment

Protocol v1:

- File: `gates/baselines/GATE_07_PROTOCOL.json`.
- Freeze commit: `355daf0`.
- It preceded the original v1 offline run, but its dataset was later found to
  expose generator seed text in public task material before any scientific
  result was accepted.

Protocol v2 amendment:

- File: `gates/baselines/GATE_07_PROTOCOL_V2.json`.
- Graded manifest digest: `sha256:32f0d29279dbbeb28ea7c3db1d076334242c7b2c092f4ac09cc32f8fb927890e`.
- Held-out manifest digest: `sha256:b4bee8ef70e14bec1d0c814394348e217bbaca9270d047ff13fc4a2da85e94a9`.
- Graded ground-truth digest: `sha256:859823d52068e4cd9f54dcb95674ba941c04794b2d7f269a6f6a5c7068614856`.
- Amendment reason: remove direct seed-bearing task/trace text; public audit
  confirmed no `20260827`, `family`, `operator`, `lineage_key`, or `tool_id`.
- Required freeze status at headline start: **NOT_COMMITTED**. This is the
  protocol violation; v2 is not an admissible freeze for the results below.

## Dataset summary

- Total generated: 216 cases.
- Graded: 180 cases.
- Held-out: 36 cases, 3 per family; not run.
- Family balance: all 12 families have 15 graded and 3 held-out cases.
- Sandbox surface: 39 synthetic tools per version; state is in-memory only.
- D9 one-old-to-multiple-new and D10 multiple-old-to-one-new shapes were
  represented explicitly before scoring.

## Baseline arms and runs

The v2 public task file contained only method-facing contracts/traces and no
oracle, family, operator, lineage, seed, or tool ID fields.

- Offline v2: lexical-name, lexical-serialized, BGE-M3 name/description,
  BGE-M3 serialized-schema, and BGE reranker cross-encoder.
- LLM v2: `llm_new_schema_only`, `llm_old_new_direct`,
  `llm_old_new_history`, and `llm_reasoning`, each on
  `openai/gpt-oss-120b` and `openai/gpt-oss-20b`.
- LLM runner used `ProviderRouter(mode="research")`, one sequential process,
  existing Groq client/key pool, frozen prompt IDs, cache keys, and ledger.
- No proposed intent/alignment method was implemented or run.

## Run inventory and provider accounting

These counts are factual run inventory only; they are not admissible scientific
metrics because the v2 amendment was uncommitted.

| Artifact | Records | Success | Parse failure | Provider error |
|---|---:|---:|---:|---:|
| Offline v2 predictions | 900 | 900 | 0 | 0 |
| Offline v2 raw records | 900 | 900 | 0 | 0 |
| LLM v2 results | 1,440 | 1,379 | 24 | 37 |
| LLM v2 raw records | 1,440 | 1,379 | 24 | 37 |

The LLM sweep had 720 records per model and 360 per arm. The 24 parse failures
and 37 provider errors never entered accuracy numerators or denominators.
Existing Groq 429 cooldown events were handled by the existing client; no
terminal rate-limited row was coerced into a wrong answer. Preflight was 8/8
successful. The `/models` verification request itself returned HTTP 403 and
was recorded as unverified provider model availability.

## Preliminary diagnostics — disqualified

An evaluator-only metric preview was generated after the v2 runs, before the
freeze-order violation was recognized. It is retained only to make the failure
lineage complete; it must not be cited as Gate 07 evidence. No official
`GATE_07_METRICS.json`, ambiguity result, or scientific decision was produced.

The disqualified preview showed Tool Alignment@1 / Argument F1:

| Arm/model | Tool@1 | Argument F1 | First-attempt success |
|---|---:|---:|---:|
| lexical_name | 0.7278 | 0.6139 | 0.4500 |
| lexical_serialized | 0.6833 | 0.5537 | 0.3944 |
| embed_name_desc | 0.8167 | 0.6463 | 0.4667 |
| embed_serialized_schema | 0.6556 | 0.5454 | 0.3944 |
| cross_encoder | 0.6389 | 0.5194 | 0.3667 |
| llm_new_schema_only / 120b | 0.1676 | 0.1676 | 0.1676 |
| llm_old_new_direct / 120b | 0.4911 | 0.5108 | 0.4911 |
| llm_old_new_history / 120b | 0.4727 | 0.4929 | 0.4727 |
| llm_reasoning / 120b | 0.5143 | 0.5333 | 0.5143 |

These numbers are not used to support any claim. History ablation is therefore
**not reportable**, and no conclusion about the history signal is allowed.

## Ambiguity audit

Not run. AGY-3 was unavailable, and no stratified blind annotation or oracle
adjudication was performed after the protocol violation. The absence of this
audit is another reason no scientific decision is made.

## Raw artifact checksums

All files below are ignored, retained locally, and not committed:

- `offline/lexical_v2.jsonl`: `1D8B043D95A91B6E0FDFC8353976603F395F0F770686357851096163DD2CCA4A`
- `offline/embedding_v2.jsonl`: `B13D46C2CC6F828B97A2CB5F0A3F552889B36183E31937ABCD742B8DD9289FA6`
- `offline/cross_encoder_v2.jsonl`: `D45CA52187CEA9B8BDC24BA730E7B0B511DFB2F8D45049C8877C572E4664CE78`
- `llm/results_v2.jsonl`: `EB715F9DE50A207D3745B319C8C7F885FE73F5D9F7A445789FB020DABBC54946`
- `raw/phase74_lexical_v2.jsonl`: `0B78FBEEC97B739821BE632F6EB95FE58D8CE8A7FDC8AB12AF741FA790101189`
- `raw/phase74_embedding_v2.jsonl`: `39236C695197E8E6ACBD9C4E9053B3C56D7E5D08DA699DB14DCEFD088C7F048C`
- `raw/phase74_cross_encoder_v2.jsonl`: `A604CFA2F7C59A571F1597BED4BA31C93FB7138FE105BF9B6D10AE4C79586E6E`
- `raw/phase75_llm_v2.jsonl`: `728E5C19CA1F95213E90B8F2E67D2D3CD251BE7A875A884D0E3895DA07144E4D`

## Result-consistency audit

AGY-4 was unavailable as a callable worker. A local read-only consistency
check reproduced all eight listed line counts and SHA-256 values exactly, and
reproduced the LLM totals (1,440 unique cache keys; 1,379 success, 24 parse
failure, 37 provider error). This validates artifact bookkeeping only; it does
not repair the missing pre-run protocol commit or make the v2 numbers
scientifically admissible.

## Acceptance checklist

- [ ] Protocol frozen before headline run — **failed**: v2 was uncommitted.
- [x] Dataset checksum recorded — v2 digest recorded above, but its run is
  disqualified by the freeze-order failure.
- [x] Baseline prompts versioned — `gate07-llm-*-v1`.
- [x] Research fallback disabled — runner asserted `mode="research"`; no
  Ollama fallback occurred.
- [x] Raw outputs retained — counts and checksums recorded above.
- [ ] Ambiguous cases audited — not run; AGY-3 unavailable.
- [ ] Decision written with quantitative scientific evidence — intentionally
  not possible from disqualified runs.
- [x] `GATE_07_RESULT.md` written.
- [x] No paper prose written.
- [x] Claims blacklist respected — no novelty claim over ToolEVO, ContDa, or
  MCPEvol-Bench; schema similarity was not treated as behavioral equivalence.
- [ ] AGY-4 independent result-consistency audit — unavailable; local
  count/hash reproduction is recorded above and is not claimed independent.

## Decision and next allowed action

Gate 07 is **BLOCKED**, not scientifically `STOP`. The only next allowed
action is a newly approved Gate 07 protocol repair/re-run plan that commits a
valid freeze before any new headline run and explicitly accounts for the
already-spent v2 budget. Gate 08 is not allowed. No next-Gate work was
performed.

STOP: No Gate 08 work performed.
