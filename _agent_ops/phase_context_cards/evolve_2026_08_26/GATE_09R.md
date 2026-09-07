# Gate 09R — Product-only Release and Observation

**Status:** `PASS — product-only release` (closed 2026-08-31)
**Source:** `gates/results/GATE_09R_RESULT.md`,
`gates/baselines/GATE_09R_PROTOCOL.json`

## Objective

Operate and observe the deployed VietRAGOps product after Gate 08 NEGATIVE.
Reconcile durable ops memory with verified repository and Cloud Run reality.

## Controls

Read-only Cloud Run, IAM, Artifact Registry, Cloud Storage, Secret Manager,
budget and browser observations only. Keep the API private, the web public,
MCP read-only and Origin-validated, and preserve the 29-path dirty overlay.
No Gate 07/08 rerun, Gate 10, rejected-method revival, Firecrawl call, source
change, GCP mutation, secret-value access, or unapproved staging.

## Maintenance arc

The follow-on maintenance arc is complete:

- 09R-M — **COMPLETE**: read-only observation and ops-memory reconciliation.
  [Result](../../../gates/results/GATE_09RM_RESULT.md)
- 09R-V — **COMPLETE — CAPACITY**: verification-gap closure and web
  availability triage. [Result](../../../gates/results/GATE_09RV_RESULT.md)

Open risks: RISK-0024 and RISK-0025. No repair, scaling, deployment, IAM or
budget mutation, Gate 09/10 work, or OpenRouter migration is authorized here.

## Exit

The maintenance arc ends at its documentation result artifacts. Any new
resource, provider, domain, budget, scientific method, Gate 07/08 rerun, Gate
09 work, or Gate 10 work requires new approval.
