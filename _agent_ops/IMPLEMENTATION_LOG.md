# Implementation Log / Nhat ky trien khai

Append-only. Add a new entry for each meaningful task or phase.

## Entry Template

### Date

`YYYY-MM-DD`

### Phase / Task

`<phase or task name>`

### Files Touched

- `<file path>`

### What Changed

- `<change>`

### Why

`<reason>`

### Tests Run

```bash
<command>
```

### Results

`<pass/fail and evidence>`

### Bugs Found

- `<bug or none>`

### Root Cause

`<root cause if known>`

### Fix Applied

`<fix or none>`

### Git Commit

`<hash or not committed>`

### Push Result

`<pushed/not pushed/not applicable>`

### Remaining Risks

- `<risk>`

### Next Step

`<next concrete task>`

---

## 2026-09-10 — Gate 15 B0 metric audit and no-control decision

- Recorded DEC-0038: no Groq key and no alternate control provider. Gate 12-V's
  frozen OpenRouter run is the within-provider before/after reference. No Groq
  spot-check and no generation request were made.
- Read the exact frozen metric: NFKC + whitespace collapse + casefold + Unicode
  `\\w+` tokenization, multiset token-F1, threshold `0.45`. Vietnamese
  diacritics are retained; numeric padding is not normalized.
- On the 36 answerable rows, 28 contain a number in the answer or expectation;
  `token_f1('07','7')` and `token_f1('02','2')` are both `0.0`, while numeric
  canonicalization makes both `1.0`. Ten rows begin with the exact
  `Theo ngữ cảnh đã truy xuất,` prefix; stripping it changes mean F1 by only
  `+0.006638` on those rows. Numeric normalization changes the all-row mean
  from `0.223210` to `0.226775`; both corrections together produce
  normalized-F1 mean `0.228619`.
- Verbosity is materially confounded: among 24 non-empty answers, Pearson
  correlation between answer token length and raw token-F1 is `-0.686026`.
  Mean raw F1 by increasing length bins (n=6 each) is `.561286`, `.455518`,
  `.219279`, `.103174`.
- Hand-adjudicated all 36 answerable rows: `18 correct`, `2 partial`, `4 wrong`,
  `12 refused`. The frozen automated decision is `7/36`; all seven are
  human-correct, but 11 human-correct rows fall below `0.45`, producing
  disagreement `11/36 = 30.6%` and zero false positives.
- Proposed corrected audit metric, written before applying it: canonicalize
  numeric runs (`07 -> 7`) and strip the exact boilerplate prefix, then report
  both symmetric normalized token-F1 and expected-token containment recall.
  Containment is diagnostic only until validated: it overcredits verbose wrong
  answers such as `dev_q008` and `gold_credit_requirement_023`.
- Arithmetic checkpoint: perfect generation cannot exceed the dense top-10
  retrieval ceiling `88/116 = 75.86%`, which is above the frozen `70%` bar in
  principle. Applying the observed Gate 12-V conversion ratio
  `0.194444/0.612069 = 31.8%` projects only `24.1%` at the new ceiling;
  Nemotron served-only correctness was independently `6/25 = 24.0%`. B4 is
  therefore not expected to reach `70%` under observed provider behavior.
- Full suite after the B0 audit artifacts passed `603 passed, 3 warnings` in
  `478.60` seconds with an external `--basetemp`; no source/test behavior
  changed in B0.

## 2026-09-10 — Gate 15-B B4/B5 paired OpenRouter run

- Frozen B4 protocol `gates/baselines/GATE_15B_PROTOCOL.json` before live
  requests. Final protocol SHA-256 is
  `sha256:149267d11811f86c5c4af39a3a35daf43eb160ff9a1b6e69ec6219054a3cdf8c`;
  protocol commits are `548bc6a`, `a613412`, and `f0c778d`.
- The valid retry reused the exact Gate 12-V 40-question sample and issued 64
  POSTs; a discarded first artifact pass issued 61 POSTs before record-file
  corruption was detected. Total accounting is `125/200`; paid spend is zero.
- B1 wire proof: `max_tokens=2048` present on `64/64` requests; successful end
  timestamps and per-POST latency present on `64/64`. B2 proof: 16 fallback
  requests were issued, but Gemma served `0`; all fallback responses were
  rate-limited. Primary raw HTTP-200 502 count was 2 in the valid pass.
- B4 metrics: frozen token-F1 correctness `11/36`, hand correctness `20/36`,
  first-attempt schema validity `24/36`, citation validity `40/40`, grounding
  precision `13/49`, grounding recall `13/37`, p95 end-to-end latency
  `122820.192ms`, finish-length `17/64`, and `46` actual Nemotron response
  bodies / `0` Gemma.
- Hand disagreement rose to `13/36 = 36.1%` on the new run; the corrected
  metric remains unvalidated as an automated proxy. The unchanged thresholds
  mechanically produce NO-GO, recorded in DEC-0040. No deployment or push was
  made.
- Final full suite after B4 instrumentation passed `603 passed, 3 warnings` in
  `407.69` seconds with an external `--basetemp`.

## 2026-09-10 — Gate 16 generation tuning and fallback policy repair

- Entry protocol `GATE_16_PROTOCOL.json` was frozen and committed as `5cbc9ce`
  before any live provider call. Its canonical SHA-256 is
  `sha256:b84668c11c100309d7f7e3e91112143a3947e13813859565d16e6bf5c139e869`.
  Entry HEAD and `origin/main` matched `6124dfed`; the pre-existing overlay was
  exactly 25 paths and the index was empty. The external-basetemp baseline was
  `603 passed, 3 warnings` in `529.06s`.
- Offline token analysis measured Gate 12-V completion p95/max `5407/5941` and
  reasoning p95/max `2382/4552`; all 17 B4 length finishes were exactly
  `completion_tokens=2048`. The pre-registered cap candidate was `8192`.
- Current OpenRouter documentation and live model metadata were read. Nemotron
  advertised reasoning with `supported_efforts=[medium, low]`,
  `supports_max_tokens=true`, and `mandatory=false`; cfg3's explicit
  `effort=none` was accepted with zero observed reasoning tokens.
- G3 used 45 accounted POSTs: one aborted sparse-fallback request plus 44
  scored requests. The four pre-registered configurations included Gemma as a
  primary for the first time. cfg3 won the frozen ranking: zero length finishes,
  `8/8` schema, `6/8` hand correctness, reasoning p95 zero, and p95 latency
  `26292ms`; Gemma issued 16 rate-limited requests and served zero.
- Source/test repair was committed as `7e7da2c`; focused provider tests passed
  `35 passed, 1 warning`. The repair adds explicit reasoning configuration,
  upstream-only model fallback, same-model rate-limit retry, a process-global
  20-RPM governor, and dispatch-counted daily accounting. The recorder's G5
  mode was committed as `4a20e41`.
- Fresh G5 protocol `GATE_16_G5_PROTOCOL.json` was frozen and committed as
  `35cf218`, canonical SHA-256
  `sha256:c846d24a757c1b28c726b2f8a04bb0accbbb14dbbe6becda8e68006ff429f826`.
  The exact 40-question Gate 12-V sample was reused. G5 issued 38 POSTs, total
  Gate 16 accounting was `83/200`, and all requests were free.
- G5 carried `max_tokens=8192` and `reasoning={effort:none}` on `38/38` POSTs,
  produced `0/38` length finishes, `38/38` first-attempt schema, p50/p95
  latency `11624.887/30508.479ms`, raw 502/429 `0/0`, and no fallback request.
  Nemotron served 38 and Gemma served 0. Hand adjudication was `26 correct`,
  `0 partial`, `4 wrong`, `6 refused`; frozen and corrected automated binary
  correctness were both `13/36`, with `15/36` disagreement.
- Mechanical verdict is NO-GO: grounding precision `15/51`, grounding recall
  `15/37`, frozen correctness `13/36`, and p95 latency `30508.479ms` fail the
  unchanged thresholds. No deployment, GCP action, secret mutation, research
  write, dataset edit, or push occurred.

## 2026-09-10 — Gate 17 zero-provider audit of grounding, correctness, and latency

- Frozen `gates/baselines/GATE_17_PROTOCOL.json` before metric implementation
  analysis and committed it as `1f4c695a7e16869eb11d7814f96eca9a2046bedd`.
  File SHA-256 is `0a0eb13e5334c8ff6c1327171c3846e94041a29cde118b7235d6194e2a7b1c2f`.
  Entry HEAD and `origin/main` were both `9b47b20f`; the pre-existing overlay
  remained 25 paths and the index was empty.
- Read the existing Gate 16 G5 `cfg3.json` artifact only; no provider/GCP
  call, deployment, secret access, source change, corpus change, golden-set
  edit, retrieval change, or prompt change occurred.
- Reproduced the full suite with `.venv\Scripts\python.exe` and external
  `--basetemp`: `607 passed, 3 warnings` in `334.04s`. The warnings are the
  known websockets deprecations and the host pytest-cache ACL warning.
- Read `evals/metrics/gate12v_metrics.py`: grounding is exact per-row set
  membership of cited IDs against `relevant_chunk_ids`, with no chunk-text or
  quote-support check. On the 26 hand-correct Gate 16 rows, `32/47` cited IDs
  were outside the annotation; 31 support the answer and one fails. Corrected
  audited-surface grounding is `46/47` precision and `46/58` recall.
- Reapplied Gate 15-B0's numeric-run/prefix correction offline to the existing
  answers. Mean F1 changed `0.353517 -> 0.353705`, containment is `0.571149`,
  and binary correctness remains `13/36`; hand correctness is `26/36` with
  `15/36` disagreement (14 false negatives, one false positive). Automation
  remains diagnostic; hand adjudication is the corpus reference.
- Recomputed the existing latency distribution. Provider-attempted `n=38`
  has p50 `11641.421ms`, p90 `18004.007ms`, p95 `30508.479ms`, max
  `37275.189ms`; the registered p95 miss is noise-compatible under the frozen
  20,000-resample bootstrap (`16672.136–37275.189ms`). The named tail is three
  slow provider responses; no tuning was made.
- Gate 17 records CONDITIONAL-GO for the corrected audited measurement surface,
  not deployment authorization. RISK-0026 remains open for the owner's
  least-privilege IAM decision. Gate 16 and Gate 12-V findings remain preserved
  with addenda rather than rewritten.

## 2026-09-10 — Gate 18 deployment attempt and fail-closed rollback

- Froze and committed GATE_18_PROTOCOL.json before GCP mutation. The baseline
  suite was 607 passed, 3 warnings with an external basetemp; the 25-path
  overlay and empty index were preserved.
- Applied the approved web-runtime TokenCreator binding and the secret-level
  accessor binding required to bind OPENROUTER_API_KEY to the API runtime.
  Secret version metadata was checked without reading its value.
- Built API digest
  sha256:5a7cfaa2cfd8951678a5941d29310e2525620b05440ff202dc45ded269dc1ce3
  from a clean context containing six active embedding files. Registry image
  size grew from 445213143 to 646295489 bytes.
- Candidate tag verification proved OpenRouter Nemotron free generation,
  citations, refusal behavior, and stateless MCP Origin enforcement. The
  candidate /health then reported
  VectorSpaceMismatchError: persisted chunk ID order does not match the active
  chunk store because the baked artifact represented 695 chunks while the
  active GCS release contained 698.
- Gate 18 is NO-GO. No promotion occurred; traffic was restored to
  vietragops-api-00009-w5j at 100%. DEC-0044 and RISK-0043 record the
 artifact-delivery decision and required re-embedding boundary.

## 2026-09-11 — Gate 18-R corpus reconciliation, guard, and promotion

### Scope and entry

- Gate 18-R protocol `gates/baselines/GATE_18R_PROTOCOL.json` was frozen and
  committed as `f22748d` before any provider, build, deployment, or traffic
  action. Canonical SHA-256 is
  `sha256:edf957a3f970342317afe6b3c679467461ae85282aa512f86415f1b845ddf961`;
  file SHA-256 is `dad24d30b7271b9c0eacb83d014de1c158832f06d8e0175a411ccce3476a7155`.
- Entry `HEAD` and `origin/main` both matched
  `c337120cabc86011a75a1c857483b15d73462a1c`. The exact 25-path user-owned
  overlay and empty index were preserved.
- R0 full suite was `607 passed, 2 warnings` in `542.48s` with external
  basetemp. The prior 3-warning report is reconciled as a host ACL warning
  that did not recur; no warning was invented.

### Corpus and evaluation evidence

- Read-only GCS registry resolution selected active release
  `release-614e820190314e5d8cda4a9ac0308dee` with 698 chunks and 38 documents.
  Its chunk hash/content hash is
  `db15b93e533b4a8806b50fed14198f0eb58ff4f84a5dbb25f3e67b2f5ab26e70`.
- The local input and old artifact each contained the same 695 ordered IDs and
  hash `0510c68876fc4b9295ba9ffff86bd1816432233f9b265b272e6e26613ba7e130`.
  The exact GCS-only set is
  `cloud-policy_s001_c001`, `cloud-policy_s002_c001`, and
  `cloud-policy_s003_c001`; artifact-only set is empty; shared ordering is
  identical. The three rows are from valid parsed/reviewed/published
  `cloud-policy.pdf` content in the release, not content edited to fix a count.
- None of the 116 golden rows references those IDs. The prior Gate 14-R/15/16
  measurements used the 695-row local input. A temporary authoritative-set
  retrieval-only run through the Gate 14-R ContextBuilder reproduced E5 int8
  RRF `k=60`, top-10 `88/116` and `curriculum_structure=7/15`, so no generation
  rerun was authorized or needed.

### Implementation and local validation

- Added release-bundle validation and changed
  `scripts/compute_corpus_embeddings.py` to require an explicit verified
  release directory plus immutable model revision. The rebuilt metadata records
  release ID/object hashes, 698 rows, model
  `intfloat/multilingual-e5-small` revision
  `614241f622f53c4eeff9890bdc4f31cfecc418b3`, dimension 384, L2 normalization,
  and int8 precision.
- Rebuilt artifact: 6 files, `136,499,031` bytes, embedding hash
  `7d890f48c17645aacd33fb87973a14b8a61f9b8993e8ba5822d3c6197061e82d`, full
  command wall-clock `189.313s`. The raw local DenseRetriever status is
  `state=active`, backend
  `onnx:intfloat/multilingual-e5-small:int8_dynamic_weight`,
  `degradation_reason=null`.
- Added `scripts/verify_vector_artifact.py` and the mandatory Dockerfile guard;
  the verifier invokes the existing DenseRetriever vector-space contract rather
  than duplicating it. Host check time was `1.935s`. Five offline tests passed
  in `0.11s`, covering match, count, ordering, content hash, and model identity
  mismatch.
- Added `scripts/prepare_api_build_context.py` and documented explicit
  `.gcloudignore` handling. The first Cloud Build
  `ff211adb-3bed-45b9-a7b7-f20ad3c2f6dd` failed closed because gcloud excluded
  the ignored artifact. The corrected context upload contained 540 files,
  including all six artifact files and all three release files.
- Source/test/docs commit is `c32be31f5d08e74106ce134aaec8cd3f6dd98645`.
  Post-change full suite was `612 passed, 2 warnings` in `536.41s`; the five
  additional passes are the new contract tests.

### Deployment and production proof

- Successful Cloud Build `213d7506-f91d-4c82-88fb-637896ffea1b` passed the
  Dockerfile guard and produced API digest
  `sha256:a1a62f4b66e920b67e4d038ce037f066550678d9afc889c00a0124e43136074e`.
  Registry image size was `646,840,968` bytes versus `646,295,489` before,
  delta `545,479` bytes / `0.520 MiB`.
- Revision `vietragops-api-00021-teb` was deployed at 0% with tag `gate18r4`.
  Direct `/health` returned active ONNX and null degradation reason; raw
  `/health/ready` returned 698 chunks and 38 documents. ContainerHealthy was
  `13.64s`; first direct health request was `551.22ms`.
- Three grounded direct `/ask` probes returned HTTP 200, valid citations, and
  active ONNX; one privacy/unanswerable row returned HTTP 200,
  `refusal=true`, zero citations, and `insufficient_evidence`. MCP missing and
  wrong Origin returned 403; canonical Host plus exact web Origin passed
  initialize, tools/list, and authorized retrieve_context.
- Cloud logs recorded exactly four free Nemotron HTTP-200 requests with ledger
  remaining `999`, `998`, `997`, `996`; the first three were direct API probes
  and the fourth was the public UI probe. Observed ending ledger is `4/1000`
  used and `996` remaining. No fallback, Gemma serving, or paid spend occurred.
- After all 0% checks, traffic moved to `00021-teb=100%` in `5.843s`. Canonical
  API health/readiness remained green. The public web UI rendered live API mode,
  a grounded answer, confidence 100%, and three citation cards.
- `DEC-0045` records the authoritative-corpus/build-guard decision. RISK-0043
  is closed by the rebuild/guard/0%-proof evidence. RISK-0044 remains open for
  release coupling and records chunk-ID-keyed embeddings as future work only.
- No corpus, manifest, golden set, secret, IAM, scaling, quota, budget, billing,
  or research artifact was changed. No push occurred; the owner must push
  explicitly if desired.

## 2026-09-11 — Gate 19 oracle reachability, additive exclusion, diagnostic probe, and external evidence

- Entry O0 reverified HEAD/origin at `bfdbb60a6bed118d058712ccc63471c16c16ecd2`,
  exactly 25 pre-existing overlay paths, empty index, and the full suite at
  `612 passed, 2 warnings` in `497.84s` with the `.venv` interpreter and an
  external basetemp. The latest repository OpenRouter receipt remained the
  Gate 18-R observation of `4/1000` used and `996` remaining for its observed
  UTC day; Gate 19 did not claim a fresh provider-account balance.
- Frozen protocol `gates/baselines/GATE_19_PROTOCOL.json` was committed before
  Gate 19 analysis. The machine-readable rights declaration and reusable
  `research/gate19/auditor.py` were added with six explicit offline tests.
- The auditor independently reproduced `tool_replacement=10/35`
  `UNREACHABLE-TARGET-ABSENT`, five of 15 graded cases requiring `::` (10 pair
  records classified `UNREACHABLE-CONVENTION-UNOBSERVABLE`), and
  `argument_split=0/40`. It also found the same hidden `::` convention in
  `argument_merge` (`30/30` pair records across 15/15 cases) and a separate
  required-field scan with 15 boolean acknowledgement defaults and five
  credential approval literals not explicitly declared in the method surface.
- Additive oracle V1 retains 15 reachable `tool_replacement` pair items; its
  manifest records all 35 original items and excludes 20 unreachable items.
  No Gate 07 or Gate 08 artifact was edited, moved, regenerated, rescored, or
  overwritten, and no Gate 07/08 number was restated on the repaired set.
- Frozen V4/V4.1 extraction covered 85 effective baseline rows for the five
  hidden-join cases: zero literal `::`, three different-separator constructions,
  and 82 no-join rows. The raw extraction is preserved separately because it
  does not match the Gate 08 prose claim that some baselines guessed `::`.
- The bounded diagnostic probe used one catalog-qualified free Nemotron slug,
  no fallback, 3.2-second pacing, and exactly 60 generation requests. All
  60 stayed on the free slug; 57 JSON successes and 3 provider failures were
  recorded. `::` emission was `0/28` valid JSON in the hidden-`::` stratum and
  `0/29` in the arbitrary-separator stratum, so the sample is inconclusive for
  convention prior and remains diagnostic-only.
- Path A reviewed MCPEvol-Bench and DynamicMCPBench public releases. The
  obtained task/trace registers were not old/new contract-pair registers, so
  the Gate 19 auditor was not applied to them. Path B hand-verified 20
  `modelcontextprotocol/servers` commit-parent pairs; all 20 were reachable and
  none was unreachable. External validation of the local defect is therefore
  not established; the supported paper tier is a single-system case study with
  a reusable criterion.
- Frozen-input hash manifest `GATE_19_FROZEN_SOURCE_HASHES.json` covers 134
  Gate 07/Gate 08 protocol, result, raw-artifact, and code-surface files.
  Closure re-verification returned `UNCHANGED=134`, `CHANGED=0`, `MISSING=0`.

## 2026-09-11 — Gate 19-C contradiction resolution, scoreable surface, and Gate 20 cancellation

### Scope and integrity

- Gate 19-C protocol `gates/baselines/GATE_19C_PROTOCOL.json` was committed as
  `4e7a58f` before analysis. Its pre-registered test is a two-sided equal-size
  two-proportion normal approximation with alpha `0.05`, target power `0.80`,
  and practically meaningful absolute difference `0.20`. Gate 07 V3/V4 raw
  references were discovered and hashed in C0 addenda before extraction; the
  frozen Gate 07/08/19 inputs were not changed.
- C0 reverified HEAD/origin at
  `d80959824ee2059d0d0eb1cbfcb0f90681147e2d`, exactly 25 overlay paths, an
  empty index, and `612 passed, 2 warnings` with the `.venv` interpreter and
  an external `--basetemp`.

### Scientific analysis

- The Gate 19 auditor was rerun over all 310 argument-pair items and all 45
  required-field items; both family summaries and item records matched the
  frozen Gate 19 audit artifacts exactly. Across the 12 families, `260/310`
  pair items are reachable. `argument_split` is `40/40`; `tool_replacement`
  is `15/35`; `argument_merge` is `0/30`.
- The required-field audit classifies `consent_ack=true`, `honor_code=true`,
  and `payment_ack=true` as unobservable in 15/15 `added_required_field`
  cases, and `approval_status="approved"` as unobservable in 5/25
  `tool_replacement` required-field items. The argument-split required fields
  are derivable. Strict complete-call retention is `0/15` for both affected
  full-call families.
- The five RISK-0022 cases have frozen targets
  `CRS-021::TERM-01`, `CRS-005::TERM-03`, `CRS-007::TERM-02`,
  `CRS-007::TERM-02`, and `CRS-020::TERM-03`. Across 85 effective V4/V4.1
  rows there are zero literal `::` constructions, three different-separator
  constructions, 82 no-join rows, and zero first-attempt successes. The raw
  evidence supports the corrected explanation that Gate 08 attributed
  family-level successes to these cases without checking the raw rows; it does
  not support a `::` guessing claim.
- Power results under the committed rule are: `argument_split` retained `n=40`,
  MDE `0.2975`, power at `0.20` `0.4578`, required `n=90`;
  `tool_replacement` retained `n=15`, MDE `0.4348`, power `0.2300`, required
  `n=76`; pooled retained `n=55`, MDE `0.2503`, power `0.6029`, required
  `n=87`. The Gate 20 GO predicate fails all three surfaces.

### Decision and closure boundary

- DEC-0047 cancels Gate 20. The replacement recommendation is a separately
  authorized Gate 10 tier-(b) measurement paper with the reachability
  criterion/auditor, synthetic-benchmark unreachability evidence contrasted
  with Path B `20/20` reachability, and the corrected RISK-0022 finding.
- Post-change final suite reproduced `612 passed, 2 warnings` in `528.54s` with
  the `.venv` interpreter and an external basetemp, reconciling the C0 count.
- RQ3 remains pre-registered NEGATIVE under DEC-0023. No provider generation,
  cloud call, deployment, secret, production source, corpus, manifest,
  chunk-store, embedding, golden-set, Gate 07/08/19 frozen-artifact, Gate 20,
  or Gate 10 paper action occurred. No push occurred.

## 2026-09-11 — Gate 10 re-scoped measurement paper and arXiv preparation

### Scope and frozen protocol

- The owner re-scoped Gate 10 under `DEC-0048`: the original `BLOCKED BY GATE
  09 PASS` condition was written for a full evaluation, while this paper is a
  measurement and benchmark-validity paper. Gate 09 remains unauthorized and
  Gate 20 remains cancelled; neither was reopened.
- The superseded alignment title and rationale were preserved. The adopted title
  is `Unreachable Oracles: Ground-Truth Derivability in Synthetic Tool-Drift
  Benchmarks for LLM Agents`.
- `gates/baselines/GATE_10_PROTOCOL.json` was frozen and committed as `8a9cc4a`;
  its SHA-256 is recorded in the evidence ledger. The machine-readable ledger
  was completed with 44 claim entries and 20 artifact entries and committed as
  `d456a5d`.

### Paper and verification

- Related-work metadata and URL checks were recorded in
  `paper/REFERENCES_VERIFIED.json` at `1cc3e27`; the set covers evolving tool
  agents, tool/schema adaptation, API migration/software evolution, and MCP
  evaluation.
- The LaTeX source, inline bibliography, three generated PNG figures, hostile
  self-review, README, and arXiv preparation checklist were committed in the
  paper package at `4da7371`; the package pointer was then pinned in the
  documentation commit `4ad1baf`.
- The external-directory LaTeX check produced an 11-page PDF with figures and
  no fatal errors or unresolved citations after the second pass. The generated
  PDF and auxiliary files were not added to the repository.
- Final repository suite: `612 passed, 2 warnings` in `367.58s` using
  `.venv\Scripts\python.exe` and external basetemp
  `D:\Temp\vietragops-gate10-basetemp-20260911-02`.

### Integrity and hygiene boundary

- The claim-to-artifact audit returned `CLAIMS=44`, `ARTIFACTS=20`,
  `CLAIM_ERRORS=0`, and `ARTIFACT_ERRORS=0`; all listed artifact SHA-256 values
  and last-touch commits matched the ledger.
- The repository hygiene checker found pre-existing tracked public-corpus/data
  and generated-artifact policy debt, plus 1,254 filesystem findings; no cleanup
  was authorized. A filename-only secret-token/private-key pattern scan found
  zero matches. Email-shaped strings occur in pre-existing public data/code/ops
  files, so no categorical claim of global private-data absence is made beyond
  the Gate 10 package and its no-new-private-data boundary.
- No provider, GCP, deployment, IAM, Secret Manager, corpus, manifest,
  chunk-store, embedding, golden-set, frozen-artifact, reset, stash, clean,
  rebase, amend, force-push, or push action occurred.

## 2026-09-16 — Gate 22 manuscript v3.2: reproduction claim repaired and verified from a public clone

### What prompted it

Manuscript v3 was committed and tagged `gate22-paper-v3-20260914`, then pushed.
Verifying the tag by checking it out into a fresh worktree and running the
harness as an external reader would produced **exit 1**, not the exit 0 section 8
asserted. The v2 external review could not have found this: it read only the
package ZIP.

### Diagnosis

- Stage 2 reported 126 of 134 manifest entries mismatching. 87 were `MISSING`
  (the `gates/artifacts/` measurement archive, ~107 MB, excluded by a bare `*`
  in `gates/artifacts/.gitignore`, present at no tag); 37 mismatched purely
  through CRLF conversion on checkout; 2 more resisted both explanations.
- Stage 4 differed on exactly one key, `register_sha256` — a hash of the raw
  bytes of `GATE_19_EXTERNAL_MCP_PAIRS.json`, rewritten by the same conversion.
- The frozen manifest is internally mixed: 39 tracked entries were hashed in LF
  form and 8 in CRLF form, so no single repository-wide line-ending policy
  reproduces it. `GATE_07_PROTOCOL_V2.json` holds 389 CRLF and 4 bare LF and
  cannot be reconstructed from its blob by any `eol` setting.
- Root finding: the committed blobs of eight `gates/baselines/GATE_0*` artifacts
  did not hash to the values the frozen manifest records for them. The working
  tree matched, so every prior run passed. The freeze verified only on the
  machine that created it.

### Changes

- `.gitattributes` (new): pins exactly the 48 hash-asserted paths with `-text` —
  the 47 tracked frozen-manifest entries plus `GATE_19_EXTERNAL_MCP_PAIRS.json`.
  A blanket `* -text` was rejected; 191 of 602 tracked files hold CRLF on disk
  against an LF blob.
- Eight frozen Gate 07/08 protocol artifacts restored to their recorded bytes via
  `git add --renormalize` on explicit paths. Manifest not edited (DEC-0049).
- `scripts/reproduce_audit.py`: stage 2 separates CHANGED, MISSING-outside-archive
  (both hard failures) from MISSING-in-archive (reported `PASS (PARTIAL)` with the
  reason and count). Added `--require-full-manifest`. Summary reports
  `ALL AVAILABLE CHECKS PASSED` and names the partial stage.
- `REPRODUCE.md`: rewritten. It still documented 4 stages, 6 unit tests, a
  "Real-Version MCP Negative Control" and the v1 tag as canonical.
- `paper/main.tex`: section 8 rewritten to state stage by stage what a clone can
  and cannot verify; the integrity paragraph's "no frozen artifact was modified"
  claim corrected with the exception; a hostile question added in 7.4; the
  traceability table now carries four tags.
- `paper/README.md`, `paper/ARXIV_CHECKLIST.md`, `paper/CHANGES_AND_AUDIT.md`,
  `paper/EVIDENCE_LEDGER_ADDENDUM.json` (notes V11, V12) updated to match.

### Verification

| Check | Command | Result |
| --- | --- | --- |
| Public clone, `core.autocrlf=true`, at the v3.2 tag | `git clone https://github.com/Dat071104/vietragops.git` then `python scripts/reproduce.py` | exit 0; stage 2 `PASS (PARTIAL)` 47/134; stages 3, 4 bit-identical; stage 5 structural match |
| Clone, strict | `python scripts/reproduce_audit.py --require-full-manifest` | exit 1, as designed |
| Owner tree, default and strict | `python scripts/reproduce.py` | 134/134 `UNCHANGED`, exit 0 both ways |
| Blob-vs-manifest | per-path SHA-256 over `git show HEAD:<path>` | 47/47 match (was 39/47) |
| Restoration is content-neutral | parsed-JSON equality and LF-normalised byte equality, per file | identical, 8/8 on both |
| Package consistency | `scratchpad/verify_v31.py` | 52 passed, 0 failed |
| Manuscript build, read from `main.log` | three-pass `pdflatex`, MiKTeX 24.1 | 27 pages, 0 overfull, 19 underfull, 0 LaTeX warnings, 3 error-level `Infinite glue shrinkage`, 0 undefined refs |

The build was also run from the public clone's tagged `main.tex` to confirm the
submission source is the tagged source. Note that the `Infinite glue shrinkage`
messages appear only in `main.log`, never on stdout — earlier rounds counted them
from stdout and saw zero.

### Boundary

No provider, GCP, deployment, IAM, Secret Manager, corpus, manifest, chunk-store,
embedding, or golden-set action occurred. No measured value was recomputed; both
audit artifacts remain bit-identical. `information_rights.json` and
`GATE_19_FROZEN_SOURCE_HASHES.json` were not edited. The published tag
`gate22-paper-v3-20260914` was not moved or deleted. The 107 MB measurement
archive was not published — see RISK-0049, which remains open.

### Amendment, same day: version 3.2

The owner directed that section 8's offer of the archive "from the authors on
request" be removed, and left the publish-or-not decision to the agent. The
archive is not published: ~107 MB of raw request ledgers, traces and sqlite
router state, unaudited for private data, and publication is irreversible. No
claim depends on it.

Section 8 now states the public hash attestation instead — the SHA-256 and byte
size of all 87 undistributed entries are in the committed frozen manifest — and
says explicitly that this is weaker than shipping the bytes. The traceability
table was simplified from a row per attempt to the three tags that pin distinct
things, naming the two superseded pre-submission tags in one line.

Re-verified after the amendment: build unchanged at 27 pages, 0 overfull, 0
LaTeX warnings; 62 package-consistency checks pass (up from 52, adding checks
that no availability offer survives anywhere in the package); clone of the public
remote at `gate22-paper-v32-20260916` runs five stages and exits 0.

Commits: `773d54b` (harness and byte-exactness), `8ec5311` (manuscript v3.1),
`2cc6d81` (manuscript v3.2). Tags `gate22-paper-v31-20260916` and
`gate22-paper-v32-20260916`, the first superseded and retained. All pushed to
`origin/main`.
