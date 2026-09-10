# Gate 18 — RISK-0026 closure and repaired product-lane deployment

## Verdict

**NO-GO — rollback retained.**

The IAM and authenticated API/MCP checks passed. The candidate OpenRouter
revision was built and reached Ready at 0% traffic, but the production ONNX
vector-space contract correctly rejected the baked corpus artifact:

- persisted embedding metadata/chunk IDs: 695 rows;
- active GCS release: 698 chunks;
- raw /health degradation reason:
  ONNX: VectorSpaceMismatchError: persisted chunk ID order does not match the active chunk store;
- deployed backend: rrf(offline_bm25+sparse_semantic_fallback).

The candidate was not promoted. Final API traffic is 100% on the recorded
rollback revision vietragops-api-00009-w5j.

## Protocol and entry

- Protocol: gates/baselines/GATE_18_PROTOCOL.json
- Protocol SHA-256: C7A8959948190DC0B3B0407B37607188F27D1A3745EDE974DD4015FF78191030
- Protocol commits: e0a0507 and reconciliation d7e5af5
- Initial snapshot: HEAD/origin ed4c9d68c3856b00cb78b7a272c792761def5740
- Concurrent external docs-only remote commit discovered before mutation:
  dae57bcd1017ae6e97ce88dcb5728091b61536bd
- Final local HEAD: d7e5af5fd3aa907b8392c7fdcd79efd9480efd0c
- Final origin/main: dae57bcd1017ae6e97ce88dcb5728091b61536bd
- Suite: 607 passed, 3 warnings with external basetemp
- Overlay: exactly 25 paths, unstaged; index empty
- No push was performed.

## D1 — IAM

Applied and verified:

1. user:thanhvu.dat@gmail.com →
   roles/iam.serviceAccountTokenCreator on
   vietragops-web-runtime@vietragops-evolve-20260831.iam.gserviceaccount.com.
2. serviceAccount:vietragops-api-runtime@vietragops-evolve-20260831.iam.gserviceaccount.com →
   roles/secretmanager.secretAccessor on the OPENROUTER_API_KEY secret. This
   was required to bind the newly created secret to the API revision; it is
   secret-level only.

No secret value or identity token was printed, logged, or stored.

## D2 — Authenticated API, MCP, and RISK-0026

Identity-token impersonation succeeded with token output held in memory only.

Baseline API evidence:

- /health: HTTP 200
- /health/ready: HTTP 200
- three grounded questions returned HTTP 200 with valid citations;
- unanswerable laptop question returned HTTP 200 with refusal=true;
- MCP initialize: 200;
- MCP tools/list: 200 with exactly document_status, index_status,
  retrieve_context;
- authorized retrieve_context: 200, isError=false;
- missing and wrong Origin: 403.

The public web page rendered LIVE API MODE. Therefore the historical
API unavailable display was not merely an expected unauthenticated viewer
state. The evidence classifies it as an intermittent web-to-API/UI
availability degradation, consistent with the separately open RISK-0024
capacity/static-asset-429 observation. The authenticated path itself is now
proven.

## D3 — Artifact delivery and contract enforcement

Decision: bake artifacts into the immutable image.

Reason: Dockerfile uses COPY . /app; .dockerignore does not exclude
data/chunks/embeddings/active; a clean external build context was used to
avoid the Git-ignored artifact exclusion and the 25-path overlay.

Build receipt:

- Cloud Build: 495ca26a-05f3-4230-be12-c1f45e32a181
- context: 259 upload files, 137.2 MiB compressed source input
- active artifact files: 6
- active artifact bytes: 136,493,803
- new API digest:
  sha256:5a7cfaa2cfd8951678a5941d29310e2525620b05440ff202dc45ded269dc1ce3
- previous API digest:
  sha256:f037b8189c01c13f5c686079c8d3abe86381dcddc0f28950d2b99af4eb816e96
- registry image size before: 445,213,143 bytes
- registry image size after: 646,295,489 bytes
- measured delta: 201,082,346 bytes / 191.767 MiB

The deployed candidate health surface proved the vector-space guard is active.
It refused the stale artifact instead of serving dense results:

VectorSpaceMismatchError: persisted chunk ID order does not match the active chunk store

No forward repair was attempted. A fresh re-embedding of the active 698-chunk
GCS release is required before another deployment gate.

## D4 — Secret and configuration

OPENROUTER_API_KEY was created in Secret Manager with version 1 enabled.
The API revision received the secret reference without exposing its value.

Candidate non-secret configuration:

- LLM_PROVIDER=openrouter
- PROVIDER_MODE=cloud
- OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free
- OPENROUTER_MODEL_FALLBACK=google/gemma-4-31b-it:free
- OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
- OPENROUTER_REQUEST_TIMEOUT_SECONDS=90
- OPENROUTER_MAX_REQUESTS_PER_DAY=1000
- OPENROUTER_ALLOW_PAID_MODELS=false
- OPENROUTER_REASONING_EFFORT=none
- RAG_MAX_OUTPUT_TOKENS=8192
- PYTHON_DOTENV_DISABLED=true
- top_k=10 remains the validated code default; no ignored top-k environment
  variable was invented.

The candidate probe issued three successful free Nemotron generations. No
paid model was selected and no paid model call was observed. The runtime daily
ledger counter is not exposed by the health surface; its exact final counter
was not fabricated.

## D5 — 0% verification and rollback

Candidate revisions:

- vietragops-api-00016-wud: Ready, malformed first env-map attempt, 0%
- vietragops-api-00020-wib: Ready, correct OpenRouter env, 0%, tag gate18v3

Candidate gate18v3 verification:

- /health: 200; OpenRouter Nemotron free active
- /health/ready: 200
- three grounded answers: 200 with citations
- unanswerable question: 200 with refusal
- MCP initialize/tools/call: 200
- missing/wrong Origin: 403
- observed answer latencies: 21,455.34 ms, 6,011.15 ms, 5,618.63 ms

Despite generation/configuration success, D3 failed because dense retrieval was
not active. Promotion was therefore prohibited.

Final traffic:

- vietragops-api-00009-w5j: 100%
- rollback digest:
  sha256:f037b8189c01c13f5c686079c8d3abe86381dcddc0f28950d2b99af4eb816e96
- candidate tags remain at 0% for diagnosis only
- web remains vietragops-web-00002-wp9 at 100%

## Decisions, risks, and closure receipt

- DEC-0044: bake ONNX/vector artifacts into the image, but reject promotion
  until the artifact is regenerated against the exact active GCS release.
- RISK-0043: active GCS chunk-store changes can stale the baked vector artifact;
  corpus/release changes now require re-embedding, integrity verification, and
  redeployment.

Closure Receipt

- CURRENT_TASK.md: not needed; gate result and protocol carry durable state
- IMPLEMENTATION_LOG.md: appended Gate 18 NO-GO evidence
- SESSION_BRIEF.md: updated Gate 18 blocked next step
- PROJECT_CONTEXT_CARD: not needed; no durable architecture change
- DECISION_LOG.md: DEC-0044 added
- RISK_REGISTER.md: RISK-0043 added
- REPO_MAP.md: not needed; no source files changed

## Limitations

- No traffic promotion occurred.
- Public web post-promotion end-to-end verification was not run because the API
  candidate failed the dense-backend acceptance gate.
- The active GCS release was not modified.
- No corpus, manifest, golden set, chunk store, source code, or research lane was
  modified.
- No paid model or paid spend was used by the candidate probe.
