# Gate 21 — Manuscript Delta (owner applies; this gate does not edit `paper/main.tex`)

Status: required delta for outcome D (`NOT AUDITABLE`). The current checkout at
entry `HEAD ff5e2b157ad218ff5e8dc652cbf06e6eef821522` was inspected. The
sentences below are quoted from the current `paper/main.tex`; line numbers are
source locators and may move if the owner edits the manuscript.

## Required changes

### 1. Evaluation Setting / Frozen evidence and controls (`paper/main.tex:133`)

Current:

> For external context, Path A inspected public MCPEvol-Bench and DynamicMCPBench releases but did not obtain an old/new contract-pair register compatible with this auditor. Path B uses 20 hand-verified parent/new MCP version pairs from the official MCP servers repository. Its machine-readable audit is `gates/results/GATE_19_EXTERNAL_AUDIT.json`, commit `c720ff2`; the pair register is `gates/baselines/GATE_19_EXTERNAL_MCP_PAIRS.json`, commit `0c73b17`. The Path B sample is purposive and is used as a negative control, not an estimate of real-world prevalence.

Required replacement:

> For external context, Gate 19 Path A inspected public MCPEvol-Bench and DynamicMCPBench releases but did not examine the four cumulative `evolution.json` files. Gate 21 pinned and surveyed those files at the resolved MCPEvol-Bench `main` commit, finding 487 tool-level records across 298 distinct `(server, tool)` pairs. The explicit `parameter_additions` surface contains 312 optional parameter items and 0 required parameter items. Under the separately declared MCPEvol-Bench agent rights, the adapter refused all 487 records: DESC and TOOL records are outside the frozen argument-target schema, while PARAM records lack a declared `task_idx`-to-expected-call target surface. The result is a feasibility finding, not an external unreachable-oracle rate or external validation. Path B continues to use 20 hand-verified parent/new MCP version pairs from the official MCP servers repository as a purposive negative control, not an estimate of real-world prevalence.

Add the Gate 21 artifact references and evidence-ledger entries when applying this
replacement. Keep the original Gate 19 and Path B artifact references; Gate 21
does not rescore or regenerate them.

### 2. Results / Synthetic defect versus real-version control (`paper/main.tex:158`)

Current:

> The real-version control contains 0/20 unreachable items. This contrast is informative but bounded: a purposive sample from one public repository can show that the auditor does not mark every evolution as unreachable, but it cannot establish that synthetic generation is the only source of oracle defects in the field. Path A was not audit-compatible, and Path B is not external validation.

Required replacement:

> The real-version control contains 0/20 unreachable items. This contrast is informative but bounded: a purposive sample from one public repository can show that the auditor does not mark every evolution as unreachable, but it cannot establish that synthetic generation is the only source of oracle defects in the field. Gate 21's reopened Path A found a public evolution register, but none of its 487 tool-level records could be expressed as a target-bearing auditor item under the declared external rights; it therefore supplies no external reachability rate. Path B remains a negative control and is not external validation.

### 3. Results / Repair has a power cost (`paper/main.tex:184`, Section 5.4)

Current:

> All three MDEs exceed the preregistered 0.20 effect. This is not a null result from a failed baseline campaign: Gate 20 was cancelled before the campaign because the frozen scoreable surface could not support its planned effect size. Excluding bad items is scientifically necessary for valid scoring, but it is not a free statistical repair.

Required replacement:

> All three MDEs exceed the preregistered 0.20 effect. This is not a null result from a failed baseline campaign: Gate 20 was cancelled before the campaign because the frozen scoreable surface could not support its planned effect size. Gate 21 adds no scoreable external items and therefore does not change this Gate 19-C power calculation or any frozen local score. Excluding bad items is scientifically necessary for valid scoring, but it is not a free statistical repair.

This Section 5.4 change is required even though the external result is negative;
it prevents readers from treating the feasibility refusal as an added scoreable
surface or as a change to the local power analysis.

### 4. Limitations / Self-authored sandbox (`paper/main.tex:198`, Section 7.1)

Current:

> **Self-authored sandbox.** Contribution 2 is a measurement of a controlled local construction, not a field prevalence estimate. Synthetic mutation operators can create unreachable targets that a real API maintainer would never publish. The real-version control found no unreachable item in its measured sample, but the sample is small, purposive, and drawn from one repository.

Required replacement:

> **Self-authored sandbox.** Contribution 2 is a measurement of a controlled local construction, not a field prevalence estimate. Synthetic mutation operators can create unreachable targets. Gate 21 does not show that MCPEvol-Bench contains the same defect: its pinned register was not auditable under the external agent rights because the acquired records did not provide the target-bearing old/new argument surface required by the frozen auditor. The real-version control found no unreachable item in its measured sample, but the sample is small, purposive, and drawn from one repository.

This removes the unsupported assertion about what a real maintainer would or
would not publish and replaces it with the observed Gate 21 boundary.

### 5. Limitations / Single-system and preprint scope (`paper/main.tex:208`, Section 7.1)

Current:

> **Single-system and preprint scope.** The evidence is a tier-(b) single-system case study. The Path B control is not external validation, and the arXiv manuscript is a preprint, not a peer-reviewed article.

Required replacement:

> **Single-system and preprint scope.** The evidence remains a tier-(b) single-system case study. Gate 21's Path A result is a second feasibility boundary, not external validation: its 487 input records yielded 0 converted auditor items and 487 adapter refusals. The Path B control is also not external validation, and the arXiv manuscript is a preprint, not a peer-reviewed article.

## Requested sentence check

The exact sentence described in the gate request — “an old/new correspondence
register is a specific artifact that a benchmark has no reason to publish unless
someone intends to audit its oracle” — is **not present** in the current
`paper/main.tex` at the inspected HEAD (no matching `correspondence`, `specific
artifact`, or `no reason to publish` text was found). If that sentence exists in
an uncommitted pre-submission copy, replace it with the evidence-bound sentence
from item 4 above; do not retain the universal claim.

## Optional tightening recommended by the same evidence

The following current sentence is not false, but should be expanded if the owner
wants the paper to carry the new feasibility result explicitly.

Current (`paper/main.tex:216`):

> **Does the self-authored sandbox undercut the unreachability measurement?** It limits generality and is a central limitation. It does not erase the local measurement: the oracle defect is reproducible, typed, and traceable. The paper's claim is that a benchmark author should perform this audit, not that every external benchmark has the same defect.

Suggested replacement:

> **Does the self-authored sandbox undercut the unreachability measurement?** It limits generality and is a central limitation. It does not erase the local measurement: the oracle defect is reproducible, typed, and traceable. Gate 21 adds a stricter external boundary: a public evolution register is not enough unless its target-bearing expected calls and contract correspondence are declared under the rights being audited. The paper's claim is that a benchmark author should perform this audit, not that every external benchmark has the same defect.

## Claims intentionally unchanged

Do not change the Gate 19-C numeric results, the 20-pair Path B audit, or the
abstract's statement that the measured defect surface is self-authored. Gate 21
does not add an external reachability denominator, does not produce a second
negative-control audit, does not rescore any frozen gate, and does not lift the
paper above tier (b).
