# Gate 09R Result — Product Release and GCP Deployment

Status: **BLOCKED**

## Decision

Gate 09R was rebased from original Gate 09 because Gate 08 closed NEGATIVE and
its cross-version alignment method was not adopted. This result covers only
independently evidenced product/runtime work. It does not rerun or rescore Gate
07/08, does not use the rejected method, and does not authorize Gate 10.

The gate is blocked before GCP foundation because the required local container
build and container health smoke could not run on this Windows host. The Docker
client is installed, but Docker Desktop and its service are not running; the
service start was denied and the Docker engine named pipe is absent. Creating
cloud resources before this local release gate closes would violate the frozen
protocol.

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

- Google account/project/billing/IAM preflight: not run because the local
  container release gate is incomplete.
- Chrome Google Cloud Console: not used.
- GCP resource creation/API enablement/billing changes: none.
- Groq calls: `0`; Firecrawl searches: `0`; Firecrawl scrapes: `0`.
- Secret values were never requested, read, printed, copied, or stored.
- No secret name/version/binding was changed.
- Image build, image digest, Cloud Run deployment, browser cloud E2E,
  durable-object restart proof, cloud MCP proof, and Cloud Run rollback: not
  run.
- Observed GCP spend: `USD 0`.

## Residual risks and limitations

1. Docker Desktop/service access must be restored before the local release
   candidate can be accepted. The Docker image is therefore not tied to a
   digest yet.
2. The Cloud Storage registry/release implementation is covered by deterministic
   in-memory contract tests only; no real bucket persistence or generation-CAS
   proof exists yet.
3. The private Firecrawl route is implemented and locally tested, but no live
   Firecrawl result was collected, so no authoritative-source or cloud web-import
   claim is made.
4. Existing pre-task dirty overlays remain user-owned and unstaged. The live
   remote SHA could not be refreshed because GitHub credential acquisition
   returned `SEC_E_NO_CREDENTIALS`.

## Exact next action

Start Docker Desktop with sufficient Windows permissions, then rerun the
container build and health smoke from source commit `dbcee18`. Do not create GCP
resources or make provider calls until that check passes. Resume at the frozen
Phase 3/4 boundary; do not create another project or raise any budget.

## Closure Receipt

| Record | Resolution |
|---|---|
| `_agent_ops/CURRENT_TASK.md` | Updated separately with the Gate 09R blocked state and next step. |
| `_agent_ops/IMPLEMENTATION_LOG.md` | Updated separately with implementation, validation, and Docker blocker evidence. |
| `_agent_ops/DECISION_LOG.md` | Updated separately with the Option A/GCS-only decision and blocked outcome. |
| `_agent_ops/SESSION_BRIEF.md` | Updated separately with the current Gate 09R closure and exact source commit. |
| `_agent_ops/PROJECT_CONTEXT_CARD.md` | Not updated: pre-existing dirty overlay preserved; result records the new evidence. |
| `_agent_ops/RISK_REGISTER.md` | Not updated: pre-existing dirty overlay preserved; Docker blocker is recorded in this result. |
| `_agent_ops/PHASE_ROADMAP.md` | Not updated: pre-existing untracked overlay preserved; no later gate authorized. |
| `_agent_ops/REPO_MAP.md` | Not regenerated in place: pre-existing dirty overlay preserved; refreshed copy was generated externally for analysis. |
| `_agent_ops/THIRD_PARTY_TOOLING.md` | Not updated: pre-existing dirty overlay preserved; no third-party provider call occurred. |
| `gates/baselines/GATE_09R_PROTOCOL.json` | Frozen and committed before implementation. |
| `gates/results/GATE_09R_RESULT.md` | This blocked result. |
