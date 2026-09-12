# GATE 21 RESULT — External Oracle Audit Feasibility (Path A Reopened)

**Date:** 2026-09-12
**Verdict:** **NOT AUDITABLE**
**Outcome matrix:** D — the register exists, but it cannot be mapped to the frozen auditor under determinable external rights.

This is a statement about derivability under a declared rights set. It is not a
defect judgment about MCPEvol-Bench and it is not an estimate of the prevalence
or quality of its benchmark.

## C0 — Entry receipt

- Canonical Git root: `D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps`.
- Branch: `main`.
- Entry `HEAD`: `ff5e2b157ad218ff5e8dc652cbf06e6eef821522`.
- Entry `origin/main`: `ff5e2b157ad218ff5e8dc652cbf06e6eef821522`.
- Pre-existing user-owned overlay: **27 paths**, all unstaged; the index was empty (`0` staged paths).
- Full suite: **612 passed, 2 warnings**, exit `0`, using an external `--basetemp` at `D:\Research\vietragops_gate21_c0_basetemp_20260912_162021`.
- `python scripts/reproduce.py`: exit `0`; Gate 19 offline tests passed `6/6`; frozen source inputs were `134/134 UNCHANGED`; the Gate 19 synthetic audit was bit-identical (`310/310`); the Gate 19 Path B external audit was bit-identical (`20/20`).
- Scope control: no provider call, paid API, GCP, IAM, Secret Manager, model run, or server archive download was planned or executed.

The C0 suite and reproduction passed, so the gate proceeded.

## C1 — Acquired and frozen external source

`main` resolved to commit
`888c779a0fe735f612ca62bdd1fdd7c9e6bf8701`. The four exact requested files
were downloaded outside the repository. Their URLs, byte sizes, SHA-256 values,
and external storage root are recorded in
`gates/results/GATE_21_EXTERNAL_SOURCE_HASHES.json`.

Observed total: **2,124,315 bytes**, derived by summing the four recorded file
sizes. No `evol-servers` archive was downloaded.

The pinned repository root has no `LICENSE` entry; the GitHub license endpoint
returned HTTP `404`; and `README.md` contains no repository license statement.
No redistribution permission was assumed from the separately labelled dataset.
The raw files are therefore not vendored; only hashes, URLs, and external paths
are recorded.

## C2 — Structural survey

The complete survey is `gates/results/GATE_21_STRUCTURE_SURVEY.md`. The headline
observations are:

| Unit | Observed count |
|---|---:|
| Server entries across the four stage files | 347 |
| Tool-level records across the four stage files | 487 |
| Distinct `(server, tool)` pairs across stages | 298 |
| Duplicate pair observations, derived as `487 - 298` | 189 |
| Distinct `mutation_type` values | 3 (`PARAM`, `DESC`, `TOOL`) |

Mutation-type denominators are **tool-level records**:

| Mutation type | Records |
|---|---:|
| `PARAM` | 141 |
| `DESC` | 152 |
| `TOOL` | 194 |

The key required-field result is measured in **parameter items**, not records:
`parameter_additions` occurs in 110 PARAM records and contains 312 parameter
items, of which **312 are optional and 0 are required**. A separate
`parameter_changes` surface contains 27 `action:add` items, including 2 marked
required, but these are not entries in `parameter_additions` and still have no
expected-call target value. `parameter_removals` contains 11 items, including 2
marked required; removals do not create new argument targets.

`PARAM` records carry named change metadata and source-code `diff_hunks`, but no
complete normalized old/new argument sets and no target-bearing expected call.
`DESC` records carry description pairs, not argument targets. `TOOL` records mix
summaries, lists, and 22 full-looking new tool configurations; they do not carry
a complete old/new argument correspondence. All 357 `diff_hunks` are source
snippets (`old_code`/`new_code`/`file_name`, with `anchor_code` on 6), so deriving
a full schema from them would require implementation-code inference. The gate
does not perform that inference.

The `task_idx` field is present on server entries, not as a unique tool-record
identifier: across 347 server entries there are 73 distinct values in the range
0–84. Gate 19's prior release observation found a separate `test_cases.json`
with 393 records and `tool_calls`, but Gate 21 did not re-download that 15.8 MB
file under the approximately 2 MB acquisition budget. The pinned runner reads
test cases by `idx` and selects mutation-involved cases by server/tool
membership; it does not evidence a `task_idx -> idx` join. The expected-call
recoverability answer is therefore **UNVERIFIED**. It could be established
without the 3.4 GB archive only by a separately declared and verified join to
the small task file. The archive is not a substitute for that join.

## C3 — External information rights

`research/gate21/external_information_rights.json` declares the external rights
separately from `research/gate19/information_rights.json`.

The rights are established from the paper and the pinned runner/agent source:

- before the first call, the agent receives the current tool names,
  descriptions, and `inputSchema`, plus task/runtime context;
- the agent does not receive the old schema, old trace, evolution register,
  migration map, or evaluator-only expected call;
- after a call, the runner appends the stringified tool result or error (limited
  to the first 500 characters) to the next model request;
- the agent retains conversation history and can continue until stop or the
  dynamically selected `max_round` bound.

The paper's own formalization says that the description space includes “essential
metadata such as tool input schemas and semantic descriptions” and that tool
execution produces an observation logged into the trajectory. The repository's
runner labels the path “Evolved toolset(s) (example with hybrid mutation path)”
and passes current tool definitions into the agent. This is an interactive
current/new-schema setting, not the local Gate 19 pre-execution old/new setting.

Under these rights:

| Mutation type | Auditable under frozen argument-target auditor? | Reason |
|---|---|---|
| `PARAM` | No for the acquired records | Named additions/changes exist, but no declared target-bearing expected call or verified `task_idx` join exists; full old/new sets would require inference. |
| `DESC` | No | Description before/after pairs are outside the auditor's argument-target input schema. |
| `TOOL` | No | Tool summaries/new configurations lack a complete old/new argument correspondence and target call. |

The rights are sufficiently established to make this negative feasibility
finding. The public paper HTML does not expose the full H.3 prompt text; this is
recorded as a limitation, not filled by assumption.

## C4 — Adapter and unmodified auditor

The adapter is `research/gate21/mcpevol_adapter.py`. It is an adapter only: it
does not import or modify `research/gate19/auditor.py`, does not infer fields or
values from `old_code`/`new_code`, and refuses a record atomically when the
required target-bearing surface is absent.

Offline adapter tests passed: **5 tests**, exit `0`.

The complete machine-readable result is
`gates/results/GATE_21_EXTERNAL_AUDIT.json`. Units are explicit there:

- input/refusal counts are **tool-level records**;
- converted/audited counts are **auditor items**;
- status counts are counts of converted auditor items only.

| Mutation type | Input records | Converted auditor items | `REACHABLE` | `UNREACHABLE-TARGET-ABSENT` | `UNREACHABLE-CONVENTION-UNOBSERVABLE` | Refused records |
|---|---:|---:|---:|---:|---:|---:|
| `PARAM` | 141 | 0 | 0 | 0 | 0 | 141 |
| `DESC` | 152 | 0 | 0 | 0 | 0 | 152 |
| `TOOL` | 194 | 0 | 0 | 0 | 0 | 194 |
| **Total** | **487** | **0** | **0** | **0** | **0** | **487** |

The zeros in the status columns are not reachability results over the input
records; their denominator is **converted auditor items**, and that denominator
is zero. The headline result is the **487-record adapter refusal count**.

Refusal reasons, with denominator **tool-level records**, are:

| Reason code | Refused records |
|---|---:|
| `MUTATION_TYPE_OUTSIDE_ARGUMENT_TARGET_SCHEMA` (`DESC`/`TOOL`) | 346 |
| `PARAM_OPTIONAL_ADDITION_HAS_NO_TARGET_CALL` | 110 |
| `PARAM_COMPOSITE_CHANGE_HAS_NO_TARGET_CALL` | 19 |
| `PARAM_CHANGE_HAS_NO_TARGET_CALL` | 6 |
| `PARAM_REMOVAL_HAS_NO_NEW_TARGET_FIELD` | 6 |
| **Total refused** | **487** |

The unmodified auditor was invoked on the adapter's item output. It received
`0` auditor items and returned zero counts for all three statuses. No external
reachability rate was calculated.

## C5 — Manual verification

Ten refusal records were hand-checked against the raw JSON, spanning all three
observed mutation types and multiple structural shapes. The adapter's refusal
reason agreed with the raw record in all 10 checks.

| # | Raw record (stage/server/tool) | What the raw JSON says | Adapter return | Hand check |
|---:|---|---|---|---|
| 1 | `stage1 / mcp-maven-deps / get_latest_release` | `parameter_additions`: `packaging` and `rows`, both `required:false` | `PARAM_OPTIONAL_ADDITION_HAS_NO_TARGET_CALL` | Correct refusal; no target call/value in register |
| 2 | `stage1 / @executeautomation/playwright-mcp-server / playwright_navigate` | `waitUntil` removed, `timeout` added optional, plus description change | `PARAM_COMPOSITE_CHANGE_HAS_NO_TARGET_CALL` | Correct refusal; composite PARAM record has no target value |
| 3 | `stage1 / @henkey/postgres-mcp-server / pg_execute_query` | required `operation` removed and optional `includeColumns` added | `PARAM_COMPOSITE_CHANGE_HAS_NO_TARGET_CALL` | Correct refusal; no target-bearing expected call |
| 4 | `stage2 / @kazuph/mcp-taskmanager / request_planning` | `priority` added required, with optional `estimatedDeadline` and `tags` | `PARAM_COMPOSITE_CHANGE_HAS_NO_TARGET_CALL` | Correct refusal; required add is named but target value is absent |
| 5 | `stage4 / @tsmztech/mcp-server-salesforce / salesforce_search_all` | required `scope` removed and optional `targetRecordId` added | `PARAM_COMPOSITE_CHANGE_HAS_NO_TARGET_CALL` | Correct refusal; no new target call/value |
| 6 | `stage1 / mcp-sequentialthinking-tools / sequentialthinking_tools` | nested tool description pair plus 12 parameter-description items | `MUTATION_TYPE_OUTSIDE_ARGUMENT_TARGET_SCHEMA` | Correct refusal; DESC is not an argument target |
| 7 | `stage1 / derived-mcp-server / add_block` | tool `original_description` and `modified_description` pair | `MUTATION_TYPE_OUTSIDE_ARGUMENT_TARGET_SCHEMA` | Correct refusal; description-only surface |
| 8 | `stage2 / @primeng/mcp / get_usage_example` | record-root `original_description` and `modified_description` | `MUTATION_TYPE_OUTSIDE_ARGUMENT_TARGET_SCHEMA` | Correct refusal; description-only surface |
| 9 | `stage1 / @magicuidesign/mcp / addition_summary` | scalar summary of a new `getComponentIndex` tool | `MUTATION_TYPE_OUTSIDE_ARGUMENT_TARGET_SCHEMA` | Correct refusal; TOOL summary has no old/new argument pair |
| 10 | `stage2 / mcp-maven-deps / new_tool_config` | full-looking new config with `name`, `description`, `input_schema` | `MUTATION_TYPE_OUTSIDE_ARGUMENT_TARGET_SCHEMA` | Correct refusal; no corresponding old contract/target call |

The protocol also requests at least three auditor-marked UNREACHABLE items.
That sample is **NOT RUN / impossible under the acquired surface**: the
auditor marked no items because the adapter converted zero records. Creating
three synthetic auditor items, or labelling refusals as auditor statuses, would
violate the fail-closed rule. This is a limitation of auditability, not a
classification disagreement or a manufactured negative result.

## C6 — Interpretation and manuscript consequence

The verdict is **NOT AUDITABLE**, not “auditable with zero unreachable items.”
The register contains meaningful evolution metadata, but the frozen auditor
needs a target-bearing argument item: a declared new field, expected target
value, method-visible source surface, and any evidenced construction rule. The
acquired records do not supply that item, and `task_idx` is not a demonstrated
join to `test_cases.json`.

This gate therefore produces a second, more precise negative boundary for Path
A. It does **not** constitute external validation, and it is not a second
negative control with a reachability denominator. Gate 19 Path B remains the
purposive 20-pair external negative control; Gate 21 does not change its result.

The owner-facing manuscript changes are listed, with current quotations and
required replacements, in `gates/results/GATE_21_MANUSCRIPT_DELTA.md`. The
universal claim that a benchmark has no reason to publish an old/new register
must not appear in the submitted manuscript. The current `paper/main.tex` at
entry HEAD did not contain that exact sentence; the delta replaces the current
weaker-but-incomplete Path A wording and adds the real reason for the
non-auditability. Section 5.4 is explicitly updated to state that Gate 21 adds
no scoreable external items and does not alter Gate 19-C power calculations.

`_agent_ops/RISK_REGISTER.md` contains RISK-0048, recording that Gate 19 Path A
did not examine `evolution.json` and that Gate 21 examined it but still found
the acquired register unauditable under declared rights.

## Limitations

1. No independent `task_idx -> test_cases.json idx` join was established; the
   expected-call surface is consequently UNVERIFIED.
2. The small task file was not re-downloaded, and the 3.4 GB server archive was
   not downloaded. No server implementation or runtime behavior was inspected.
3. Source-code diff hunks are weaker than declared old/new contracts; no schema
   was inferred from implementation code.
4. The external agent has post-call feedback and retry, unlike the local
   pre-execution rights. Gate 21 does not claim comparability of its interactive
   setting to Gate 19's first-call score.
5. The four files are cumulative, so raw record counts and distinct pair counts
   have different units. All reported denominators are labelled.
6. The source repository's license status was not found; no raw files are
   redistributed in this repository.
7. No model, agent, MCP server, execution trajectory, or paid provider was run
   in Gate 21. This is a feasibility audit, not a behavioral benchmark result.

## C7 — Closure status

The C7 re-run on the final gate code surface produced:

- Full suite: **612 passed, 2 warnings**, exit `0`, in 462.97s.
- Reproduction: exit `0`; all Gate 19 checks passed; 134 frozen files were
  `UNCHANGED`; synthetic and Path B external outputs were bit-identical.
- C7 verification `HEAD` before selective Gate 21 release staging:
  `ff5e2b157ad218ff5e8dc652cbf06e6eef821522`.
- The pre-existing overlay remained **27 paths** and the index remained empty
  before release staging. The exact comparison is recorded in the Closure
  Receipt.
- No push was performed. The owner must push, if desired, after reviewing the
  explicit Gate 21 path set.

## Final status

**Gate 21 is closed as NOT AUDITABLE.** No later gate is started. The only
remaining handoff is owner review of the additive artifacts and the manuscript
delta; applying the manuscript delta is outside this gate.
