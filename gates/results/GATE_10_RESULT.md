# Gate 10 Result — Re-scoped Measurement and Benchmark-Validity Paper

**Date:** 2026-09-11  
**Status:** READY FOR OWNER REVIEW — NOT SUBMITTED  
**Tier:** (b) single-system case study with a reusable oracle-reachability criterion

## Protocol and scope decision

`DEC-0048` re-scoped Gate 10 from a full-evaluation paper to a measurement and
benchmark-validity paper. The original `BLOCKED BY GATE 09 PASS` condition was
written when Gate 10 was expected to report a full evaluation. The current paper
measures oracle reachability and benchmark validity; VietRAGOps Evolve is a
deployed case study, not the scientific result. Gate 09 remains unauthorized and
unchanged. Gate 20 remains cancelled under `DEC-0047`; this result does not
authorize it.

The adopted title is:

> **Unreachable Oracles: Ground-Truth Derivability in Synthetic Tool-Drift
> Benchmarks for LLM Agents**

The superseded title, its date, and the reason for replacement are preserved in
`DEC-0048` and `_agent_ops/RESEARCH_PLAN_PAPER.md` §1. The shorter candidates
were rejected because they did not satisfy all four owner conditions
simultaneously; the adopted title makes no alignment-method, new-benchmark, or
SOTA claim and remains valid under a 10% movement in reported values.

The frozen protocol is:

- path: `gates/baselines/GATE_10_PROTOCOL.json`
- commit: `8a9cc4a72197effacf530c87160be8045b7b8aeb`
- SHA-256: `725accbb050fe72654c0071746956f51a2b618787cd1ddc91aa652f52fc6fd5d`

## Evidence ledger

The machine-readable backbone is:

- path: `gates/baselines/GATE_10_EVIDENCE_LEDGER.json`
- commit: `d456a5dc487173bc43dac60fb2ca8026a1afa370`
- SHA-256: `6a71719d7256cffa13cad5ea20e27682120f556e9cb14580feb9b39cbd3a7489`
- coverage: 44 claim entries, 20 artifact entries

The ledger-to-filesystem audit returned:

```text
CLAIMS=44 ARTIFACTS=20
CLAIM_ERRORS=0
ARTIFACT_ERRORS=0
```

Every numeric result in the paper has a ledger entry with value, artifact path,
artifact commit, producing gate, and locator. Derived values are labelled as
derived. The ledger contains all-family reachability, the `10/35` and `5/15`
auditor findings, `260/310` and `50/310`, `0/30`, `15/35`, `40/40`, `0/20`,
`0/85`, zero first-attempt success, the diagnostic probe, the `P(::)=1/9`
baseline, the 146-hash integrity check, the power analysis, Wilson intervals,
and the RAG case-study figures.

## Paper and related work

The paper package contains:

- `paper/main.tex` — portable LaTeX source with inline bibliography;
- `paper/figures/figure1_problem.png` — the unreachable-oracle problem;
- `paper/figures/figure2_information_rights.png` — the information-rights table;
- `paper/figures/figure3_reachability.png` — all-family reachability and the real-pair control;
- `paper/ADVERSARIAL_REVIEW.md` — hostile self-review and resolutions;
- `paper/ARXIV_CHECKLIST.md` — categories, endorsement, license, and upload checklist;
- `paper/REFERENCES_VERIFIED.json` — nine verified references and license record.

Related-work citation verification is committed at:

- commit: `1cc3e27`
- SHA-256: `ed68073d69bf856ecc783721ce9abc2ec84d83ba5584881490a5056b22222592`

The paper distinguishes evolving-tool agents, schema/tool adaptation, API
migration/software evolution, and MCP evaluation. MCPEvol-Bench precedes this
paper; no first-benchmark claim is made. arXiv-only works are labelled preprints
and are not described as peer-reviewed.

## P4 adversarial review and resolutions

The paper and `paper/ADVERSARIAL_REVIEW.md` answer all required objections:

1. The criterion is positioned as an operational, rights-aware audit adjacent to
   test-set validity, not as a claim of a new validity theory.
2. The 20 real pairs are explicitly a purposive negative control, not external
   prevalence validation.
3. The self-authored sandbox is disclosed as a material generality limitation.
4. The cancelled Gate 20 campaign is a power/design decision, not a null method
   result; no repaired-lane comparative campaign ran.
5. The reusable criterion, auditor, typed statuses, information-rights table,
   independent reproduction, and evidence ledger distinguish the work from a
   deployment report.

The text uses `observe`, `measure`, and `report` for observational findings and
does not claim SOTA, first benchmark, peer review, external validation, or
generalization beyond the measured scope.

## Reproducibility and integrity

The public repository is `https://github.com/Dat071104/vietragops`. The
substantive paper package is reachable at commit
`4da7371fe7d414ba0e4f0064983c71e8c458fa8a`; the documentation pin and current
pre-closure checkout are `4ad1baf0b52e2f742b11318e1bc0116ec7b55206`.

The frozen Gate 07/08/19/19-C input manifest was reverified by Gate 19-C as:

```text
recorded hashes: 146
UNCHANGED=146
CHANGED=0
MISSING=0
```

No frozen artifact was edited, moved, regenerated, rescored, or overwritten.
The Gate 19 auditor, information-rights declaration, additive oracle, exclusion
manifest, real-pair control, protocols, ledger, and paper source are committed
and reachable from the local history. No provider, GCP, deployment, IAM, Secret
Manager, production source, corpus, manifest, chunk store, embedding artifact,
golden set, or external service action was used in Gate 10.

## Suite and hygiene

Final suite receipt:

```text
.venv\Scripts\python.exe -m pytest -q --basetemp=D:\Temp\vietragops-gate10-basetemp-20260911-02
612 passed, 2 warnings in 367.58s (0:06:07)
```

The hygiene checker passed the session-scoped `_agent_ops` tracking check but
reported pre-existing repository policy debt: tracked public corpus/data paths,
`.env` patterns, generated caches, databases, and other artifacts. The scan was
run with warning-only filesystem reporting; no cleanup was authorized. A
filename-only scan for common secret-token/private-key patterns found zero
matches. Email-shaped strings occur in pre-existing public data/code/ops files;
therefore this gate claims no new secret or private data in the Gate 10 package,
not a categorical global-private-data guarantee while the pre-existing hygiene
debt remains.

## arXiv preparation

The checklist recommends `cs.SE` primary with `cs.CL` and `cs.AI` cross-lists,
with `cs.CL` primary as an owner-approved alternative. It recommends CC BY 4.0
subject to author/funder/journal confirmation. arXiv's current official pages
were checked and recorded in `paper/ARXIV_CHECKLIST.md`:

- submission: `https://info.arxiv.org/help/submit/index.html`
- endorsement: `https://info.arxiv.org/help/endorsement.html`
- licenses: `https://info.arxiv.org/help/license/index.html`
- category taxonomy: `https://arxiv.org/category_taxonomy`

The author list, final license, final category choice, and actual arXiv
submission remain owner actions. Nothing was submitted.

## Limitations and readiness verdict

The substantive limitations are the self-authored sandbox, single-system scope,
small surfaces and wide intervals, RISK-0020's `0.9333` upper-bound versus the
`0.90` bar, RISK-0023 design-time exposure, the bounded 20-pair control, the
non-audit-compatible Path A, the RISK-0022 scorer/mechanism correction, and the
fact that the reachability criterion does not establish semantic equivalence.

**Verdict:** `READY_FOR_OWNER_REVIEW — SCIENTIFICALLY CLOSED FOR THE TIER-(B)
MEASUREMENT PAPER; NOT_READY_TO_SUBMIT`. The scientific package and evidence
traceability are complete. Submission remains intentionally pending the owner's
author, license, category, and final hygiene decisions.

No push occurred. At entry to final closure, local HEAD was
`4ad1baf0b52e2f742b11318e1bc0116ec7b55206`; `origin/main` remains
`f7f5d37d7a5539cc99657f557e18086a21034ed7`.
