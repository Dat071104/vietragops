# Risk Register / Danh sach rui ro

| Risk ID | Severity | Likelihood | Area | Description | Mitigation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| RISK-0001 | High | High | Ingestion | Upload/index is a placeholder rather than a governed document lifecycle | Implement validate -> provenance/version -> parse -> chunk -> candidate index -> review -> atomic publish/retire, with integration tests | Open |
| RISK-0002 | High | High | Security | No authentication/authorization was found in the supplied audit | Add role checks before exposing upload, index, eval, debug and source-management operations | Open |
| RISK-0003 | High | Medium | Upload safety | Filename/path, type, size and storage-boundary controls are incomplete or unverified | Enforce basename/path normalization, allowlists, size limits, checksum/deduplication and bounded storage | Open |
| RISK-0004 | Medium | High | Runtime/index | Default runtime is a static JSONL/in-memory store with process-cache limitations | Stabilize the file-backed contract first; add durable/versioned index only when requirements justify it | Open |
| RISK-0005 | High | Medium | Source trust | Citation support does not establish freshness, legal/operational validity or conflict resolution | Add source version, effective dates, supersedes links, review state and explicit conflict handling | Open |
| RISK-0006 | High | Medium | Evaluation | Small or historical QA/benchmark claims may not support production safety or answer correctness | Use versioned, human-curated, lane-specific datasets and separate citation verification from answer correctness | Open |
| RISK-0007 | Medium | Medium | Reproducibility | Dependency/runtime and live provider/Docker/browser status are not current proof | Establish a supported environment, lock path and rerun deterministic checks before redesign claims | Open |
| RISK-0008 | Medium | Medium | Frontend | Broad silent fallback can hide API/runtime failures | Show mode and failure reason clearly while retaining a friendly fallback | Open |
| RISK-0009 | High | Medium | Credentials/quota | A multi-account borrowed-key pool could expose secrets and be used to evade provider account or quota controls | Preserve single-authorized-key current contract; do not store/rotate pools; use provider-compliant capacity decisions | Mitigated for setup; revisit only in Gate 05 |
| RISK-0010 | High | Medium | Firecrawl self-hosting | The source-aligned local stack is unauthenticated by default and does not itself prove persistence, backup, TLS or public safety | Keep it localhost-only and configuration-validated; require explicit security/deployment design before `up` outside local gate tests | Controlled setup only |
| RISK-0011 | High | High | Program governance | Installed tools or proposal prose may be misreported as integrated, tested or a passed gate | Use the Evolve tracker, result artifacts and hard STOPs; record tool preparation separately | Open |
| RISK-0012 | Medium | Low | Web import (SSRF boundary) | Firecrawl's own hosted infrastructure re-resolves an approved URL independently at fetch time; an attacker controlling authoritative DNS with a very short TTL could in principle return a public address for our pre-check and a private/metadata address moments later for Firecrawl's actual fetch (TOCTOU/DNS-rebinding). This app cannot pin the IP Firecrawl itself connects to. | Keep the domain allowlist narrow and owner-reviewed (currently one domain); do not treat this app's pre-check as a substitute for Firecrawl's own egress controls; revisit if Firecrawl exposes IP-pinning or an allowlist-enforcement option. | Accepted (SaaS-boundary limitation, Gate 03) |
| RISK-0013 | Low | Medium | Web import (provenance completeness) | The real Firecrawl scrape response used in Gate 03's live proof did not surface `credits_used` or an action/job id under the header/field names `rag/ingestion/firecrawl.py` looks for (`x-credits-used`/`x-firecrawl-credits-used` header, top-level `id`); both are recorded as `None` rather than fabricated. | Confirm the exact real field/header names against more live calls before relying on credit tracking for cost control; adjust the adapter's parsing then, not before. | Open (monitor before heavier Gate 04+ usage) |

## Web Import Scope Correction (Gate 03)

RISK-0010's mitigation ("keep localhost-only and configuration-validated")
still holds: Gate 03 did not start the Firecrawl self-host Compose stack.
It used the hosted `api.firecrawl.dev` API instead, with the safety
controls described in RISK-0012/RISK-0013 above.

## Scope Note

These entries summarize unresolved risks in the supplied master context card. They are not a substitute for a fresh Gate 00 audit and should be revalidated before implementation.
