# Gate 09R GCP deployment runbook

This directory is a deployment contract, not permission to broaden the frozen
Gate 09R scope. The only approved project is
`vietragops-evolve-20260831`, in `asia-southeast1`. Do not substitute a
project, region, billing account, provider, domain, secret, or resource.

## Shape

- `vietragops-web`: public Streamlit demo.
- `vietragops-api`: private FastAPI service, governed lifecycle, version-aware
  retrieval, and MCP.
- Cloud Storage is the durable store for source objects, candidate artifacts,
  registry state, and immutable release bundles.
- Cloud SQL, GPUs, GKE, Qdrant, queues, workers, commitments, and subscriptions
  are excluded.

The YAML files are final-shape templates containing deliberate replacement
markers for image digests, the bootstrap release, and service URLs. Never
deploy a template containing `REPLACE_WITH_`.

## Preflight

Run from the repository root after local validation is green:

```powershell
$projectId = "vietragops-evolve-20260831"
$region = "asia-southeast1"
gcloud config set project $projectId
gcloud projects describe $projectId --format="value(projectId,lifecycleState)"
gcloud billing projects describe $projectId --format="value(billingEnabled)"
gcloud services list --enabled --project $projectId --format="value(config.name)"
```

Verify the active account visibly against the already approved account. Do not
write the account identifier to repository files, logs, screenshots, or
reports. If the project is unavailable, billing is disabled, or the account
differs, stop and ask the user. Do not attach another billing account.

Enable only the APIs needed by the frozen shape, after billing is confirmed:

```powershell
gcloud services enable `
  run.googleapis.com `
  artifactregistry.googleapis.com `
  cloudbuild.googleapis.com `
  storage.googleapis.com `
  secretmanager.googleapis.com `
  --project $projectId
```

Record the before/after enabled-API lists without recording credentials or
billing identifiers.

## Foundation

Create the regional Artifact Registry repository only if it does not already
exist:

```powershell
gcloud artifacts repositories create vietragops `
  --project $projectId `
  --location $region `
  --repository-format docker `
  --description "VietRAGOps Gate 09R images" `
  --immutable-tags
```

Create the bucket with uniform access and apply the bounded lifecycle policy:

```powershell
gcloud storage buckets create gs://vietragops-evolve-20260831-vietragops-data `
  --project $projectId `
  --location $region `
  --uniform-bucket-level-access
gcloud storage buckets update gs://vietragops-evolve-20260831-vietragops-data `
  --versioning `
  --lifecycle-file deploy/gcp/storage-lifecycle.json
```

Do not delete an existing bucket or change an existing retention policy without
stopping for approval.

Create dedicated runtime identities, if absent:

```powershell
gcloud iam service-accounts create vietragops-api-runtime `
  --project $projectId `
  --display-name "VietRAGOps API runtime"
gcloud iam service-accounts create vietragops-web-runtime `
  --project $projectId `
  --display-name "VietRAGOps web runtime"
```

Grant only bucket object access to the API identity. Grant Secret Manager
access only on the specific approved secret resources that are actually used.
Do not grant Owner, Editor, project-wide secret access, or service-account
private-key access.

Apply the Artifact Registry cleanup policy:

```powershell
gcloud artifacts repositories set-cleanup-policies vietragops `
  --project $projectId `
  --location $region `
  --policy deploy/gcp/artifact-cleanup-policy.json
```

## Secrets

Approved names are `GROQ_API_KEY`, `FIRECRAWL_API_KEY`, `MCP_AUTH_SECRET`, and
`VIETRAGOPS_ADMIN_AUTH_SECRET`. The private Cloud Run shape uses Cloud Run IAM
for API/MCP authentication, so the last two are not required by default.

Create secret containers by name only when needed. The user must enter secret
values through the Google Cloud Console or another secure local interface. The
agent must not request, read, print, copy, or store those values. Verify only
secret name, version existence, binding, and redacted metadata.

## Baseline release

After the validated source commit is known, upload the public baseline as one
immutable release. The command prints hashes and identifiers only:

```powershell
$sourceCommit = "<validated-full-source-commit>"
$releaseId = "bootstrap-$sourceCommit"
python scripts/gcs_bootstrap.py `
  --bucket vietragops-evolve-20260831-vietragops-data `
  --release-id $releaseId `
  --manifest data/manifests/documents_manifest.csv `
  --chunks data/chunks/chunks_500.jsonl `
  --source-commit $sourceCommit
```

The API must not start in GCS mode until this release exists.

## Build and deploy

Build from the exact validated source commit. Use an immutable Git tag and
record the resulting image digest. Do not use `latest`:

```powershell
$image = "$region-docker.pkg.dev/$projectId/vietragops/api:git-$sourceCommit"
gcloud builds submit --project $projectId --tag $image .
gcloud artifacts docker tags add $image `
  "$region-docker.pkg.dev/$projectId/vietragops/web:git-$sourceCommit"
gcloud artifacts docker images describe $image --format="value(image_summary.digest)"
```

Deploy the API privately with the limits in `api-service.yaml`: min `0`, max
`2`, concurrency `1`, timeout `300s`, no GPU. The first deployment may keep
MCP cloud mode disabled until the stable API host is known. Then deploy the
public web service with the API URL and
`VIETRAGOPS_API_AUTH_MODE=cloud_iam`. Finally redeploy the same API image digest
with:

- `MCP_CLOUD_IAM=true`;
- `MCP_REQUIRE_ORIGIN=true`;
- exact API host in `MCP_ALLOWED_HOSTS`;
- exact public web origin in `MCP_ALLOWED_ORIGINS`;
- `VIETRAGOPS_STORAGE_BACKEND=gcs`;
- `VIETRAGOPS_GCS_BOOTSTRAP_RELEASE=$releaseId`;
- `PROVIDER_MODE=cloud` and no localhost Ollama fallback.

Use `gcloud run services describe` and `gcloud run revisions list` after every
deployment. Record only service/revision names, image digests, traffic, and
redacted configuration metadata.

Grant the web runtime only `roles/run.invoker` on `vietragops-api`. Keep the
API service itself unauthenticated access disabled. IAM protects the whole API
service; it is not a path-level public/private split.

## Verification order

1. `/health/live` and `/health/ready`.
2. Public web page through Chrome.
3. Vietnamese grounded question and refusal behavior.
4. MarkItDown candidate upload and malformed-file rejection.
5. Review, publish, version-aware retrieval, retire, and rollback.
6. MCP missing-auth, wrong-Origin, and authorized read-only calls.
7. Firecrawl only through the approved domain and budget; every result remains
   candidate-only until review/publish.
8. Provider timeout/429 and cloud Ollama-disabled behavior.
9. New-revision persistence proof using the same durable release/registry.

If a secret value, new domain, new provider, higher cost, new resource, or
destructive cleanup is needed, stop and ask the user.

## Cloud Run rollback

Capture the healthy revision and image digest. Deploy the candidate revision
with no traffic, test its tagged URL, then move traffic to it. Move 100% of
traffic back to the healthy revision, verify the public web/API behavior, and
restore the intended final revision. Record before/after revision names,
traffic percentages, image digests, and in-flight request handling. Do not
delete revisions merely to demonstrate rollback.
