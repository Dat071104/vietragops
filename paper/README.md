# Unreachable Oracles — manuscript package, version 3.4

Revised 2026-09-17 from version 3.3 (`gate22-paper-v33-20260916`), which was
revised from version 3.2 (`gate22-paper-v32-20260916`), version 3
(`gate22-paper-v3-20260914`), version 2 (`gate21-paper-v2-20260912`) and
version 1 (`gate10-paper-v1-20260911`).
Tag `gate22-paper-v34-20260917`.

**Version 3.4 is a correction pass on four statements plus one omission. It
changes no code, no artifact, and no measured value.** A pre-submission review
of the version 3.3 package found a bound stated in the wrong direction, a
limitations sentence that overclaimed against this paper's own Section 5.4, a
family count in the abstract that disagreed with the frozen audit artifact, and
one closely related work — a released benchmark that states this paper's own
premise as a benchmark-construction requirement — that neither the version 3
nor the version 3.3 literature search reached. See *What changed in 3.4* below.

**Version 3.3 was a literature and declaration correction pass on the same
terms.** An external review of the version 3.2 package found four things that
package could not have found by compiling itself: a third-party figure quoted
against the wrong denominator, a Related Work claim broader than the literature
supports, two closely related works the version 3 search had missed, and an
Appendix A that still contradicted the two disclosures version 3 was written to
make. See *What changed in 3.3* below.

Version 3 existed because an external review of the version 2 package found
three defects that version 2 could not have found by compiling itself. All
three were defects of **declaration** — the paper described its own instrument
inaccurately — and none moved a measured value.

**Version 3.2 exists because the same discipline was then applied to the
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
| `EVIDENCE_LEDGER_ADDENDUM.json` | The nine numbers in the manuscript that are not in the frozen Gate 10 ledger, plus the seven `B`-keyed rule-ablation records added in version 3, each with source artifact, commit, SHA-256, and locator. Also eighteen verification notes: three recording the version 2 defects, two added in version 3.2 recording that the section 8 reproduction claim did not hold for a reader and that eight frozen artifacts had stopped hashing to their own manifest, two added in version 3.3 (`V13`, `V14`) recording the wrong-denominator citation and the Appendix A contradiction, and four added in version 3.4 (`V15`–`V18`) recording the inverted bound direction, the overclaimed summary of the failed external audit, the family count that disagreed with the frozen artifact, and the power-analysis phrasing. No claim record changed in 3.3 or 3.4. |
| `REFERENCES_VERIFIED.json` | Per-reference verification record at two levels: bibliographic metadata, and the specific content claim the manuscript makes. 19 references, 18 verified at both levels. Records one corrected author list, one reference whose content could not be verified, one verified only from a conference programme entry, one supporting quote corrected from paraphrase to verbatim, and the abstract-level verification standard applied to the nine references added in versions 3 and 3.3 — against which the single version 3.4 addition is the one entry verified from its full text. |
| `ARXIV_CHECKLIST.md` | Submission metadata and the owner decisions that remain open. |

### On the rendered PDF, and on what the release archive contains

The three versions before this one each answered this differently, so the
current answer is stated once, with the reason.

**Version 3.4 ships no PDF.** Version 2 shipped one and the README then had to
warn against uploading it. Version 3.2 shipped none, which removed the failure
mode. Version 3.3 shipped one under `build/` with a warning, because a reader
had asked to read the paper without a TeX installation. Version 3.4 returns to
shipping none, and the reason is arXiv's own rule rather than taste: when a PDF
is produced from TeX, arXiv wants the source and asks that generated output not
be included, so a release archive that carries `main.pdf` next to `main.tex` is
an archive a reader can upload wrongly.

**The release archive for this version is `main.tex` and nothing else.** That
makes it the arXiv submission and not merely a package containing it. Build the
PDF with the commands below; the build recorded under *Last verified build* is
the one that produced the page count quoted there.

The provenance files listed above — this README, the change log, the
checklist, and the two JSON records — are not in that archive either. They are
records for the repository and for a reader of the repository, not inputs to a
LaTeX build, and arXiv has no use for them. They live at tag
`gate22-paper-v34-20260917` under `paper/`.

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

Three-pass `pdflatex` via MiKTeX (MiKTeX-pdfTeX), 2026-09-17, read from
`main.log` rather than from stdout — the messages below do not appear on
stdout at all, which is how a build can look clean and not be:

- **30 pages** (version 3.3 was 29, version 3.2 was 27; the version 3.4
  Related Work and Appendix E additions account for the one)
- **0 overfull hboxes**, 19 underfull hboxes
- **0 LaTeX warnings**, 0 undefined references or citations
- **2 messages at error level**, which is why `pdflatex` exits with status 1
  even though the PDF is correct. Reproduced in full rather than summarised
  away:

  ```
  ! Infinite glue shrinkage found in box being split.
  ```

Both come from `\end{longtable}`, at source lines 1775 and 1829 — the same
two tables as in version 3.3, moved down the file by the version 3.4 additions.
Version 3.2 produced three of these from three splitting appendix longtables;
the version 3.3 repagination means the third table no longer splits, so there
are two. The
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

One overfull hbox **was** introduced in version 3.3 and is not in the count
above because it was fixed rather than reported: adding a third superseded tag
to the Section 8 list put three `\texttt` tags on one line with one break point
each, at 11.17pt over. Extra `\allowbreak` points inside each tag resolved it.
The count above is from the build after that fix. Version 3.4 adds a fourth tag
to the same list and widens one Appendix D table cell; the `\allowbreak` points
already there absorbed both, and this build introduced no new overfull box.

Version 3.4 also sets `\hypersetup` in the preamble, so the PDF now carries a
document title, author, subject, and keywords instead of leaving them blank.
That is metadata on the rendered file only. arXiv takes its own metadata from
the submission form, so this changes nothing about the submission.

## What changed in 3.4

Nothing in the measurement, nothing in the code, and nothing in any gate
artifact. Four statements that claimed more or other than the evidence
supports, one missing reference, and one preamble addition. The defects came
from a pre-submission review of the 3.3 package; each was re-derived here
against a primary record before being accepted, which is why two of the four
came out differently from the way the review described them.

**1. A bound was stated in the wrong direction.** Section 7.1 said that a
monotonic extension of `G_R` — one that only adds admission rules — "could
only lower the reported rate", and then concluded that "monotonicity is the
condition under which the rate is a lower bound". Those two clauses contradict
each other. If enrichment can only lower the unreachability rate, then the
reported rate bounds the enriched one from above: 16.1% is an **upper** bound
over that class of grammars, not a lower one.

This one is worth dwelling on, because version 3.3 touched this exact sentence.
Defect F5(a) of the 3.3 pass narrowed the claim from enrichment *in general* to
*monotonic* enrichment and left the direction wrong, and the change-log entry
describing that fix repeated the inversion. Fixing the scope of a claim without
re-checking its direction is the same inattention as quoting a paraphrase
instead of a source. The manuscript and the 3.3 change-log entry are both
corrected. Note `V15`.

**2. One sentence overclaimed in two ways, and one of them contradicted Section
5.4.** Section 7.1 summarised the failed external audit as showing that "one
published benchmark in this space adds no required parameters and evaluates
interactively, a design under which the pre-execution defect class we measure
does not arise."

The review flagged the second half, correctly. It is not supported: the same
paragraph says no record could be converted into an auditable item, so no rate
exists in either direction, and an interactive rights regime does not make
derivable a target that no rights regime makes derivable.

The first half was found while fixing the second, by reading Section 5.4
against the sentence instead of editing the sentence alone. Section 5.4 states
the scope carefully — 0 of 312 parameter items are required on the
`parameter_additions` surface — and then reports that **two** required
additions appear on a separate `parameter_changes` surface and **two** required
fields appear among 11 removals. Unscoped, the Section 7.1 summary contradicted
the result two sections earlier in the same paper. Both halves are now scoped,
with the two required additions and the two required removals named in place.
Note `V16`.

**3. The abstract attached a 12-family count to a denominator that spans 11.**
The abstract read "50 of 310 argument-pair items unreachable across 12 drift
families"; contribution 2 read "Across 12 families and 310 argument-pair
items". The benchmark does have 12 drift families — that is claim `C001` —
but the 310 argument-pair items do not span them. `GATE_19_AUDIT.json` carries
11 family keys against `item_count` 310; `GATE_19C_RESULT.md` section C2 marks
every pair column for `no_equivalent` as N/A and says it has no argument-pair
items; Section 3.1 already said "11 families; `no_equivalent` contributes
none"; and Figure 3 already drew `no_equivalent` as a family with no
argument-pair surface.

So the abstract disagreed with the frozen artifact, with its own figure, and
with its own Section 3.1, across four releases. The review rated this a
low-severity precision item; it is recorded here at a higher one, because a
number in the abstract that disagrees with the artifact it cites is the defect
class this paper exists to document. The abstract and contribution 2 now name
the 11 of 12 families that have an argument-pair surface. The Appendix D
provenance row now reads "12 drift families, 11 of them pair-bearing", which
carries the frozen value of `C001` rather than replacing it. Note `V17`.

**4. A disclosure implied a result it had not derived.** Section 7.2 discloses
that the power calculation runs over argument-pair items while first-attempt
execution scoring is case-level, then argued that the mismatch "makes our
cancellation decision more conservative, not less". The argument behind that is
sound, but the phrasing reads as a monotonicity result relating power across
two observational units, which was never derived. The passage now calls the
pair-level calculation an optimistic planning screen rather than a valid
case-level power analysis, keeps the 0/15 against 15/35 retention comparison as
the reason the smaller surface cannot pass a screen the larger one already
failed, and says explicitly that this supports the cancellation decision
without establishing a formal cross-unit relation. Note `V18`.

### Also in this version

**GeneBench is cited, and it costs the paper a claim.** The 3.3 pass added
three references and said the version 3 search had missed the pre-execution and
identifiability framings. It had also missed the closest published statement of
this paper's own premise, which sits inside a benchmark rather than inside an
audit. GeneBench's primary design constraints open with a block titled *Ground
truth and identifiability*, requiring that agents be graded on "the quantity
that is actually recoverable from agent-visible data, and not the hidden
data-generating parameters", and that the staged evidence "supports one
uniquely defensible answer" — failing which "success depends on guessing the
benchmark designer's preferred pipeline rather than reasoning from the
evidence".

That is this paper's premise, stated as a construction requirement and enforced
at construction time, by simulating the data so the correct answer is
recoverable from the staged files and by independent review of target
identifiability. Section 2.1 gains two paragraphs; the "what this paper does
not claim" box and the Section 2.1 disclaimer both gain the recoverability
clause; and the Section 7.4 hostile question now names the design-time position
alongside the transcript, construction and protocol ones. What is left as ours
is position in time and mechanism of decision: GeneBench designs
identifiability in and confirms it by independent review, and this paper tests
whether it is present in an oracle that already exists, per item, under a
declared grammar.

The reference is verified from its full text rather than from an abstract —
three routes, recorded in `REFERENCES_VERIFIED.json` and in Appendix E — which
makes it the one entry among the ten references added in versions 3, 3.3 and
3.4 at that level. Appendix E also now records that two consecutive releases
have had their closest related work supplied by a reader rather than by the
author's own search, and that this is a fact about the search.

**PDF document metadata.** `\hypersetup` now sets a document title, author,
subject and keywords, which were previously blank. This is metadata on the
rendered file only; arXiv takes its own metadata from the submission form.

**The release archive is now `main.tex` alone.** See *On the rendered PDF, and
on what the release archive contains* above.

### What was proposed and declined

**Renaming the criterion.** Not done, for the reason given in 3.3: "oracle
identifiability" is a field value inside committed artifacts, and renaming it
across them buys no honesty that narrowing the claim does not already buy. The
claim is narrowed instead, which is what the GeneBench paragraphs do.

**Nothing else.** Every item in the review survived checking and was applied,
including the one the review itself rated lowest.

## What changed in 3.3

Nothing in the measurement, nothing in the code, and nothing in any gate
artifact. Four corrections to what the paper says about other people's work
and about its own instrument, all found by an external review of the 3.2
package and all re-verified here against primary records rather than taken
from the review.

**1. A third-party figure was quoted against the wrong denominator.** Sections
2.1 of versions 3, 3.1 and 3.2 read "Wang et al. run an agentic auditor over
168 benchmarks in nine domains and find over 25.7% carrying critical issues".
The subject of that sentence is the benchmark count, so it reads as 25.7% of
168 benchmarks. The abstract of arXiv:2605.26079 states it as a share of
*tasks*: "critical issues including ambiguous task design, execution
environment conflicts, and incorrect ground truths in over 25.7% of the
evaluated tasks". Corrected, with the denominator emphasised.

The root cause is worth stating because it is inside the artifact meant to
prevent it. The `supporting_quotes` entry for that reference in
`REFERENCES_VERIFIED.json` was a *paraphrase* sitting in a quotations field,
and the paraphrase had already dropped "of the evaluated tasks". Three
releases then copied the paraphrase instead of the source. The quote is now
verbatim and a `correction_v33` field records what it used to say. Note `V13`.

**2. The Related Work distinction was broader than the literature supports.**
Version 3.2 claimed the distinction was position in the evaluation pipeline,
and said "Each of these audits inspects evidence that exists only after a
trajectory has been produced". That is true of Bhat et al., Mohl et al. and
Zhang et al. It is not true of the broader frameworks: the agentic auditor of
Wang et al. reports ambiguous task design and execution-environment conflicts,
which are properties of the task definition, and BenchJack red-teams benchmark
construction. Both inspect the item before any agent runs.

Pre-execution auditing is therefore withdrawn as the distinction. What replaces
it is narrower and survives the literature: **the item-level question of
whether the benchmark's expected target value — each field, each literal, each
construction step — is derivable from the method-visible information surface
before the first call, under an explicitly declared finite derivation
grammar.** The unit is one ground-truth value rather than a task, a benchmark
or a score, and the decision is a deterministic rule rather than expert review
or an LLM judge. Section 2.1, the hostile-questions entry in Section 6.4, the
"what this paper does not claim" box, and the abstract's "We define" all
changed to match.

**3. Three references added, one of which bounds the novelty claim.**

- **Luo et al.**, arXiv:2608.13326, is the one that matters. It audits
  *protocol-level identifiability* for controlled reasoning evaluation, asking
  before any model inference whether an observation protocol's support can
  distinguish policies with different estimands. Structural identifiability
  auditing before inference therefore already exists, and this manuscript now
  says so and claims no priority over it. The objects do differ, and Section
  2.1 states how: Luo et al.'s unit is the protocol and its estimand, ours is
  one ground-truth target and its construction steps. `identifiability` is a
  shared word, not a shared contribution.
- **BenchGuard** (Tu et al., arXiv:2604.24955) cross-verifies benchmark
  artifacts and reports tasks made unsolvable by benchmark defects.
- **AgentSuite / COBA** (Suh et al., ICML 2026) decomposes an agent task into
  User, Environment, Ground Truth and Evaluation and audits each component.
  COBA's Ground Truth component is the same object this paper audits, reached
  by LLM judgement where this work uses a declared grammar.

All three were verified against a primary record before being cited, on the
principle that a reference added on a reviewer's word is the defect this paper
is about. Luo et al. and BenchGuard: arXiv abstract pages read directly.
AgentSuite: title, full author list and abstract read from the ICML 2026
conference programme entry, cross-checked against the ICML 2026 downloads
index. No arXiv record for AgentSuite could be retrieved and the camera copy
was not read — that is the weakest metadata route anywhere in
`REFERENCES_VERIFIED.json` and its entry says so.

Appendix E also now records *why* version 3 missed the two closest works: its
literature search was scoped to tool-calling and agent-benchmark validity and
never reached the pre-execution and identifiability framings.

**4. Appendix A contradicted the two disclosures version 3 was written to
make.** Version 3 declared the complete five-rule grammar in
`research/gate19/derivation_grammar.json` and disclosed in Section 4.1 that
the auditor does not parse an arbitrary rights policy, because the builders
materialise the rights ahead of the audit. Appendix A was not updated for
either. Its step 1 still said "Parse the declared information-rights object",
and its step 3 listed only `identity`, `visible_split` and
`declared_external_derivation` — omitting `visible_literal`, the undeclared
rule Section 3.3 reports firing 35 times. A reader treating Appendix A as the
algorithm specification would have found the paper contradicting itself on
exactly the two points version 3 existed to repair.

Appendix A is now the `evaluation_order` of the committed grammar artifact,
nine steps, checked against `research/gate19/auditor.py::classify_item` line
by line. One detail is worth flagging because the external review got it
wrong: the review proposed an order that put the convention check *after* the
admission rules. The implementation evaluates `unobservable_join` **between**
`visible_literal` and `visible_split`, so adopting the review's order would
have replaced one appendix/implementation mismatch with a subtler one. The
appendix now states that the order is load-bearing, that a target which is
simultaneously an unobservable join and a visible split is classified
unreachable, and that no item in the frozen register is both. Note `V14`.

**Also in this version:** two sentences in Section 6.1 softened to what they
can carry. "A richer $G_R$ could only lower the reported rate" is true of a
*monotonic* extension only — a revision that narrowed an existing rule could
raise it — and "no grammar can derive a symbol it has never seen" is false of
a grammar carrying built-in convention literals, which is precisely why the
restriction on $G_R$ is the load-bearing part of that argument. The
conclusion's one-sentence summary of the 20-pair sample now carries its own
caveat, so it cannot be quoted out of Section 5.3's context. And the AI-use
appendix no longer invokes ICMJE and COPE by name, because the manuscript
cites neither; the substantive statement is unchanged and now stands on its
own.

**What was proposed and declined.** The review also asked for two Appendix E
upgrades, and both are refused for the same reason.

- It reported finding a public full-text copy of `assidiqi2026referencefree`
  and proposed recording that the full text was inspected. It could not be
  retrieved here: IEEE Xplore returned no body and the ResearchGate copy
  returned HTTP 403. The DOI does resolve, which supports the metadata-level
  claim the appendix already makes. Recording a full-text inspection that was
  not performed, in the appendix whose entire purpose is to record where
  verification stopped, is the defect this paper documents. **If the owner
  retrieves that copy, the edit is theirs to make and Appendix E has the slot
  for it.**
- It proposed noting that the full-text HTML of `mohl2026transcript` was
  inspected for the definition of `ground truth access`, to justify Section
  2.1's description of it. Not needed: that abstract names all four criteria
  verbatim — "ground truth access, tool failure, guessing vulnerability, and
  answer format ambiguity" — so the abstract-level standard already covers the
  claim. Re-verified 2026-09-16.

## What changed in 3.2

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

The superseded tags `gate22-paper-v3-20260914` and
`gate22-paper-v31-20260916` were left in place rather than moved. A published
tag records what was claimed at that moment, and rewriting
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
