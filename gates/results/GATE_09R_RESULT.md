# Gate 09R Result — Product Release and GCP Deployment

Status: **PASS**

## Decision

Gate 09R is the frozen product-only rebase of the original Gate 09. Gate 08
closed **NEGATIVE**: its proposed cross-version alignment method was not
adopted. The original Gate 09 premise is therefore unsatisfied. This result
does not rerun or rescore Gate 07/08, does not use or advertise the rejected
method, and does not authorize Gate 10.

The Gate 09R product lane passed its frozen local, immutable-image, Cloud Run,
security, persistence, browser/API/MCP, provider-policy, cost-control, and
rollback criteria. The deployed behavior is independently evidenced product
behavior: version-aware retrieval, governed candidate/review/publish
lifecycle, citation display, typed refusal/failure states, and bounded
provider/web-import integrations. Deployment is not a claim that the rejected
scientific method passed, nor a blanket claim of production correctness.

The historical local-container blocker at `6402cbc` and the subsequent
read-only GCP-access blocker at `a0792a3` remain historical records. They were
resolved without changing the frozen protocol, changing ACLs, substituting a
project, or bypassing the dirty overlay.

## Frozen identity and provenance

- Protocol: `gates/baselines/GATE_09R_PROTOCOL.json`
- Protocol SHA-256:
  `F4C78F2E392D1BA55E030788E9255EB82944756DDB589316EC140008444C9E23`
- Protocol freeze/amendment tip: `f07d154`
- Validated runtime source commit:
  `2d775eeeeaa4958d782c664b4cb5f520427d362b` (`2d775ee`)
- Source change after the initial implementation commit `dbcee18` was
  limited to cloud MCP transport hardening and its integration test:
  `app/mcp/server.py` and `tests/test_cloud_mcp.py`. The cloud transport uses
  stateless JSON mode when Cloud Run IAM mode is active; local static-bearer
  mode remains unchanged.
- Gate 08 closure ancestor:
  `e43c932807aa2e49b0bd3df754e266ffc01446f6`
- Branch: `main`
- The validated Docker contexts were clean Git exports of the source commit;
  the working-directory overlay was never used as a build context.

## Scientific routing and scope

- Gate 08 status remains NEGATIVE.
- The Gate 08 method remains unadopted and absent from the production feature
  and public claim surface.
- No Gate 07 or Gate 08 provider rerun, tuning, recollection, or rescore was
  performed.
- No proposed-method result is presented as positive evidence.
- Gate 10 remains outside this task and is not authorized.

## Repository and dirty-overlay boundary

At the final source validation boundary, the Git index was empty. The known
pre-existing 29-path overlay remains user-owned, unstaged, and untouched; it
includes modified governance/context files, deleted skill scripts, and
untracked `_agent_ops`/phase-card/tool/test artifacts. The overlay was excluded
from every Docker build, Cloud Build submission, deployment image, and release
commit. Only the explicitly named Gate 09R result and agent-ops records are
eligible for the closure commit.

## Frozen architecture actually deployed

Option A was deployed:

- `vietragops-web`: public Streamlit demo only.
- `vietragops-api`: private FastAPI product API and private MCP endpoint.
- Web-to-API calls use a Cloud Run identity token; the web runtime has
  `roles/run.invoker` on the API service only.
- The API service itself has no `allUsers` invoker binding. Cloud Run IAM is
  applied to the whole API service; no path-level public/private split is
  assumed.
- Cloud MCP uses Cloud Run IAM plus exact Origin validation and stateless JSON
  transport for sequential requests at concurrency one. Only the read-only
  `document_status`, `index_status`, and `retrieve_context` tools are exposed.
- Cloud Storage is the durable store for originals, canonical documents,
  candidate artifacts, registry pointers, and release objects. Local files are
  ephemeral cache/scratch only.
- Cloud SQL, GPU, GKE, Qdrant, queues, workers, commitments, and subscriptions
  were not created.

## GCP foundation and controls

Read-only final preflight under the approved host identity confirmed:

- Project `vietragops-evolve-20260831`: `ACTIVE`.
- Billing enabled: `True`; no billing account identifier was recorded.
- Region: `asia-southeast1`.
- Required APIs present: `run.googleapis.com`,
  `artifactregistry.googleapis.com`, `cloudbuild.googleapis.com`,
  `storage.googleapis.com`, and `secretmanager.googleapis.com`.
  Thirty APIs were enabled at final inventory because unrelated pre-existing
  APIs were preserved; none were disabled by this task.
- Required IAM access was readable and the approved active-account owner
  binding matched without recording the account identifier.
- Artifact Registry repository: `vietragops`, Docker format, regional,
  immutable tags enabled. Cleanup policy deletes untagged images after 30 days
  and `ci-` tagged images after 30 days.
- Durable bucket:
  `gs://vietragops-evolve-20260831-vietragops-data`, uniform bucket-level
  access, object versioning enabled, seven-day soft delete, and bounded
  lifecycle rules for candidates, registry/snapshots, experiments, and
  source/release objects.
- Cloud Build staging bucket was auto-created by the approved build service;
  its seven-day lifecycle rule was applied. No unrelated bucket was modified.
- Runtime identities: `vietragops-api-runtime` and
  `vietragops-web-runtime`. The API identity has bucket object access on the
  approved bucket and secret access only on the two used approved secrets.
  The web identity has only API-service invocation access.
- Approved Secret Manager containers only: `GROQ_API_KEY` and
  `FIRECRAWL_API_KEY`; version `1` exists and is enabled for each. The two
  admin/static-auth secret names were not needed in private Cloud Run IAM MCP
  mode. No secret value was read, printed, copied, stored, or placed in an
  image or repository file.
- Target budget control: `750,000 VND`, thresholds `50%/80%/100%`, scoped to
  VietRAGOps Evolve. Target Cloud Run spend cap control: `375,000 VND`, the
  conservative local-currency control for the approved USD 15 target, with the
  same thresholds. The mistaken unrelated-project cap was removed after user
  confirmation; no unrelated budget was changed.

## Immutable build and deployment evidence

### Local image

- Clean export: `D:\Research\vietragops_gate09r_export_2d775ee_20260831_141333_444`
- Tag: `vietragops-gate09r-local:2d775ee`
- Command: `docker build --tag vietragops-gate09r-local:2d775ee .`
- Exit: `0`; cached dependency/base layers were reused.
- Base: `python:3.11-slim@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6`
- Local image ID:
  `sha256:cbd3697b96d1514afd232c3930a77e0f7ab6cc020766aa38e549a80c930cf3e5`
- Size: `443991584` bytes.
- This local image ID is not the Artifact Registry digest.

The exported context contained no `.env`, lifecycle database, uploads, caches,
tests, gates, `_agent_ops`, or user overlay. No secret-pattern hit was found.

### Cloud Build and registry

Both images were built from the exact validated source commit and deployed by
digest, never by `latest`:

- API tag:
  `asia-southeast1-docker.pkg.dev/vietragops-evolve-20260831/vietragops/api:git-2d775eeeeaa4958d782c664b4cb5f520427d362b`
  - Cloud Build: `efff1ea6-c850-4b2c-9c11-a3d294515ab3`, success.
  - Artifact Registry digest:
    `sha256:f037b8189c01c13f5c686079c8d3abe86381dcddc0f28950d2b99af4eb816e96`
- Web tag:
  `asia-southeast1-docker.pkg.dev/vietragops-evolve-20260831/vietragops/web:git-2d775eeeeaa4958d782c664b4cb5f520427d362b`
  - Cloud Build: `549c3dde-896a-4f4b-b0ef-ab3faad80be6`, success.
  - Artifact Registry digest:
    `sha256:6b7a68f20c17b47321cb94a37dcec13af01a39d9915652c9547efdb37eeb7d4f`

Cloud Build emitted only the known legacy-builder deprecation and pip
root-install warnings. No `.env` or secret value entered the build context.

## Cloud Run services and traffic

- API service URL: `https://vietragops-api-ohtmo6zgoq-as.a.run.app`
  - active traffic: `100%` to `vietragops-api-00009-w5j`;
  - image: API digest above;
  - private at the Cloud Run IAM edge;
  - `min=0`, `max=1` (within the frozen maximum of 2), concurrency `1`,
    timeout `300s`, generation 2, session affinity enabled;
  - `vietragops-api-rbk09r` is the tested no-traffic rollback candidate. It is
    the latest ready revision by creation order, but it does not receive
    traffic.
- Web service URL: `https://vietragops-web-ohtmo6zgoq-as.a.run.app`
  - active traffic: `100%` to `vietragops-web-00002-wp9`;
  - image: Web digest above;
  - public `allUsers` access;
  - `min=0`, `max=2`, concurrency `1`, timeout `120s`, generation 2.

The API image configuration pins cloud mode to Groq, disables localhost Ollama
fallback, uses the approved GCS bucket/release/registry pointer, requires the
exact API host and public web Origin for MCP, disables the protected probe
tool, disables dotenv loading, and references only secret versions by name and
version.

## Local validation evidence

Exact full-suite command:

```text
D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp D:\Research\vietragops_gate09r_full_local_2_20260831
```

Result after the `2d775ee` source fix: **564 passed, 2 warnings** in
`304.23s`. The warnings are third-party `websockets` deprecations. The
changed-container/MCP focus passed **24 tests, 2 warnings** in `69.62s`.

Additional checks:

- no-write AST parse for changed source/tests: passed;
- tracked/staged high-entropy secret scan: `0` hits;
- task-record personal-email scan: `0` hits;
- `git diff --check`: exit `0`;
- container contract, provider policy, Cloud Storage registry, lifecycle,
  Origin, and frontend identity-token tests: passed;
- `python -B -m compileall -q app rag frontend scripts tests`: the only
  failure was the known Windows ACL replacement error for
  `app/api/__pycache__/routes_documents.cpython-313.pyc` (`WinError 5`). It
  produced no syntax/assertion failure, and no cache was deleted or changed.

### Local container gate

The exact source export was run through the approved host Docker path because
the sandbox identity cannot access the host Docker named pipe. No ACL, Docker
profile, Windows service, process, or WSL setting was changed.

The container ran with an explicit `PORT=8080`, mock/offline provider mode,
dotenv disabled, no secret values, no mounted administrator profile, no
repository bind mount, no Ollama fallback, loopback-only host binding,
read-only root, and ephemeral `/tmp`. It ran as non-root `appuser`, listened on
the injected port, had zero restarts, and stopped cleanly with exit `0`.

- `/health/live`: `200`.
- `/health/ready`: `200`.
- grounded Vietnamese request: evidence and valid citation returned;
- unsupported request: refusal with `insufficient_evidence`;
- MCP missing authentication: `401`;
- MCP invalid Origin: `403`;
- image audit: no `.env`, lifecycle data, governance, tests, or skills;
- container logs: no secret, personal email, or private host path.

### Local API/browser/lifecycle

Against fresh public/synthetic fixtures, local API and browser checks passed:

- readiness, grounded Vietnamese answer, citation rendering, and refusal;
- MarkItDown valid PDF candidate with `parse_status=ok`;
- malformed-file rejection and invalid PDF-header/schema rejection;
- candidate isolation before publish;
- review/publish, second-version publish, retire, and rollback with the
  expected source/version/index markers;
- local MCP unauthorized and wrong-Origin rejection;
- local Streamlit API-only browser flow with visible `Live API mode` and no
  local fallback.

## Cloud browser/API/MCP and provider evidence

### Product browser and API

Fresh Chrome proof against the final public web service recorded:

- initial load errors: `0`;
- grounded Vietnamese flow errors: `0`; answer and Citation Cards rendered;
- refusal flow errors: `0`; refusal state rendered with no citations;
- the UI showed `Live API mode` for both flows.

The private API edge rejected unauthenticated `/health/live` with `403`.
An approved authenticated request to `/health/ready` returned `200` with
`status=ready`, `storage_backend=gcs`, `chunk_count=698`, and
`document_count=38`. Authenticated `/ask` returned Groq metadata with
`fallback_used=false` on the grounded public fixture. The displayed citation
resolved to the served source/version; it is not treated as proof of answer
correctness.

### MarkItDown and Firecrawl

- A normal PDF uploaded as `cloud-policy` entered candidate version
  `e7b682ea...` with parse success.
- A second valid PDF entered candidate version `664c2af...`; neither candidate
  changed retrieval before publish.
- A malformed PDF remained an unpublishable failed candidate with
  `malformed_pdf`; an invalid PDF header was rejected with
  `format_validation_failed`.
- Version 1 publish changed the index to `sha256:db15b93e533b4a88`.
  Version 2 publish changed it to `sha256:f08553194b76b815`. Version 2 was
  retired and rollback restored version 1 and
  `sha256:db15b93e533b4a88`.
- Firecrawl successful scrape count: `1`; search count: `0`; two blocked
  target attempts were classified before outbound access. The one successful
  scrape was restricted to `undergrad.tdtu.edu.vn`, stored as candidate
  document `web-88b8c28734c6c0199ae608b8` / version
  `b63dbb8a6eff49e2a04624180b1f0cbf`, and was not published. An
  `example.com` request returned `domain_not_allowlisted` without outbound
  access. Firecrawl adapter credit metadata remained `0.0`; no plan upgrade or
  recharge occurred.

### MCP security

- no Cloud Run/IAM authentication: rejected at the private edge;
- IAM-authenticated request without Origin: `403`;
- IAM-authenticated request with the wrong Origin: `403`;
- IAM-authenticated request with the exact configured public-web Origin:
  initialize, `tools/list`, `index_status`, and `retrieve_context` succeeded;
- final tool list was exactly `document_status`, `index_status`,
  `retrieve_context`; no admin, filesystem, URI-conversion, or rejected-method
  tool was exposed.

### Provider and failure policy

- Cloud product mode is provider-pinned to Groq with deterministic grounded
  fallback only. Cloud health reported Groq enabled and Ollama skipped/not
  available.
- A cloud request before the provider secret was bound returned the typed
  deterministic fallback; after secure secret-version binding, bounded Groq
  grounded QA succeeded without fallback.
- Deterministic provider-policy tests covered typed rate-limit/timeout/error
  handling, fallback metadata, and cloud Ollama policy denial without probing
  `127.0.0.1:11434`. The deployed image contains the same tested source.
- No provider fault injection was used to manufacture a paid timeout/429; the
  approved Groq budget was reserved for bounded functional QA.

## Durable persistence and CAS evidence

- GCS bootstrap release:
  `bootstrap-dbcee185a4a55583459da6b3bee691907bf3218a`.
- Bootstrap manifest SHA-256:
  `2211b9191dcdd767bbac1b078a9a2221e93ea17d7d82fbef017e4ce0f2c11c8f`.
- Bootstrap chunks SHA-256:
  `0510c68876fc4b9295ba9ffff86bd1816432233f9b265b272e6e26613ba7e130`.
- Final registry pointer generation:
  `1788175456987374`; active release id
  `release-614e820190314e5d8cda4a9ac0308dee`; registry metadata reported
  four versions with candidate/published/retired separation.
- A real-bucket immutable CAS probe wrote
  `experiments/gate09r-cas-probe-20260831.json` at generation
  `1788175895422903`; the second write was rejected by the immutable
  precondition. The live registry pointer was not overwritten.
- A new Cloud Run revision read the same GCS release/registry and returned the
  same ready index markers, proving the required state was not dependent on a
  local container filesystem.

## Rollback evidence

The frozen non-destructive procedure was executed:

1. captured healthy API revision `vietragops-api-00009-w5j` and API image
   digest;
2. deployed `vietragops-api-rbk09r` with no traffic and the same immutable
   image/config contract;
3. tested the candidate tag for health and authenticated Groq QA;
4. moved candidate traffic to `100%` and verified health/QA;
5. moved traffic back to healthy revision at `100%` and verified health/QA;
6. restored the final state: healthy `00009-w5j` at `100%`, rollback candidate
   at `0%`.

An invalid revision-target attempt failed before mutation and traffic remained
on the healthy revision. No revision or durable object was deleted, and no
in-flight destructive data mutation occurred.

## Failure matrix and not-run boundaries

| Case | Evidence and classification |
|---|---|
| cold start/capacity | Final browser load passed with zero errors. A transient Streamlit static-module `429` was observed only while two tabs saturated `max=2`, `concurrency=1`; it was classified as Cloud Run capacity behavior, not an answer failure, and the single-tab final proof passed. |
| provider timeout/429 | Typed adapter/router tests passed; no paid live fault injection was run. |
| cloud Ollama unavailable | Cloud mode health/config and policy tests confirm Ollama is skipped/denied; no localhost fallback is reachable. |
| Firecrawl failure/domain | Blocked target and non-allowlisted domain were typed without outbound access; approved domain scrape remained candidate-only. |
| malformed/invalid document | Malformed candidate and invalid PDF-header rejection passed. |
| invalid MCP auth/Origin | Private edge, missing Origin, and wrong Origin rejected with `403`; local static-bearer missing auth was `401`. |
| storage failure/CAS | Real GCS immutable write and generation/CAS conflict passed; local typed storage failure contracts passed. |
| stale/missing version | Candidate isolation, publish/retire/rollback, and version-aware index markers passed. |
| bad revision | Invalid traffic target failed without changing traffic; controlled rollback/restore passed. |

The only intentionally not-run live fault injection was a paid provider
timeout/429 simulation. It is not counted as a successful provider result.
No user secret, billing identifier, password, MFA value, payment data, or
private key was inspected.

## Cost and usage receipt

- Final billing overview for the exact project showed current total cost
  `0 VND` and target budget current usage `0.00 VND` at observation time.
- The approved target budget is `750,000 VND` with `50%/80%/100%` alerts; the
  approved Cloud Run control is `375,000 VND`. The USD 15 warning/stop policy
  remains in force; no ceiling was raised.
- Groq calls were limited to bounded synthetic/public-fixture functional QA
  and rollback verification, stayed within the approved USD 5 allowance, and
  no key value or provider credential output was retained.
- Firecrawl usage was `0` searches, `1` successful scrape, and `2` blocked
  attempts, within `25`/`100` limits and the single approved domain.
- No paid queue/worker, GPU, GKE, Cloud SQL, Qdrant, commitment, subscription,
  or automatic plan/recharge action occurred.

## Limitations and residual risks

1. `compileall` remains unable to replace one existing `.pyc` on this Windows
   checkout because of an ACL (`WinError 5`). No source syntax or test failure
   was found; a future host-maintenance window should repair that ACL without
   changing repository ownership or deleting caches blindly.
2. API `max=1` was selected within the frozen `max=2` ceiling to keep the
   stateless MCP request path deterministic at concurrency one. The web service
   can still experience capacity 429s under simultaneous cold-start pressure;
   the final browser flow passed after bounded warm-up.
3. Provider timeout/429 evidence is deterministic policy/adapter evidence, not
   a live paid fault-injection receipt. This gate makes no provider reliability
   or answer-correctness claim beyond the recorded bounded calls.
4. Firecrawl output remains candidate evidence and is not authoritative until a
   separately reviewed/published product decision. Citations show source
   resolution, not truth of an answer.
5. Billing dashboards can lag. The observed zero is a point-in-time receipt,
   not a guarantee of future zero cost; the frozen alerts and stop thresholds
   remain active.

## Exact next action

No further Gate 09R execution is required. Monitor the bounded GCP budget and
Cloud Run behavior; rotate the two approved provider secrets through Secret
Manager when operationally required without exposing values. Any new domain,
provider, resource, budget, scientific method, Gate 07/08 rerun, or Gate 10
work requires a separate approval and protocol.

## Closure Receipt

| Record | Resolution |
|---|---|
| `_agent_ops/CURRENT_TASK.md` | Updated with Gate 09R PASS, validated source `2d775ee`, final traffic state, and maintenance-only next action. |
| `_agent_ops/IMPLEMENTATION_LOG.md` | Appended final local/container, immutable build, GCP, provider, persistence, E2E, rollback, and cost evidence. |
| `_agent_ops/SESSION_BRIEF.md` | Updated with final Gate 09R state and the closure commit pointer. |
| `_agent_ops/PROJECT_CONTEXT_CARD.md` | Not needed: pre-existing dirty overlay preserved; final gate evidence is recorded in the result and implementation log. |
| `_agent_ops/RISK_REGISTER.md` | Not needed: existing overlay preserved; residual risks are recorded in the result and no new risk identifier is required for closure. |
| `_agent_ops/PHASE_ROADMAP.md` | Not needed: pre-existing untracked overlay preserved; no later gate is authorized. |
| `_agent_ops/REPO_MAP.md` | Not regenerated in place: pre-existing dirty overlay preserved; fresh generator outputs were written to `D:\Research\vietragops_repo_map_gate09r_2d775ee_final.md` and `D:\Research\vietragops_code_index_gate09r_2d775ee_final.json`. |
| `_agent_ops/DECISION_LOG.md` | Added the final Gate 09R product-only PASS decision and its evidence boundary. |
| `_agent_ops/THIRD_PARTY_TOOLING.md` | Not needed: no tooling policy changed; bounded provider use is recorded in the result/log. |
| `gates/baselines/GATE_09R_PROTOCOL.json` | Not changed: frozen protocol and SHA-256 remain unchanged. |
| `gates/results/GATE_09R_RESULT.md` | Updated from BLOCKED to PASS using the new local, cloud, security, persistence, cost, and rollback evidence. |
