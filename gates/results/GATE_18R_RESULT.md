# Gate 18-R — Corpus reconciliation, build-time guard, and deployment retry

## Verdict

**PASS — authoritative GCS corpus reconciled, dense artifact rebuilt, build-time
guard enforced, and the API revision promoted after the 0%-traffic proof.**

The production corpus is the active GCS release with 698 chunks. The rebuilt
ONNX E5-small int8 artifact is bound to that release and the deployed health
surface proves the dense backend is active with no degradation reason. The
previous 695-row artifact was not reused.

## Protocol, source, and entry receipts

- Protocol: `gates/baselines/GATE_18R_PROTOCOL.json`.
- Protocol canonical SHA-256: `sha256:edf957a3f970342317afe6b3c679467461ae85282aa512f86415f1b845ddf961`.
- Protocol file SHA-256: `dad24d30b7271b9c0eacb83d014de1c158832f06d8e0175a411ccce3476a7155`.
- Protocol freeze commit: `f22748d` (`gate18r: freeze corpus reconciliation protocol`).
- Entry `HEAD` and `origin/main`: `c337120cabc86011a75a1c857483b15d73462a1c`.
- Protocol was committed before the source change, provider probes, build, or
  Cloud Run mutation.
- Gate 18-R source commit used for the image: `c32be31f5d08e74106ce134aaec8cd3f6dd98645`.
- Entry overlay: exactly 25 user-owned paths; index empty. The overlay was not
  staged, committed, reset, stashed, cleaned, or pushed.
- Interpreter: `.venv\\Scripts\\python.exe`.
- R0 suite: `607 passed, 2 warnings` in `542.48s` with external basetemp
  `D:\\Research\\vietragops_gate18r_r0_20260910_01`.
  The prior Gate 18 reference was `607 passed, 3 warnings`; this invocation
  emitted the two known websockets deprecations and did not emit the prior host
  pytest-cache ACL warning. No unobserved warning was added.
- Final post-change suite: `612 passed, 2 warnings` in `536.41s` with external
  basetemp `D:\\Research\\vietragops_gate18r_r4_20260910_01`. The `+5` is the
  five new vector-contract tests. A final closure rerun after the source commit
  completed `612 passed, 2 warnings` in `541.10s` with external basetemp
  `D:\\Research\\vietragops_gate18r_final_20260911_01`.
- No secret value was read, printed, logged, stored, or committed. One early
  auth-probe error handler accidentally included an ephemeral identity token in
  tool output after a `gcloud` warning was concatenated with the token; the
  token was not stored or reused, and no API secret was accessed. Later probes
  used a filtered in-memory token path.

## R0 — Live rollback target and configuration boundary

Project `vietragops-evolve-20260831`, region `asia-southeast1`.

### Rollback target

| Service | Revision | Digest | Traffic before Gate 18-R |
| --- | --- | --- | ---:|
| API | `vietragops-api-00009-w5j` | `sha256:f037b8189c01c13f5c686079c8d3abe86381dcddc0f28950d2b99af4eb816e96` | 100% |
| Web | `vietragops-web-00002-wp9` | `sha256:6b7a68f20c17b47321cb94a37dcec13af01a39d9915652c9547efdb37eeb7d4f` | 100% |

The prior Gate 18 candidate remained at 0%:
`vietragops-api-00020-wib`, tag `gate18v3`, digest
`sha256:5a7cfaa2cfd8951678a5941d29310e2525620b05440ff202dc45ded269dc1ce3`.

The API service was observed with its pre-existing `maxScale=1` and
`containerConcurrency=1`; the web service was observed with `minScale=0`,
`maxScale=2`, and `containerConcurrency=1`. No scaling or concurrency setting
was changed. Both services remained gen2.

The API environment names were read without values. Secret bindings were:

- `GROQ_API_KEY` -> Secret Manager `GROQ_API_KEY`, version `1`;
- `FIRECRAWL_API_KEY` -> Secret Manager `FIRECRAWL_API_KEY`, version `1`;
- `OPENROUTER_API_KEY` -> Secret Manager `OPENROUTER_API_KEY`, version `1`.

The web service had no secret bindings. The deployed API retained cloud mode,
GCS storage, the OpenRouter model chain, `reasoning={"effort":"none"}`,
`max_tokens=8192`, and the existing MCP cloud/origin configuration.

## R1 — Exact 695-versus-698 reconciliation

The active release was read from
`gs://vietragops-evolve-20260831-vietragops-data/registry/pointers/state.json`:

- active release ID: `release-614e820190314e5d8cda4a9ac0308dee`;
- chunks object: `releases/release-614e820190314e5d8cda4a9ac0308dee/chunks_500.jsonl`;
- manifest object: `releases/release-614e820190314e5d8cda4a9ac0308dee/manifest.csv`;
- release chunks SHA-256 and `ChunkIndexStore.content_hash()`:
  `db15b93e533b4a8806b50fed14198f0eb58ff4f84a5dbb25f3e67b2f5ab26e70`;
- manifest SHA-256:
  `80265185aa7e09f86bb676e8192ceb7973354b57147e1021344579f365bd2209`;
- release metadata file SHA-256:
  `1133138e7dfbf9cd310e0fcd30789c0be8dec1f82e91a203e5d37023db7b6950`;
- GCS release: 698 rows, 698 distinct IDs, 38 documents.

The old artifact and its local input were identical to each other:

- local input: `data/chunks/chunks_500.jsonl`, 695 rows and 695 distinct IDs;
- local input SHA-256 and `content_hash()`:
  `0510c68876fc4b9295ba9ffff86bd1816432233f9b265b272e6e26613ba7e130`;
- old artifact `chunk_ids.json`: 695 IDs, no duplicates;
- old artifact metadata `chunk_store_sha256`:
  `0510c68876fc4b9295ba9ffff86bd1816432233f9b265b272e6e26613ba7e130`.

### Set difference

GCS-only IDs:

1. `cloud-policy_s001_c001`;
2. `cloud-policy_s002_c001`;
3. `cloud-policy_s003_c001`.

Artifact-only IDs: **none**.

All 695 shared IDs have the same order. The filtered GCS shared sequence and
the artifact sequence both have 695 IDs, with zero differing positions. Thus
the failure was a count/set divergence, not an additional ordering divergence
among the shared rows.

### Differing chunks and source

Each differing row has `doc_id=cloud-policy`, `source_type=pdf`, empty
`source_url`, and title `cloud-policy`:

| Direction | Chunk ID | Heading path | Source document and reason |
| --- | --- | --- | --- |
| GCS only | `cloud-policy_s001_c001` | `cloud-policy` | `cloud-policy.pdf`, version `e7b682ea37aa42eaafe981bbc132d136`, source object `sources/original/e7b682ea37aa42eaafe981bbc132d136.pdf`; release contains the first parsed section. |
| GCS only | `cloud-policy_s002_c001` | `cloud-policy > 1. Scope` | Same `cloud-policy.pdf` version; release contains the second parsed section. |
| GCS only | `cloud-policy_s003_c001` | `cloud-policy > 1. Scope > 2. Checks` | Same `cloud-policy.pdf` version; release contains the third parsed section. |

The registry records this document as `cloud-policy.pdf`, `parse_status=ok`,
reviewed, published, and later selected again by a rollback event into active
release `release-614e820190314e5d8cda4a9ac0308dee`. The local static corpus has
37 documents and never contains `cloud-policy`; the GCS release has 38.

### Cause

This is **structural source divergence: a partial local corpus relative to the
active GCS release**. It is not a chunking change, not an ordering-only change,
and not a document ingested after the September 9 artifact build: the GCS
document was already present in the August 31 lifecycle history, while the
artifact was independently built from the local 37-document store. The
previous process had no binding between the local embedding input and the GCS
release.

## R2 — Authoritative corpus decision

Production authority is the active GCS release. The service is configured with
`VIETRAGOPS_STORAGE_BACKEND=gcs` and reads its active release through the GCS
registry, so the GCS release is the only corpus that can define production
retrieval without changing service behavior.

The three extra chunks are legitimate content in the active release, not an
accident established by this gate. The registry shows a valid parsed and
reviewed `cloud-policy.pdf` version and an explicit rollback selecting it. No
content was removed, added, or edited, and no rollback of the corpus was
authorized.

None of the 116 golden questions references any of the three differing IDs.
The golden file and all `expected_answer` and `relevant_chunk_ids` fields were
left unchanged.

## R3 — Evaluation/production corpus identity

The prior validated evaluations used the 695-row local input:

- Gate 14-R protocol `gates/baselines/GATE_14R_PROTOCOL.json` records
  `data/chunks/chunks_500.jsonl`, SHA-256 `0510c688...`, and the E5 int8
  top-10 result `88/116`, `curriculum_structure=7/15` in
  `gates/results/GATE_14R_RESULT.md`.
- Gate 15 protocol/result use the same frozen chunk path/hash and record the
  selected RRF `k=60`, top-10 result `88/116`, `curriculum_structure=7/15`.
- Gate 16 G5 protocol `gates/baselines/GATE_16_G5_PROTOCOL.json` records
  retrieval as ONNX E5-small int8, RRF `k=60`, top-10; Gate 16 result states
  retrieval was held fixed. Its generation artifact was therefore also
  produced against the 695-row local store.
- Gate 17 read the existing Gate 16 G5 artifact only, with zero provider/GCP
  calls; it did not change the corpus identity.

Because those inputs differed from production, a retrieval-only rerun was
required. A temporary 698-row int8 artifact was materialized outside the repo
and evaluated through the existing Gate 14-R product `ContextBuilder` path:

```text
output: D:\Research\vietragops_gate18r_r3_retrieval_20260910_01.json
backend: rrf(offline_bm25+onnx:intfloat/multilingual-e5-small:int8_dynamic_weight)
state: active
answerable: 88/116
macro recall: 0.758621
macro precision: 0.077586
MRR: 0.472876
curriculum_structure: 7/15
```

The three GCS-only IDs had zero intersection with the union of golden
`relevant_chunk_ids`. The retrieval ceiling and worst-slice result did not
change materially (they were identical), so no generation rerun or provider
budget decision was required.

## R4 — Rebuild receipt

`scripts/compute_corpus_embeddings.py` now requires `--release-dir` and
`--model-revision`; it no longer accepts an implicitly selected bare `--chunks`
input. `rag/retrieval/release_bundle.py` validates release identity, object
basenames, manifest/chunk hashes, unique IDs, manifest document IDs, and
`ChunkIndexStore.content_hash()` before materialization.

The rebuild used:

```text
.venv\Scripts\python.exe -B -m scripts.compute_corpus_embeddings \
  --release-dir D:\Research\vietragops_gate18r_corpus_20260910_01 \
  --encoder-dir data\chunks\embeddings\gate14r\multilingual-e5-small\int8 \
  --output-dir D:\Research\vietragops_gate18r_rebuilt_artifact_20260910_01 \
  --model-revision 614241f622f53c4eeff9890bdc4f31cfecc418b3 --batch-size 32
```

The model revision is the local Hugging Face snapshot used by the existing
export: `614241f622f53c4eeff9890bdc4f31cfecc418b3`.

Resulting metadata:

- model ID: `intfloat/multilingual-e5-small`;
- model revision: `614241f622f53c4eeff9890bdc4f31cfecc418b3`;
- dimension: `384`;
- normalization: `l2`, `normalized=true`;
- precision: `int8_dynamic_weight`;
- corpus release: `release-614e820190314e5d8cda4a9ac0308dee`;
- chunk count: `698`;
- `chunk_store_sha256`:
  `db15b93e533b4a8806b50fed14198f0eb58ff4f84a5dbb25f3e67b2f5ab26e70`;
- `chunk_ids_sha256`:
  `a9f3cb5522e428c6f7ba7e92c0e4c8370bd17a89572780dff7d6f968801742d2`;
- `embedding_sha256`:
  `7d890f48c17645aacd33fb87973a14b8a61f9b8993e8ba5822d3c6197061e82d`;
- six files, `136,499,031` bytes total (`130.18 MiB` using 2^20 bytes);
- embedding array: `1,072,256` bytes;
- full command wall-clock: `189.313s`; metadata materialization: `186.913s`.

The rebuilt artifact was copied into the ignored active artifact directory. A
raw local initialization against the copied artifact and the 698-row release
returned:

```json
{
  "backend_state": "active",
  "backend_name": "onnx:intfloat/multilingual-e5-small:int8_dynamic_weight",
  "status": {
    "name": "dense",
    "backend": "onnx:intfloat/multilingual-e5-small:int8_dynamic_weight",
    "state": "active",
    "degraded": false,
    "degradation_reason": null,
    "downgrade_reasons": [],
    "model_name": "intfloat/multilingual-e5-small",
    "onnx_artifact_dir": "data\\chunks\\embeddings\\active"
  }
}
```

## R5 — Build-time guard

`scripts/verify_vector_artifact.py` loads the explicit release bundle and
initializes `DenseRetriever` with the required model ID/revision. This invokes
the existing vector-space contract; it does not reimplement the ordered-ID,
row-count, hash, dimension, normalization, or model checks. It also checks the
artifact's release provenance metadata against the target release.

The guard was measured at `1.935s` for the matching 698-row artifact. The
successful build/deploy/promote sequence took `372.948 + 52.784 + 5.843 =
431.575s`, so the host verification was approximately `0.45%` of that cycle.
The full 189.313s rebuild is separate and is not hidden inside the guard.

Offline contract tests in `tests/test_vector_space_contract.py`:

- matching artifact: pass;
- count mismatch: fail (`persisted embedding row count does not match`);
- ordering mismatch: fail (`persisted chunk ID order does not match`);
- content-hash mismatch: fail (`persisted embeddings were generated from a different chunk-store content hash`);
- model-identity mismatch: fail (`persisted model identity ... != loaded query model ...`).

Receipt: `5 passed in 0.11s`.

The guard was also run through the complete image path. The Dockerfile now
requires `deploy/corpus-release/release.json` and runs the same verifier before
the image is finalized. `scripts/prepare_api_build_context.py` archives the
committed `HEAD` and injects only the verified release and ignored active
artifact into an external context.

The first build attempt (`ff211adb-3bed-45b9-a7b7-f20ad3c2f6dd`) intentionally
failed at this boundary because gcloud's generated default ignore rules
excluded the ignored active artifact. It did not produce a revision or traffic
change. An explicit external `.gcloudignore` was added with only `.git/` and
`.gcloudignore` exclusions. The upload list was then verified at 540 files and
included all six active artifact files plus all three release files.

## R6 — Artifact delivery and image receipt

The delivery mechanism remains immutable image baking. The successful context
was `D:\\Research\\vietragops_gate18r_build_context_c32be31_20260911_01` and
was built from committed source `c32be31f...`; no overlay path entered it.

Successful Cloud Build:

- build ID: `213d7506-f91d-4c82-88fb-637896ffea1b`;
- local wall-clock: `372.948s`;
- Cloud Build duration: `4M4S`;
- image tag:
  `asia-southeast1-docker.pkg.dev/vietragops-evolve-20260831/vietragops/api:git-c32be31f5d08e74106ce134aaec8cd3f6dd98645`;
- image digest:
  `sha256:a1a62f4b66e920b67e4d038ce037f066550678d9afc889c00a0124e43136074e`;
- registry image size: `646,840,968` bytes;
- prior Gate 18 image size: `646,295,489` bytes;
- measured image delta: `545,479` bytes (`0.520 MiB`).

The Cloud Build log itself shows the Dockerfile verifier returning `status=ok`,
698 chunks, the GCS chunk hash, model revision, and an active ONNX backend.

Cloud Run revision deployment:

- revision: `vietragops-api-00021-teb`;
- tag: `gate18r4`;
- direct URL: `https://gate18r4---vietragops-api-ohtmo6zgoq-as.a.run.app`;
- image digest: `sha256:a1a62f4b66e920b67e4d038ce037f066550678d9afc889c00a0124e43136074e`;
- deployment wall-clock: `52.784s`;
- deployed at 0% traffic.

Cloud Run revision conditions were all `True`: Ready message
`Deploying revision succeeded in 44.45s`, ContainerHealthy
`Containers became healthy in 13.64s`, and ContainerReady
`Container image import completed in 27.83s`. The first authenticated direct
`/health` request after deployment took `551.22ms`; this is the observed
scale-up/cold-request proxy, while the platform condition is the container
startup receipt.

## R7 — 0% proof, promotion, and post-promotion verification

### 0% direct health/readiness

The candidate `/health` raw response body was:

```json
{"status":"ok","groq_enabled":true,"deepseek_enabled":false,"llm_provider":"openrouter","llm_model":"nvidia/nemotron-3-super-120b-a12b:free","provider_mode":"cloud","ollama":{"available":false,"model_available":false,"base_url":"http://localhost:11434","model":"qwen2.5:3b","models":[],"error":"Skipped because active provider is not ollama."},"mcp_configured":true,"storage_backend":"gcs","retrieval_backend":"rrf(offline_bm25+onnx:intfloat/multilingual-e5-small:int8_dynamic_weight)","retrieval_status":{"name":"hybrid","backend":"rrf(offline_bm25+onnx:intfloat/multilingual-e5-small:int8_dynamic_weight)","state":"active","degraded":false,"degradation_reason":null,"components":{"bm25":{"name":"bm25","backend":"offline_bm25","state":"active","degraded":false,"degradation_reason":null},"dense":{"name":"dense","backend":"onnx:intfloat/multilingual-e5-small:int8_dynamic_weight","state":"active","degraded":false,"degradation_reason":null,"downgrade_reasons":[],"model_name":"intfloat/multilingual-e5-small","onnx_artifact_dir":"data/chunks/embeddings/active"}}}}
```

The candidate `/health/ready` raw response body was:

```json
{"status":"ready","index_version":"sha256:db15b93e533b4a88","chunk_count":698,"document_count":38,"storage_backend":"gcs"}
```

### 0% grounded/refusal probes

| Question | HTTP | Refusal | Citations | Citation verification | Backend | End-to-end latency |
| --- | ---: | ---: | ---: | --- | --- | ---: |
| `dev_q001` | 200 | false | 1: `ug_student_portal_guide_s001_c001` | true | ONNX active | `5439.86ms` |
| `dev_q003` | 200 | false | 1: `ug_student_email_guide_s001_c001` | true | ONNX active | `12408.45ms` |
| `gold_training_regulation_068` | 200 | false | 2: `ug_training_reg_k2020_html_s020_c001`, `ug_training_reg_k2020_pdf_s023_c001` | true | ONNX active | `11805.55ms` |
| `dev_q019` (answerable=false privacy row) | 200 | true | 0 | true; `evidence_state=insufficient_evidence` | ONNX active | `2041.08ms` |

All three grounded responses had `generation.provider=openrouter`,
`generation.model=nvidia/nemotron-3-super-120b-a12b:free`,
`fallback_used=false`, and no generation error. The refusal had no generation
block because guardrails stopped it before provider transport.

### 0% MCP cloud/origin proof

The tagged URL requires the canonical API Host header because the service's
existing `MCP_ALLOWED_HOSTS` is
`vietragops-api-ohtmo6zgoq-as.a.run.app`. With that Host plus the exact public
web Origin, stateless JSON MCP succeeded:

| Check | HTTP/result |
| --- | --- |
| missing Origin | 403 |
| wrong Origin `https://evil.example` | 403 |
| initialize, canonical Host + exact web Origin | 200; server `vietragops-mcp`, protocol `2025-03-26` |
| tools/list | 200; exactly `retrieve_context`, `document_status`, `index_status` |
| authorized `retrieve_context` | 200; `is_error=false` |

An initial exact-Origin request without the canonical Host header returned 421
from the existing Host allowlist. No allowlist or service configuration was
changed; the valid probe used the same canonical Host pattern as the existing
Gate 18 procedure.

### Promotion and after-state

Traffic sequence:

1. Before deploy: `vietragops-api-00009-w5j=100%`; candidate revisions 0%.
2. Deploy `vietragops-api-00021-teb` with `--no-traffic --tag=gate18r4`.
3. Verify health, readiness, three grounded probes, refusal, MCP, and latency
   at the tagged URL.
4. Promote with `vietragops-api-00021-teb=100%`; traffic update wall-clock
   `5.843s`.
5. After promotion: `00021-teb=100%`; `gate18v2` and `gate18v3` remain 0%.

Post-promotion canonical API verification returned HTTP 200 for both `/health`
and `/health/ready`, with the same active ONNX status and 698/38 readiness
identity. The public web UI was opened through the public URL and visibly
rendered `LIVE API MODE`. Submitting the email-structure question produced a
`LIVE API MODE • GROUNDED ANSWER`, confidence `100%`, the correct Vietnamese
answer, and three visible citation cards. This is the public UI end-to-end
receipt; the direct API refusal proof above remains the refusal receipt.

### OpenRouter ledger and cost

The `/health` schema does not expose the nested OpenRouter ledger. Cloud Run
logs for revision `00021-teb` recorded four dispatched generation requests,
all HTTP 200 and served by free Nemotron: `remaining=999`, `998`, `997`, then
`996`. The first three were the direct API grounded probes; the fourth was the
post-promotion public-UI grounded probe. The candidate therefore ended at
`4/1000` used and `996` remaining for the observed UTC day. No fallback request
was dispatched, Gemma served zero, and paid model selection/paid spend was
zero.

## R8 — Decisions, risks, and closure

- `DEC-0045` records the GCS authoritative-corpus decision and mandatory
  release-bound build guard.
- `RISK-0043` is closed with this evidence: the exact 698-row release was
  rebuilt, release/model/hash provenance was persisted, the shared contract
  passed locally and in Docker build, the 0% health surface reported active
  ONNX with no degradation, and the revision was promoted only after all
  checks.
- `RISK-0044` remains open for the corpus/artifact release-coupling class. A
  corpus release change now requires re-embedding and redeploying; a stale
  artifact is still a production failure mode if the release process is
  bypassed. The recommendation to key persisted embeddings by `chunk_id`
  instead of a positional array is recorded as future work: it would make
  reordering a non-event and leave genuine additions/removals as failures. That
  format change is deliberately not implemented in this deployment gate.
- RISK-0024 and the prior evaluation/annotation risks remain outside this
  gate. The local 37-document static store remains unchanged; future embedding
  builds must use an explicit verified release directory.
- No corpus content, manifest, golden set, expected answer, relevant IDs, or
  retrieval/generation tuning was changed.
- No unapproved GCP mutation occurred. Existing Gate 18 IAM and Secret Manager
  bindings were read only. No quota, budget, scaling, billing, service, or IAM
  mutation occurred in Gate 18-R.
- No push occurred. Local `HEAD` after closure is reported with the explicit
  commit list below; `origin/main` remains the entry
  `c337120cabc86011a75a1c857483b15d73462a1c`.

## Commit list and final receipt

Gate 18-R task-owned commits:

1. `f22748d` — freeze `GATE_18R_PROTOCOL.json` before mutation;
2. `c32be31` — release-bound embedding CLI, provenance loader, build verifier,
   Docker backstop, context preparation, model revision pin, documentation,
   and five offline contract tests;
3. `5070b2a` — result plus tracked decision/risk/implementation-log closure;
   the ignored local `CURRENT_TASK.md` and `SESSION_BRIEF.md` pointers were
   updated locally but intentionally not staged. No push follows.

Final closure must re-check the exact 25-path overlay and empty index after the
closure commit. The user-owned `_agent_ops/PROJECT_CONTEXT_CARD.md` and
`_agent_ops/REPO_MAP.md` overlays were intentionally preserved and are not
part of this gate's staged file set.

## Closure Receipt

- `CURRENT_TASK.md`: updated with Gate 18-R PASS, receipts, limitations, and next step.
- `IMPLEMENTATION_LOG.md`: appended dated Gate 18-R evidence.
- `SESSION_BRIEF.md`: updated current pointer; its Last Verified Commit row is
  not needed because no push occurred. Local HEAD and remote mismatch are
  reported above.
- `PROJECT_CONTEXT_CARD.md`: not needed; it is a pre-existing user-owned
  overlay and was preserved untouched.
- `DECISION_LOG.md`: updated with `DEC-0045`.
- `RISK_REGISTER.md`: updated by closing `RISK-0043` and adding `RISK-0044`.
- `REPO_MAP.md`: not needed; it is a pre-existing user-owned overlay and was
  preserved untouched.
