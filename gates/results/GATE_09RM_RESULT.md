# Gate 09R-M Result — Operate, Reconcile, Observe

Status: **COMPLETE — read-only observation receipt with explicit unverified items**

Date: `2026-09-02`

## Decision and boundary

Gate 09R-M executed the authorized maintenance-only operation after Gate 09R
PASS / DEC-0027. It reconciled the approved ops-memory documents, classified
the pre-existing dirty overlay, and performed bounded read-only observations.
No product source, deployment configuration, GCP resource, budget, secret
value, Firecrawl call, or provider call was changed or created.

Gate 08 remains NEGATIVE and its method remains unadopted. The original Gate 09
full evaluation and Gate 10 remain unavailable. No Gate 07/08 rerun, rescore,
tuning, or scientific claim was made.

## Frozen protocol

- Protocol: `gates/baselines/GATE_09RM_PROTOCOL.json`
- SHA-256: `8212F0AC4C0895D1D281DF30B46D51B378C0DBF401B5A691455157E3498D4685`
- Gate 09R protocol SHA-256 rechecked:
  `F4C78F2E392D1BA55E030788E9255EB82944756DDB589316EC140008444C9E23`
- Working directory:
  `D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps`
- Required interpreter: `.venv\Scripts\python.exe`

## M0 entry-gate receipts

`session_start.py --root .` was run with the required interpreter. Relevant
output was:

```text
# Session Start (deterministic checks)
Root: D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps
Branch: main
HEAD: 3ceba47
Uncommitted changes: 29 file(s)
SESSION ESTABLISHED. A brief exists; no task is mid-flight.
SESSION_BRIEF has no usable Last Verified Commit. Treat project memory as UNVERIFIED against the current tree.
REPO_MAP: STALE
```

The exact entry checks were:

| Check | Receipt |
|---|---|
| `git rev-parse HEAD` | `3ceba474fc0c80fe88b44a2c4157b60ce37291be` |
| `git rev-parse gate09r-pass-20260831^{commit}` | `3ceba474fc0c80fe88b44a2c4157b60ce37291be` |
| live remote | The default Schannel attempt failed with `SEC_E_NO_CREDENTIALS`; the bounded read-only retry `git -c http.sslBackend=openssl ls-remote origin main` returned `3ceba474fc0c80fe88b44a2c4157b60ce37291be refs/heads/main`. |
| pre-freeze `git status --short` count | Exactly 29 paths, listed verbatim below. |
| pre-freeze `git diff --cached --name-only` | Empty. |
| `GATE_09R_PROTOCOL.json` SHA-256 | `F4C78F2E392D1BA55E030788E9255EB82944756DDB589316EC140008444C9E23` |
| first status line of `GATE_09R_RESULT.md` | `Status: **PASS**` |

The 29 pre-existing status paths were:

```text
 M AGENTS.md
 M PROJECT_STATE.md
 M _agent_ops/PROJECT_CONTEXT_CARD.md
 M _agent_ops/REPO_MAP.md
 M _agent_ops/RISK_REGISTER.md
 M _agent_ops/THIRD_PARTY_TOOLING.md
 M _agent_ops/phase_context_cards/evolve_2026_08_26/README.md
 D skills/implementation-logger/scripts/append_log.py
 D skills/project-context-cards/scripts/new_phase_card.py
 D skills/rag-eval-harness/scripts/compute_retrieval_metrics.py
 D skills/release-quality-gate/scripts/check_required_files.py
 D skills/zone-brain/scripts/scan_deps.py
?? _agent_ops/PHASE_ROADMAP.md
?? _agent_ops/archive/
?? _agent_ops/env_templates/
?? _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_03.md
?? _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_04.md
?? _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07.md
?? _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07_EXECUTION_PROMPT.md
?? _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07_REPAIR_PROMPT.md
?? _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_08.md
?? _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_09.md
?? _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_10.md
?? _agent_ops/tools/check_repo_hygiene.py
?? _agent_ops/tools/generate_context_card.py
?? _agent_ops/tools/scan_deps.py
?? _agent_ops/tools/summarize_implementation_log.py
?? gates/results/GATE_07_FIX_PROMPT.md
?? tests/test_groq_rotation.py
```

The newly written `GATE_09RM_PROTOCOL.json` is a gate artifact created after
this entry snapshot and is not part of the pre-existing 29-path overlay.

## M1 ops-memory reconciliation

| Record | Before | After |
|---|---|---|
| `_agent_ops/PHASE_ROADMAP.md` | Program state stopped at Gate 08 NEGATIVE with stale ops HEAD; Gate 00 was `Next / not started` and Gates 01-06 were stale blocked/tool-prepared states. | Program state is Gate 09R closed PASS, Gate 00-06 are PASS and pushed, Gate 07 is narrow V4.1 GO, Gate 08 is NEGATIVE, Gate 09 and Gate 10 are unavailable, and a `09R` row records `PASS — product-only release`. The superseded snapshot is retained under `Historical`. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/README.md` | Gate 08 was described as forbidden/not started; no 09R row existed. | Gate 08 is closed NEGATIVE, Gate 09R is `PASS — product-only release`, the original Gate 09 and Gate 10 are unavailable, and the 09R row points to this result. |
| `_agent_ops/SESSION_BRIEF.md` | Current and historical Gate 08/Gate 05-06 narratives were mixed; stale `31396a3` and duplicate verified-commit headings remained. | Current state is Gate 09R; exactly one authoritative `Last Verified Commit` records governance HEAD `3ceba474...` matching live `origin/main`, with runtime source `2d775ee`. Superseded material is under `Historical` / `Historical Evidence Archive`. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_09R.md` | Missing. | Added with Status / Source / Objective / Controls / Exit, limited to product-only observation and reconciliation. |
| `_agent_ops/INDEX.md` | Read order dated `2026-08-26`. | Not changed: the read order did not change; the active phase-card rule still routes to the active gate card. |

The four approved M1 files were the only pre-existing overlay files written.

## M2 complete 29-path overlay triage

No path was staged, restored, deleted, committed, or otherwise mutated during
triage. `PROMOTE` means a later explicit filename-level staging decision may be
considered; it does not mean staging occurred. `RESTORE?` records unresolved
intent and never authorizes `git checkout --` or `git restore`.

| Path | Class | Evidence / decision | Action proposed |
|---|---|---|---|
| `AGENTS.md` | `KEEP-DIRTY` | User-owned governance overlay. Its dirty text encourages multi-account/multi-key Groq rotation, contradicting RISK-0009 and the frozen single-authorized-key policy. | Leave untouched; security review is required before any decision. |
| `PROJECT_STATE.md` | `KEEP-DIRTY` | Stale user-owned project snapshot outside the approved M1 correction set. | Leave untouched. |
| `_agent_ops/PROJECT_CONTEXT_CARD.md` | `PROMOTE` | Durable historical Gate 07/08 context; already tracked but dirty. | Propose explicit `git add -- _agent_ops/PROJECT_CONTEXT_CARD.md` only after user review. |
| `_agent_ops/REPO_MAP.md` | `PROMOTE` | Durable map is dirty and stale relative to the checkout. Fresh generator output exists at `D:\Research\vietragops_repo_map_gate09r_2d775ee_final.md`. | Propose compare/overwrite and explicit add only after user decides; regeneration was not executed. |
| `_agent_ops/RISK_REGISTER.md` | `PROMOTE` | Durable risk entries are present in the dirty tracked copy. | Propose explicit `git add -- _agent_ops/RISK_REGISTER.md` only after user review. |
| `_agent_ops/THIRD_PARTY_TOOLING.md` | `PROMOTE` | Durable tooling-policy note; dirty tracked copy. | Propose explicit `git add -- _agent_ops/THIRD_PARTY_TOOLING.md` only after user review. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/README.md` | `PROMOTE` | Durable tracker and approved M1 write; remains unstaged. | Propose explicit `git add -- _agent_ops/phase_context_cards/evolve_2026_08_26/README.md` only under separate staging approval. |
| `skills/implementation-logger/scripts/append_log.py` | `RESTORE?` | Deleted from HEAD; intent cannot be inferred from the tree. | Ask user whether deletion is intentional; do not restore. |
| `skills/project-context-cards/scripts/new_phase_card.py` | `RESTORE?` | Deleted from HEAD; no authorized restore decision. | Ask user; do not restore. |
| `skills/rag-eval-harness/scripts/compute_retrieval_metrics.py` | `RESTORE?` | Deleted from HEAD; no authorized restore decision. | Ask user; do not restore. |
| `skills/release-quality-gate/scripts/check_required_files.py` | `RESTORE?` | Deleted from HEAD; no authorized restore decision. | Ask user; do not restore. |
| `skills/zone-brain/scripts/scan_deps.py` | `RESTORE?` | Deleted from HEAD. `_agent_ops/tools/scan_deps.py` exists but is not byte-identical to the deleted script, so it is not proof of intentional replacement. | Ask user; do not restore. |
| `_agent_ops/PHASE_ROADMAP.md` | `PROMOTE` | Durable roadmap and approved M1 write; remains unstaged. | Propose explicit `git add -- _agent_ops/PHASE_ROADMAP.md` only under separate staging approval. |
| `_agent_ops/archive/` | `PROMOTE` | Directory contains durable `_agent_ops/archive/README.md`. | Propose explicit `git add -- _agent_ops/archive/README.md` only after review. |
| `_agent_ops/env_templates/` | `PROMOTE` | Directory contains `_agent_ops/env_templates/README.md`; template values were not read. | Propose explicit `git add -- _agent_ops/env_templates/README.md` only after review. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_03.md` | `PROMOTE` | Durable phase card. | Propose explicit filename-level add after review. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_04.md` | `PROMOTE` | Durable phase card. | Propose explicit filename-level add after review. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07.md` | `PROMOTE` | Durable phase card. | Propose explicit filename-level add after review. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07_EXECUTION_PROMPT.md` | `PROMOTE` | Durable historical gate prompt. | Propose explicit filename-level add after review. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07_REPAIR_PROMPT.md` | `PROMOTE` | Durable historical gate prompt. | Propose explicit filename-level add after review. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_08.md` | `PROMOTE` | Durable negative-gate card. | Propose explicit filename-level add after review. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_09.md` | `PROMOTE` | Durable original-Gate-09 unavailable card. | Propose explicit filename-level add after review. |
| `_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_10.md` | `PROMOTE` | Durable unavailable Gate-10 card. | Propose explicit filename-level add after review. |
| `_agent_ops/tools/check_repo_hygiene.py` | `PROMOTE` | Durable tracked helper candidate. | Propose explicit filename-level add after review. |
| `_agent_ops/tools/generate_context_card.py` | `PROMOTE` | Durable tracked helper candidate. | Propose explicit filename-level add after review. |
| `_agent_ops/tools/scan_deps.py` | `PROMOTE` | Durable tracked helper candidate; not identical to the deleted zone-brain script. | Propose explicit filename-level add after review. |
| `_agent_ops/tools/summarize_implementation_log.py` | `PROMOTE` | Durable tracked helper candidate. | Propose explicit filename-level add after review. |
| `gates/results/GATE_07_FIX_PROMPT.md` | `KEEP-DIRTY` | Historical prompt artifact outside Gate 09R-M; no need to promote for this result. | Leave untouched. |
| `tests/test_groq_rotation.py` | `REVIEW-SECURITY` | Directly tests multi-key discovery, round-robin selection, cooldown skipping, and retry/rotation after HTTP 429. It implements assertions for rotation behavior; it is not merely a negative test against rotation. | Leave untouched; user security decision required against RISK-0009. |

The five deleted scripts remain unresolved `RESTORE?`; no restore command was
run. The rotation test was included in the full suite and passed, but its
passing behavior does not make the multi-key policy authorized.

## M3 read-only Cloud Run observation

All cloud commands used for this phase were read-only `describe`, `list`, or
filtered `get-iam-policy` calls. No API enablement prompt was accepted.

| Frozen 09R assertion | Live observation | Assessment |
|---|---|---|
| Project `vietragops-evolve-20260831` is ACTIVE | `gcloud projects describe ... --format=value(lifecycleState)` returned `ACTIVE`. | Consistent. |
| Region `asia-southeast1` | Both target services were successfully described using `--region=asia-southeast1`. | Consistent. |
| API traffic is 100% on `vietragops-api-00009-w5j`; rollback candidate receives no traffic; no `latest` target | Live traffic JSON showed `vietragops-api-00009-w5j` with observed `100`, a `rollbackcandidate` entry without a percent field, and no `latest` tag. | Consistent with the 09R receipt; the zero allocation is not directly emitted by this projection and is not restated as a newly observed number. |
| Web traffic is 100% on `vietragops-web-00002-wp9` | Live traffic JSON showed revision `vietragops-web-00002-wp9`, observed `100`, `latestRevision: true`. | Consistent. |
| API image digest is `sha256:f037b8189c01c13f5c686079c8d3abe86381dcddc0f28950d2b99af4eb816e96` | Artifact Registry digest lookup returned the exact digest. | Consistent. |
| Web image digest is `sha256:6b7a68f20c17b47321cb94a37dcec13af01a39d9915652c9547efdb37eeb7d4f` | Artifact Registry digest lookup returned the exact digest. | Consistent. |
| API is private; web is public | Filtered API IAM query returned no `allUsers`; filtered web IAM query returned `allUsers`. | Consistent. |
| Target budget control is `750,000 VND`, alerts `50%/80%/100%`; Cloud Run control is `375,000 VND` | Current Console redirected to sign-in. CLI budget listing requires a billing identifier, which this phase is prohibited from reading. | Not independently observable in this session; frozen 09R control remains the applicable policy. |
| Current billing cost is a point-in-time observation | The 09R receipt recorded `0 VND` on 2026-08-31. No current cost number was obtained in this session. | Current value unverified; no alarm or drift value was invented. |
| GCS lifecycle matches `deploy/gcp/storage-lifecycle.json` | Allowlisted bucket projection returned the four exact lifecycle rules: candidates 30 days, registry/snapshots 90 days, experiments 30 days, and sources/canonical/releases 365 days. Soft-delete metadata returned 604800 seconds. | Consistent. Versioning/uniform-access fields were not emitted by the current CLI projection and are not claimed as freshly observed. |
| Artifact Registry cleanup matches `deploy/gcp/artifact-cleanup-policy.json` | Observed `delete-untagged-builds` with `UNTAGGED`/`2592000s` and `delete-old-nonrelease-tags` with `TAGGED`/`ci-`/`2592000s`. | Consistent. |
| Secret Manager names and version counts only | Listed names were `FIRECRAWL_API_KEY` and `GROQ_API_KEY`; each had version count `1`, state `enabled`. No secret values were accessed. | Consistent with the 09R receipt. |
| Cloud SQL, GPU, GKE, Qdrant, queue, worker, commitment, subscription absent | Cloud Run service list contained only `vietragops-api` and `vietragops-web`; Pub/Sub subscription list was empty. Compute, SQL, GKE and Cloud Tasks list APIs were disabled and were not enabled; commitments therefore could not be enumerated. No extra Cloud Run GPU/worker/Qdrant service was listed. | No drift signal, but limited observation; disabled APIs prevent a complete independent inventory. |

## M4 bounded live health probe

The browser runtime used one tab only. The initial public web load reached the
Streamlit shell but failed to load dynamic `TextInput`, `Checkbox`, `Slider`,
`Metric`, and related modules. One bounded reload in the same tab reached the
app shell but still had no question textbox. No second tab was opened and the
known two-tab saturation behavior was not reproduced.

| Probe | Outcome |
|---|---|
| Public web grounded question with resolving citation | `NOT EXECUTED`: the question input was unavailable after bounded single-tab retry. No answer or citation was claimed. |
| Public web out-of-scope question | `NOT EXECUTED`: same UI limitation; no hallucinated answer was generated. |
| API readiness with identity token | `BLOCKED_BY_IDENTITY_TOKEN`: `gcloud auth print-identity-token --audiences=<API URL>` exited `1` without producing a token. No token was written to a file. |
| MCP missing auth | `403` observed at the private edge. |
| MCP wrong Origin | `NOT EXECUTED`: identity token unavailable. |
| MCP approved Origin | `NOT EXECUTED`: identity token unavailable. |
| Exposed MCP tools | Not freshly observed in cloud because authenticated MCP could not run. The frozen 09R receipt and local cloud-MCP test still specify exactly `document_status`, `index_status`, `retrieve_context`; this is not presented as a fresh live observation. |
| Groq-backed answers / spend | `0` answers initiated by this phase; attributable provider spend `USD 0.00`, within the `USD 0.50` phase ceiling. |
| Firecrawl | `0` calls initiated by this phase. |

The single-tab static-module failures are recorded as an observation/limitation,
not as a reproduced two-tab 429 finding and not as authorization to change
source or deployment.

## M5 residual-risk maintenance

### L1 / WinError 5

The known failing replacement target is
`app/api/__pycache__/routes_documents.cpython-313.pyc`. Read-only ACL metadata
showed the file exists, has no deny rule, and is under inherited ACLs; the
parent cache directory likewise had no deny rule. This does not explain away
the known host replacement failure, so no new compileall claim was made.

Minimal proposed repair, not executed: during a user-approved host maintenance
window, grant the owning local principal `Modify` permission on the affected
cache/file or repair the specific inherited ACL that blocks replacement, then
rerun only the compileall check. Do not change repository ownership, delete
`__pycache__` trees blindly, or alter ACL inheritance without a separate
approval.

### RISK-0015

`Open` for the local path: the measured Ollama completion is approximately
100–110 seconds while the local default timeout is 30 seconds. `Not applicable
in cloud`: Cloud Run cloud mode has no reachable localhost Ollama fallback.
Both halves remain explicit; the cloud half is not treated as a defect.

### RISK-0013

`Open`: Firecrawl credit fields remain unverified. No new Firecrawl call was
permitted or made in this phase.

### Secret rotation runbook

When operationally required and separately approved:

1. Add a new version to the existing approved Secret Manager secret name.
2. Point the service revision/configuration at the new version.
3. Verify readiness, grounded QA, MCP Origin checks, and the exact read-only
   tool surface.
4. Disable the old version only after verification succeeds.

No rotation was performed and no secret value was read or recorded.

### Regression confidence

Executed with the required interpreter, bytecode disabled, pytest cache
disabled, and an external temporary directory:

```text
D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp D:\Research\vietragops_gate09rm_full_local_20260902
```

Result: `564 passed, 2 warnings in 276.94s`. Warnings were third-party
`websockets` deprecations. No source fix was made.

## M6 closure

### Mutation and cost receipt

- Product source and deploy files: unchanged.
- Pre-existing 29-path overlay: preserved; no stage, restore, delete, stash,
  reset, amend, rebase, or push occurred.
- GCP: no mutation; no API enablement, deployment, traffic change, IAM change,
  budget change, resource creation/deletion, or cleanup occurred.
- Groq: zero calls initiated by this phase; phase-attributable spend `USD 0.00`.
- Firecrawl: zero calls initiated by this phase.
- Secret values, billing identifiers, account identifiers, and keys were not
  recorded.

### Closure Receipt

| Record | Resolution |
|---|---|
| `_agent_ops/CURRENT_TASK.md` | Updated with Gate 09R-M completion, evidence limitations, preserved overlay, and maintenance-only next action. |
| `_agent_ops/IMPLEMENTATION_LOG.md` | Appended M0/M1/M2/M3/M4/M5 evidence, the full local-suite result, and the no-mutation boundary. |
| `_agent_ops/SESSION_BRIEF.md` | Updated with current Gate 09R state, one authoritative `Last Verified Commit`, historical separation, and the 09R-M receipt. |
| `_agent_ops/PROJECT_CONTEXT_CARD.md` | Not needed: pre-existing dirty overlay preserved; current observation and limitations are recorded here. |
| `_agent_ops/DECISION_LOG.md` | Updated with new `DEC-0028` for the bounded observation and reconciliation decision. |
| `_agent_ops/RISK_REGISTER.md` | Not needed: pre-existing dirty overlay preserved; RISK-0013 and the local/cloud split of RISK-0015 are recorded in this result, with no new risk identifier required. |
| `_agent_ops/REPO_MAP.md` | Not needed: dirty copy preserved; regeneration was proposed only. Fresh generator output remains at `D:\Research\vietragops_repo_map_gate09r_2d775ee_final.md`. |
| `_agent_ops/INDEX.md` | Not needed: read order did not change. |
| `gates/baselines/GATE_09RM_PROTOCOL.json` | Written and frozen with the SHA-256 recorded above. |
| `gates/results/GATE_09RM_RESULT.md` | Written as this read-only observation receipt. |

## Limitations

1. Current billing budget/cost could not be refreshed without a signed-in
   Console session or reading a prohibited billing identifier.
2. Authenticated API readiness and current cloud MCP behavior could not be
   refreshed because identity-token acquisition failed.
3. Public web question/refusal flows could not be submitted because the
   single-tab Streamlit UI did not load its question widget modules.
4. Disabled resource APIs limited independent enumeration of compute, SQL,
   GKE, Tasks and commitments. No mutation was attempted to improve visibility.
5. The API rollback candidate's zero allocation was not directly emitted by the
   selected live traffic projection; it is retained only as the prior 09R
   assertion, not a new observation.

## Exact next action

Monitor the bounded GCP budget and Cloud Run behavior. Do not repair, deploy,
rotate, enable APIs, change budget, change IAM, refresh the rejected method,
start the original Gate 09, start Gate 10, or stage the overlay without a new
explicit approval and protocol. Stop here after this result artifact.

## Post-release correction — Gate 09R-C (2026-09-07)

The `375,000 VND` Cloud Run control recorded during Gate 09R-V is a derived
arithmetic half of the project-scoped `750,000 VND` budget, not a budget
object. No Cloud Run-scoped budget object exists, and the project budget has no
Cloud Run service filter. Only the project-scoped `750,000 VND` budget is
enforced. Creating a service-scoped budget would be a GCP mutation requiring
separate approval; none was proposed or executed.

Current billing spend remains unobservable through the read-only budget
configuration path. The only identified paths are an interactive Console
sign-in or a billing export; the latter is a mutation with its own cost.
Neither path was authorized or executed in Gate 09R-C.
