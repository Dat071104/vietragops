# Unreachable Oracles — manuscript package, version 3.1

Revised 2026-09-16 from version 3 (`gate22-paper-v3-20260914`), which was
revised from version 2 (`gate21-paper-v2-20260912`) and version 1
(`gate10-paper-v1-20260911`).

Version 3 existed because an external review of the version 2 package found
three defects that version 2 could not have found by compiling itself. All
three were defects of **declaration** — the paper described its own instrument
inaccurately — and none moved a measured value.

**Version 3.1 exists because the same discipline was then applied to the
reproduction claim itself, and it did not survive.** Checking out the version 3
tag into a fresh working tree and running `scripts/reproduce.py` there exited
**1**, not 0, for two independent reasons: a line-ending rewrite on checkout,
and 107 MB of frozen measurement inputs that the repository has never
distributed. Section 8 asserted a clean run. Along the way the check found that
eight frozen Gate 07/08 artifacts had stopped hashing to their own frozen
manifest. No measured value moved here either. See *What changed in 3.1*
below.

## Contents

| File | What it is |
|---|---|
| `main.tex` | The manuscript. Single file, self-contained. **This is the arXiv submission.** |
| `CHANGES_AND_AUDIT.md` | Every defect found in versions 1 and 2 and what was done about it, plus the audit of this version against twelve failure categories. Read this first if you want to know what was checked. |
| `EVIDENCE_LEDGER_ADDENDUM.json` | The nine numbers in the manuscript that are not in the frozen Gate 10 ledger, plus the seven `B`-keyed rule-ablation records added in version 3, each with source artifact, commit, SHA-256, and locator. Also twelve verification notes: three recording the version 2 defects, and two added in version 3.1 recording that the section 8 reproduction claim did not hold for a reader and that eight frozen artifacts had stopped hashing to their own manifest. |
| `REFERENCES_VERIFIED.json` | Per-reference verification record at two levels: bibliographic metadata, and the specific content claim the manuscript makes. 15 references. Records one corrected author list, one reference whose content could not be verified, and the abstract-level verification standard applied to the six references added in version 3. |
| `ARXIV_CHECKLIST.md` | Submission metadata and the owner decisions that remain open. |

`main.pdf` is **not** shipped with this package. Version 2 shipped one and the
README had to warn against uploading it; not shipping it removes the failure
mode. Build it from `main.tex` with the commands below.

## Building

`main.tex` is the top-level file. It needs no `.bib` file (the bibliography is
inline) and **no image files** — both figures are drawn in TikZ.

```
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Three passes resolve the `longtable` column widths and the cross-references.
Packages used are all standard: `geometry`, `fontenc`, `inputenc`, `lmodern`,
`microtype`, `amsmath`, `amssymb`, `array`, `booktabs`, `longtable`,
`tabularx`, `enumitem`, `xcolor`, `url`, `tikz` (with `arrows.meta` and
`positioning`), and `hyperref`.

### Last verified build — stated exactly

Three-pass `pdflatex` via MiKTeX 24.1 (MiKTeX-pdfTeX 4.18), 2026-09-16, read
from `main.log` rather than from stdout — the messages below do not appear on
stdout at all, which is how a build can look clean and not be:

- **27 pages**
- **0 overfull hboxes**, 19 underfull hboxes
- **0 LaTeX warnings**, 0 undefined references or citations
- **3 messages at error level**, which is why `pdflatex` exits with status 1
  even though the PDF is correct. Reproduced in full rather than summarised
  away:

  ```
  ! Infinite glue shrinkage found in box being split.
  ```

All three come from `\end{longtable}` — the three appendix longtables, at
source lines 1596, 1650 and 1700. Version 3 produced one of them at 26 pages;
the version 3.1 text repaginates those tables so three of them now split. The
message is emitted by `longtable` when a table splits across a page
boundary, TeX reports it as an error and then continues (`the offensive
shrinkability has been made finite`), and the rendered output is correct. We
bisected it: it reproduces on a bare `\documentclass{article}` +
`\usepackage{longtable}` document with a table long enough to split, so it is
not caused by anything in this manuscript's content or preamble. It is
recorded rather than omitted because version 2's README claimed "0 errors, 0
LaTeX warnings, 18 pages" against a source that actually produced 21 pages,
seven overfull hboxes, and three copies of this message. A paper that asks
benchmark authors to audit their own ground truth cannot misreport its own
build.

## What changed in 3.1

Nothing in the measurement. Three things in what the paper claimed about
reproducing it, and one repair to the repository.

**1. Section 8 claimed a clean reproduction that a reader could not get.** It
said the harness "exits zero with the audit artifacts byte-identical to the
committed files". Cloning the version 3 tag into a fresh working tree and
running it there exited **1**. Section 8 now states, stage by stage, what a
clone can and cannot verify.

**2. Line-ending rewrites broke byte-exactness on checkout.** 48 paths have
their SHA-256 asserted inside a committed artifact. Cloning on Windows with the
Git-for-Windows default `core.autocrlf=true` rewrote every one of them, which
failed stage 2 and the stage 4 `register_sha256` comparison. A `.gitattributes`
now pins exactly those 48 with `-text`. A blanket policy was rejected: 191 of
602 tracked files hold CRLF on disk against an LF blob and would all have been
rewritten by one.

**3. 87 of the 134 frozen manifest entries are not distributed.** They are the
raw Gate 07/08 measurement archive, ~107 MB, excluded by
`gates/artifacts/.gitignore` and carried by no tag — so no clone has ever been
able to check them. Stage 2 now separates a file that is present but altered
(always a failure) from one that was never distributed, reports `PASS
(PARTIAL)` with the reason, and says so in its summary.
`--require-full-manifest` restores strict behaviour. No reachability number
depends on those 87 files: the 310-item register is rebuilt from the committed
generator, so stages 3 and 5 are byte-identical from a bare clone.

**4. Eight frozen artifacts had stopped hashing to their own manifest.** Git
had normalised `GATE_07_METRICS.json`, `GATE_07_METRICS_V4.json`,
`GATE_07_PROTOCOL.json`, `GATE_07_PROTOCOL_V2.json`, `GATE_07_PROTOCOL_V3.json`,
`GATE_07_PROTOCOL_V4.json`, `GATE_07_PROTOCOL_V4_FREEZE_LEDGER.json` and
`GATE_08_PROTOCOL.json` to LF at an earlier commit, so their committed bytes no
longer matched the value `GATE_19_FROZEN_SOURCE_HASHES.json` records for them.
For `GATE_07_PROTOCOL_V2.json` the original mixed endings (389 CRLF and 4 bare
LF) cannot be reconstructed from the blob by any `eol` setting. Their bytes were
restored to the recorded form. **The manifest was not edited to match the
artifacts; the artifacts were moved back to the manifest.** For each of the
eight, the parsed JSON before and after is identical and the only difference is
line endings.

Verified after the change: a fresh clone with `core.autocrlf=true` runs all
five stages and exits 0, with stage 2 reported as partial and stages 3 and 4
bit-identical. The owner's working tree still reports 134/134 UNCHANGED, and
`--require-full-manifest` exits 0 there and 1 in a clone.

The superseded tag `gate22-paper-v3-20260914` was left in place rather than
moved. A published tag records what was claimed at that moment, and rewriting
one to make a later claim true is the move this paper argues against.

## What changed from version 2

Three defects, found by external review of the version 2 package, plus the
package-metadata cleanup that review also prompted.

**1. The auditor evaluated rules the rights declaration did not list.**
`research/gate19/information_rights.json` declares three derivation rules.
`research/gate19/auditor.py` evaluates five: the three declared, plus
`visible_literal` (a reachability rule) and the hidden-join detector (an
unreachability rule). Version 2 said "three declared rules" and this was
wrong. Worse for the paper's own discipline, the undeclared reachability rule
fires 35 times while the declared rule it shadows fires zero.

*What we did.* Declared the complete grammar in a new artifact,
`research/gate19/derivation_grammar.json`, rather than editing the frozen
rights file — that file is what the frozen audit was produced under and its
commit is cited in the manuscript. Then tested whether the result depended on
the undeclared rule, by re-running all 310 items under four configurations of
the grammar:

| | Configuration | reach | absent | conv. |
|---|---|---|---|---|
| V1 | As committed | 260 | 10 | 40 |
| V2 | `visible_literal` removed | 260 | 10 | 40 |
| V3 | `visible_split` evaluated first | 260 | 10 | 40 |
| V4 | `visible_literal` scoped to source values only | 260 | 10 | 40 |

Per-family counts are identical across all four. The 50/310 headline does not
depend on the undeclared rule, because the two rules accept exactly the same
35 items on this register. The harness is `research/gate19/ablation.py`; it
asserts that its default configuration reproduces the committed auditor item
for item before reporting anything.

**2. The paper said the auditor parses the rights object. It does not.**
`classify_item` accepts a `rights` argument and never reads it; `audit_items`
reads only `rights["schema"]`. What actually constrains a classification is
the *materialised* surface: the builders instantiate the declared rights into
each item's visible source values, visible text, and declared contract fields
ahead of the audit. Section 4.1 now says so, and a new test states the
relationship executably — withdraw a source value from an item's granted
surface and a reachable target becomes unreachable.

**3. The 20-pair external sample was not the negative control it was called.**
Fifteen of the twenty are admitted by `declared_external_derivation`, the rule
that accepts a hand-supplied observability annotation produced by the same
adjudication pass that judged the pair. For those, the auditor returns the
adjudicator's conclusion. Withholding the annotation gives 5 reachable and 15
fail-closed. The specificity claim is withdrawn; contribution 3 is retitled to
a hand-adjudicated external sample; and the manuscript now notes that three of
the five mechanical acceptances have the new tool's own registered name as
their target value, with a fourth being a schema status word and the fifth a
resource description string.

**Also in this version:**

- **Six benchmark-validity references added**, including the closest prior
  work — a 2026 validity audit of four tool-calling benchmark families in the
  same arXiv category. Version 2 positioned against agent-adaptation, drift
  benchmarks, MCP evaluation, and API migration, and omitted the literature
  nearest its actual contribution. A new Related Work subsection states the
  distinction we can defend (position in the evaluation pipeline) and
  explicitly disclaims priority over benchmark-validity auditing and over
  finding incorrect ground truths.
- **Absolute impossibility language replaced with identifiability.** The
  introduction no longer says no agent can produce the target except by
  guessing; a pretrained model's prior over naming conventions is outside the
  benchmark's rights but inside the model. The claim is now that the
  benchmark-supplied evidence does not determine the target, which is what the
  measurement supports.
- **Reachability is stated as relative to a declared grammar**,
  `Reachable(g | R, G_R)`, with an explicit list of the transformations the
  grammar does *not* decide.
- **Three tags separated** in Section 8: the measurement-evidence freeze, the
  version 2 manuscript tag, and this version's artifact tag. Version 2's
  checklist put the version 1 tag in the arXiv Comments field.
- **Formatting.** Seven overfull hboxes (largest 60.93pt) reduced to zero.
- **Reproduction harness extended** to five stages and ten unit tests; it now
  re-runs the ablation and compares it to a committed artifact. The synthetic
  and external audits remain bit-identical to their committed counterparts.

`CHANGES_AND_AUDIT.md` has the detail, with evidence for each.

## Before submitting

Four things are the owner's, not the manuscript's:

1. **Licence.** The arXiv licence choice is irrevocable for that version.
2. **Categories.** `cs.SE` primary with `cs.CL` and `cs.AI` cross-lists is the
   recommendation; see `ARXIV_CHECKLIST.md` for the reasoning.
3. **Endorsement**, if arXiv asks for it on a first submission.
4. **Submission itself.** Nothing in this package submits anything.

The author block is set — Nguyen Thanh Dat, Ton Duc Thang University — and is
no longer a placeholder. Version 2's README still described it as one.

## A note on the numbers

Every numeric claim in the manuscript carries a superscript key into a ledger
record that names the artifact, its commit, its SHA-256, and the locator inside
it. During the version 2 revision, no number was carried over from version 1's
prose; each was re-read from the artifact. Version 3 adds no new measurement of
the benchmark and changes none: its seven new `B`-keyed records are outputs of
the ablation harness, and they exist to test whether the existing measurements
depend on an undeclared rule.

This is deliberate, and version 3 is the case for it. A declaration drifted
from its implementation for two releases without anyone noticing, and what
caught it was an outside reader with the package and no access to the code.
The right response was to check whether the numbers moved — they did not — and
to say both things plainly.
