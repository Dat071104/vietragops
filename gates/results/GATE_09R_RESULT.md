# Gate 09R Result — Product Release and GCP Deployment

Status: **BLOCKED**

## Decision

Gate 09R was rebased from original Gate 09 because Gate 08 closed NEGATIVE and
its cross-version alignment method was not adopted. This result covers only
independently evidenced product/runtime work. It does not rerun or rescore Gate
07/08, does not use the rejected method, and does not authorize Gate 10.

The historical blocked result was recorded at commit `6402cbc` when the
sandbox identity could not reach Docker Desktop. That local blocker was
resolved through the approved host Docker path: the exact `dbcee18` source
exported cleanly, the local image built, and the container health/behavior
smoke passed. GitHub provenance was then verified at `4d6f363`.

The current execution is BLOCKED at the read-only GCP preflight. The approved
account is active, but it cannot access the exact approved project;
`gcloud projects describe vietragops-evolve-20260831` exited `1` with a
permission-denied-or-not-found response. Billing state and required IAM access
therefore cannot be verified. No cloud resource, API enablement, billing
change, secret, provider call, or substitute project was attempted.

## Frozen identity

- Protocol: `gates/baselines/GATE_09R_PROTOCOL.json`
- Protocol SHA-256: `F4C78F2E392D1BA55E030788E9255EB82944756DDB589316EC140008444C9E23`
- Protocol freeze/amendment commits: `81d650f`, `7c1feb0`, `c0892e1`,
  `d8584f6`, `93b0ec2`, `b11bf2e`, `f07d154`
- Implementation source commit: `dbcee18`
- Branch: `main`
- Gate 08 closure ancestor: `e43c932807aa2e49b0bd3df754e266ffc01446f6`

## Approved target, not deployed

- Project: `vietragops-evolve-20260831`
- Region: `asia-southeast1`
- Intended shape: public `vietragops-web` Streamlit service plus private
  `vietragops-api` FastAPI/MCP service.
- Intended durable store: Cloud Storage immutable objects and generation-CAS
  registry; Cloud SQL was explicitly excluded.
- Intended limits: min `0`, max `2` per service, concurrency `1`, no GPU.
- Cloud Run revisions, URLs, image digests, Artifact Registry objects,
  Storage objects, Secret Manager versions, IAM bindings, and budgets: none
  created or changed by this task.

## Local evidence

### Automated tests

Command:

```text
D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp D:\Research\vietragops_gate09r_full_local_2_20260831
```

Result: `563 passed, 2 warnings` in `298.11s`.

Focused cloud/runtime result: `61 passed, 2 warnings`; latest private
admin/Firecrawl/runtime focus: `45 passed, 2 warnings`.

Warnings are third-party `websockets` deprecations. No live provider or
Firecrawl call occurred during these tests.

### Static and contract checks

- No-write AST syntax check: passed for all 24 changed/new Python files.
- `git diff --check`: exit `0`.
- GCS release/registry CAS, cloud provider policy, Origin policy, frontend
  Cloud Run ID-token client, bounded retention files, and container-contract
  tests: passed.
- `python -B -m compileall -q app rag frontend scripts tests`: blocked by an
  existing Windows ACL error while replacing
  `app/api/__pycache__/routes_documents.cpython-313.pyc` (`WinError 5`). No
  assertion failure occurred, and the cache was not deleted or overwritten.

### Local container gate (R2/R3)

- Exact committed export: `dbcee185a4a55583459da6b3bee691907bf3218a`
  (`dbcee18`); build context was the exported tree, not the dirty checkout.
- Build command: `docker build --tag vietragops-gate09r-local:dbcee18 .`.
  Exit `0`; elapsed wall time was approximately `116s`; the base was
  `python:3.11-slim@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6`;
  no Docker build cache step was used. The build emitted only package-manager
  noninteractive/root warnings. Local image ID is
  `sha256:ab4cc2623d0ad127b576bc37d823f365c746c2de8fbbe01d952598db18e6c213`
  and size is `443990990` bytes; this is not an Artifact Registry digest.
- Smoke container ran with `PORT=8080`, mock provider mode, dotenv disabled,
  no secret values, no host bind mount, read-only root, an ephemeral `/tmp`,
  and `127.0.0.1`-only host binding. It ran as `appuser`, listened on the
  injected port, had zero restarts, and stopped with exit `0`.
- `/health/live` and `/health/ready` returned `200`; the grounded Vietnamese
  request returned evidence and a valid citation; the unsupported request
  returned refusal with `insufficient_evidence`; MCP missing authentication
  returned `401`; authenticated wrong-Origin returned `403`.
- Image audit found no `.env`, lifecycle files, `_agent_ops`, `gates`,
  `tests`, or `skills` in the image and no high-entropy secret/private-key
  pattern. The only textual `sk-` matches were redacted harmless fragments in
  a research identifier and historical log prose.
- Post-resume focused validation: `28 passed, 2 warnings` in `97.18s`;
  tracked high-entropy secret scan: `0` hits; task-record email scan: `0`
  hits; `git diff --check`: exit `0`.

### Live local API and browser

Against a fresh external test fixture, local Uvicorn API E2E passed:

- `/health/ready` returned `ready`;
- Vietnamese grounded answer returned a verified citation;
- unsupported fee question refused with insufficient evidence;
- valid MarkItDown PDF upload entered `candidate` with `parse_status=ok`;
- malformed PDF was rejected with `format_validation_failed`;
- candidate remained absent from retrieval until review/publish;
- v1 publish, v2 publish, retire, and rollback changed exact marker evidence
  as expected;
- MCP unauthenticated request returned `401`;
- MCP wrong-Origin request returned `403`.

Chrome browser E2E passed on the local Streamlit page in API-only mode: the
grounded Vietnamese answer and citation rendered, and the refusal rendered;
the UI displayed `Live API mode` and did not use local fallback.

## Cloud/provider execution

- Host `gcloud` account preflight: approved account matched; no credential
  value was recorded. Configured project and region were unset. The exact
  project lookup exited `1` because the approved account could not access the
  project (or it may not exist); billing-enabled state was blank and the
  read-only IAM permission test returned `0` granted permissions.
- Chrome Google Cloud Console: existing-tab connector timed out while claiming
  the heavy console tab; no browser mutation or account switch occurred.
- GCP resource creation/API enablement/billing changes: none.
- Groq calls: `0`; Firecrawl searches: `0`; Firecrawl scrapes: `0`.
- Secret values were never requested, read, printed, copied, or stored.
- No secret name/version/binding was changed.
- Artifact Registry image digest, Cloud Run deployment, browser cloud E2E,
  durable-object restart proof, cloud MCP proof, and Cloud Run rollback: not
  run.
- Observed GCP spend: `USD 0`.

## Residual risks and limitations

1. The exact approved GCP project is not accessible to the approved account;
   project existence, billing, and IAM cannot be verified.
2. The local image is validated but is not yet tied to an Artifact Registry
   digest; no cloud deployment can proceed until project access is restored.
3. The Cloud Storage registry/release implementation is covered by deterministic
   in-memory contract tests only; no real bucket persistence or generation-CAS
   proof exists yet.
4. The private Firecrawl route is implemented and locally tested, but no live
   Firecrawl result was collected, so no authoritative-source or cloud web-import
   claim is made.
5. Existing pre-task dirty overlays remain user-owned and unstaged. GitHub
   remote `main` was verified at `4d6f3634da9a1bce7c9e5732bd8d048ab94b7d4b`.

## Exact next action

Make the exact project `vietragops-evolve-20260831` accessible to the approved
account and ensure its approved billing/IAM state can be read without changing
the billing account or budget. Then resume the frozen GCP preflight in
`asia-southeast1`. Do not substitute a project, raise any budget, or make
provider calls before that access blocker is resolved.

## Closure Receipt

| Record | Resolution |
|---|---|
| `_agent_ops/CURRENT_TASK.md` | Updated separately with the GCP project-access blocker and resume condition. |
| `_agent_ops/IMPLEMENTATION_LOG.md` | Appended GCP preflight account/project/IAM blocker evidence. |
| `_agent_ops/DECISION_LOG.md` | Appended the GCP access STOP decision; prior local blocker remains historical. |
| `_agent_ops/SESSION_BRIEF.md` | Updated separately with the current BLOCKED state and exact current commit. |
| `_agent_ops/PROJECT_CONTEXT_CARD.md` | Not updated: pre-existing dirty overlay preserved; result records the new evidence. |
| `_agent_ops/RISK_REGISTER.md` | Not updated: pre-existing dirty overlay preserved; GCP access blocker is recorded in this result. |
| `_agent_ops/PHASE_ROADMAP.md` | Not updated: pre-existing untracked overlay preserved; no later gate authorized. |
| `_agent_ops/REPO_MAP.md` | Not regenerated in place: pre-existing dirty overlay preserved; refreshed copy was generated externally for analysis. |
| `_agent_ops/THIRD_PARTY_TOOLING.md` | Not updated: pre-existing dirty overlay preserved; no third-party provider call occurred. |
| `gates/baselines/GATE_09R_PROTOCOL.json` | Frozen and committed before implementation. |
| `gates/results/GATE_09R_RESULT.md` | Updated to BLOCKED from new GCP preflight evidence; `6402cbc` remains the historical local-Docker blocker result. |
