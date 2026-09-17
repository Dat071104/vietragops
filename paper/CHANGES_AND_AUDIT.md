# Version 3.4: the bound, the scope, and the closest related work

Prepared 2026-09-17 against manuscript version 3.3 (repository tag
`gate22-paper-v33-20260916`). The version 3.3 log follows below, unmodified
apart from one correction marked in place inside defect F5, because that entry
described its own fix in the wrong direction and leaving it standing would
propagate the error.

**No code, no gate artifact, and no measured value changed in this version.**
The auditor was not re-run for correctness, because nothing it reads was
touched; it was re-run anyway before the tag was created, so the tag points at
a state that was verified rather than assumed.

The pattern is now four for four, and version 3.4 makes its shape plainer than
the earlier entries did. Version 2 asserted a rule set its implementation did
not match. Version 3 asserted a reproduction its repository could not deliver.
Version 3.3 asserted a distinction from the literature that the literature does
not support. Version 3.4 asserts none of those, and instead corrects four
statements that were checkable against artifacts and sections already in the
package — including one sentence that version 3.3 had itself rewritten and
left wrong. In every case the claim was checkable, nobody had checked it, and
the error ran in the flattering direction.

Two of the five items below were found by working outward from the review
rather than by accepting it. G2 was reported as one defect and turned out to be
two, the second of which contradicts Section 5.4 of the same paper. G3 was
reported as a low-severity precision item and is recorded here at higher
severity, because a number in the abstract that disagrees with the artifact it
cites is the defect class this paper exists to document.

---

## Part 0a — Defects found in version 3.3

### G1 — The grammar-enrichment bound was stated in the wrong direction (severity: high)

**Defect.** Section 7.1 read: the criterion errs toward calling items
defective, and a *monotonic* extension of `G_R` — one that only adds admission
rules and tightens none — "could only lower the reported rate. A revision that
narrowed an existing rule could raise it, so monotonicity is the condition
under which the rate is a **lower** bound, not a property of enrichment in
general."

The first clause and the last contradict each other. If a monotonic enrichment
can only lower the unreachability rate, then the reported rate bounds the
enriched rate from above. Formally: for any monotonic enrichment `G_new` of
`G_current`, `U(G_new) <= U(G_current)`, so 16.1% is an **upper** bound on the
unreachability rate attainable under that class of grammars.

**Why it survived.** Version 3.3 rewrote this exact sentence. Defect F5(a) of
that pass correctly narrowed the claim from enrichment *in general* to
*monotonic* enrichment, and did not re-check the direction of the bound while
doing it. The F5 entry in the log below then described the fix in the same
inverted terms. Narrowing the scope of a claim without re-reading its direction
is the same inattention as quoting a paraphrase instead of a source, which is
the root cause recorded for F1.

**Fix.** The passage now says that a monotonic extension can only lower the
reported rate, that this makes 16.1% an upper bound on the unreachability rate
obtainable under any such enrichment, that it is not a bound in general, and
that a revision narrowing or replacing an existing rule can move the rate in
either direction. It discloses that an earlier version stated the direction
backwards. Defect F5 below carries a correction note at the point of the error.

**Impact on measured values.** None. 50/310 and 16.1% are measurements under
the grammar actually declared; the corrected sentence is about what a
counterfactual grammar would do. Note `V15`.

### G2 — One limitations sentence overclaimed twice, and once against Section 5.4 (severity: high)

**Defect.** Section 7.1 summarised the failed external audit as showing that
"one published benchmark in this space adds no required parameters and
evaluates interactively, a design under which the pre-execution defect class we
measure does not arise."

*(a) The scope was dropped.* Section 5.4 reports the finding carefully: across
the 141 `PARAM` entries there are 312 parameter items on the
`parameter_additions` surface, of which 0 are required. It then reports that
**two** further required additions appear on a separate `parameter_changes`
surface and **two** required fields appear among 11 removals. Unqualified, "adds
no required parameters" contradicts the paper two sections earlier.

*(b) The conclusion did not follow.* The same paragraph states that no record
could be converted into an auditable item, so no rate exists in either
direction. A feasibility failure cannot then support a claim that the defect
class does not arise under that design. Interactivity changes the rights
regime; it does not make derivable a target that no rights regime makes
derivable, and the paper argues exactly that in Section 2.4.

**How each was found.** (b) came from the pre-submission review. (a) came from
reading Section 5.4 against the sentence while fixing (b), rather than editing
the sentence in isolation. The review did not report it.

**Fix.** The passage now scopes the required-parameter finding to the
`parameter_additions` surface, names the two required additions and the two
required removals in place with a pointer to Section 5.4, and concludes only
that the benchmark does not instantiate the specific hidden-required-field
mechanism of our own surface and that its information rights differ materially
from ours. It states that this does not show reachability defects cannot arise
under an interactive design, and that no claim is made in either direction
because no record became an auditable item.

**Impact on measured values.** None. 0 of 312, the two `parameter_changes`
additions and the two required removals are as reported in Section 5.4 and are
unedited. Note `V16`.

### G3 — The abstract attached a 12-family count to a denominator spanning 11 (severity: high)

**Defect.** The abstract read "50 of 310 argument-pair items unreachable across
12 drift families (16.1%)" and contribution 2 read "Across 12 families and 310
argument-pair items, 50 items (16.1%) are unreachable". The benchmark does have
12 drift families; the 310 argument-pair items do not span them.

Four records already said so:

| Record | What it says |
|---|---|
| `gates/results/GATE_19_AUDIT.json` | `families` has 11 keys; `item_count` is 310 |
| `gates/results/GATE_19C_RESULT.md` §C2 | 12 rows; every pair column for `no_equivalent` is `N/A`, with the note that it has no argument-pair items |
| Manuscript §3.1 | "11 families; `no_equivalent` contributes none, because it has no argument-pair surface" |
| Manuscript Figure 3 | draws `no_equivalent` as a family with no argument-pair surface |

So the abstract disagreed with the frozen artifact it cites, with the figure on
its own page 10, and with its own Section 3.1, across four releases.

**Severity, restated.** The review rated this a low-severity precision item.
That rating is defensible on reader impact and wrong on kind. This paper's
standing rule is that every number traces to a committed artifact and was
verified against it; an abstract number that disagrees with the cited artifact
is a violation of the rule the paper is about. Recorded at high severity for
that reason, not because the figure misleads by much.

**Fix.** The abstract now reads "50 of 310 argument-pair items unreachable
(16.1%), across the 11 of 12 drift families that have an argument-pair
surface". Contribution 2 reads "Across the 310 argument-pair items of the 11
families that have such a surface". The Appendix D provenance row for
`C001`–`C005` now reads "12 drift families, 11 of them pair-bearing" — it
carries the frozen value of `C001` rather than replacing it, because `C001` is
"12 drift families" and that is still true of the benchmark.

**Impact on measured values.** None. 310, 260, 50 and 16.1% are unchanged, and
no claim record changed. Note `V17`.

### G4 — A mixed-unit disclosure implied a result it had not derived (severity: low)

**Defect.** Section 7.2 discloses that the power calculation runs over retained
argument-pair item counts while first-attempt execution scoring is case-level,
and then argued that "the mismatch makes our cancellation decision more
conservative, not less". The argument behind that is sound — the usable
case-level surface is no larger than the item-level surface the calculation
assumed, and is strictly smaller for `tool_replacement` at 0/15 against 15/35
— but the phrasing reads as a monotonicity result relating statistical power
across two different observational units, which was never derived and does not
follow from a retention comparison alone.

**Fix.** The passage now calls the pair-level calculation an optimistic
planning screen and not a valid case-level power analysis, keeps the 0/15
against 15/35 comparison as the reason a smaller surface cannot pass a screen
the larger one already failed, states that this supports the cancellation
decision without establishing a formal cross-unit power relation, and ends by
saying a future case-level or paired design needs its own power analysis and
that the MDE table is not one.

**Impact on measured values.** None. The MDE table, the Wilson intervals and
the CANCEL decision are unchanged. Note `V18`.

### G5 — The closest published statement of this paper's premise was not cited (severity: high)

**Defect.** Version 3.3 added three references and recorded that the version 3
search had missed the pre-execution and identifiability framings. It had also
missed the closest statement of this paper's premise in the literature, which
is not in an audit paper at all. GeneBench, a benchmark for AI agents on
multi-stage inference problems in genomics and quantitative biology, opens its
primary design constraints with a block titled *Ground truth and
identifiability*. Verbatim from that table:

> Agents are graded on recovering the quantity that is actually recoverable
> from agent-visible data, and not the hidden data-generating parameters.

> The staged evidence along with a minimum viable prompt supports one uniquely
> defensible answer. If multiple approaches would ordinarily appear defensible,
> the data contain some empirical signature that rules out all but one.

and the failure mode if the second is violated:

> The task becomes under-specified, and success depends on guessing the
> benchmark designer's preferred pipeline rather than reasoning from the
> evidence.

That is this paper's premise. Enforcement is at construction time: data are
simulated so the correct answer is recoverable from the staged files, and
independent review of target identifiability is part of problem development.

**What it costs.** Any claim that recoverability of a graded target from
method-visible information is a new evaluation concern. Version 3.3 had already
withdrawn *pre-execution auditing* and *protocol-level identifiability* as
distinctions; this withdraws the principle itself. What survives is narrower and
of a different kind: the position in time and the mechanism of decision.
GeneBench designs identifiability into problems under construction and confirms
it by independent review. This paper tests whether it is present in an oracle
that already exists and was not built with the property in mind, by a
deterministic per-item rule over fields, literals and construction steps, under
a declared information-rights object and a finite derivation grammar, with the
typed outcome of every item committed as an artifact.

**What it does not cost.** The measurement, the auditor, the typed failure
classes, the rights object, the grammar, the ablation, or the item-level
evidence ledger. GeneBench states a requirement for benchmarks its authors are
writing; it does not supply a procedure a third party can run on a benchmark
already published, and it does not decide individual items mechanically.

**Fix.** Two paragraphs at the end of Section 2.1, quoting both requirements
and the failure mode verbatim and stating plainly that the principle is not
ours. The priority disclaimer in Section 2.1 and the "what this paper does not
claim" box both gain the recoverability clause. The Section 7.4 hostile
question now names the design-time position alongside the transcript,
construction and protocol ones. One `\bibitem`, one entry in
`REFERENCES_VERIFIED.json`, and a verification paragraph in Appendix E.

**Verification.** Three routes, all on 2026-09-17, and the only full-text check
among the ten references added in versions 3, 3.3 and 3.4:

1. `https://doi.org/10.64898/2026.04.22.720113` resolved — HTTP 302 to
   `biorxiv.org/lookup/doi/10.64898/2026.04.22.720113`.
2. The bioRxiv API record at
   `api.biorxiv.org/details/biorxiv/10.64898/2026.04.22.720113` returned the
   title above, authors `Li, J.; Ho, A.`, date `2026-04-23`, version `1`,
   category `genomics`, published `NA`.
3. The publisher-hosted PDF was retrieved, its text extracted locally, and
   Table 1 and the problem-development paragraph read directly. Every quote
   above is verbatim from that PDF, not from an abstract or a summary.

**Impact on measured values.** None.

---

## Part 0b — What version 3.4 deliberately did not do

**It did not rename the criterion.** The same reasoning as version 3.3.
`oracle identifiability under declared information rights` is a field value
inside committed artifacts; renaming it across them would introduce a new
consistency risk and buy no honesty that narrowing the claim does not already
buy. The claim is narrowed instead, in Section 2.1.

**It did not upgrade `assidiqi2026referencefree`.** Still metadata-level. The
full text was not retrieved for version 3.4 either, and asserting a full-text
inspection in the appendix whose purpose is recording where verification
stopped would be this paper's own documented defect. Carried forward as an
owner action.

**It did not re-open the literature search as a campaign.** One reference was
added because a reader supplied it and it checked out. No claim is made that
the literature is now complete, and Appendix E says so: two consecutive
releases have had their closest related work supplied by a reader rather than
by the author's search, which is a property of the search.

**It did not ship a rendered PDF.** Version 3.3 shipped one under `build/` with
a warning. Version 3.4 ships `main.tex` alone, because arXiv compiles the
source itself and asks that generated output not be included beside it. The
README records all four versions of this decision and the reason for each.

---

## Part 0c — Verification performed for version 3.4

Every item below was run, and the result is what is stated:

1. **GeneBench, three routes.** DOI resolution, bioRxiv API record, and
   full-text PDF. Recorded in G5 above.
2. **The family count, against four records.** `GATE_19_AUDIT.json` parsed:
   `len(families) == 11`, `item_count == 310`, and the 11 per-family item
   counts sum to 310. `GATE_19C_RESULT.md` §C2 read directly. Manuscript
   §3.1 and Figure 3 read directly.
3. **The frozen claim `C001`.** Read from
   `gates/baselines/GATE_10_EVIDENCE_LEDGER.json`: value `12 drift families`,
   status `observed`, locator `C2 all-family scoreable surface`. The Appendix D
   row was written to carry that value rather than to replace it, and the
   frozen ledger was not edited.
4. **Section 5.4 against the Section 7.1 summary.** The two required
   `parameter_changes` additions and the two required fields among 11 removals
   are in Section 5.4 as reported; the Section 7.1 sentence omitted them. This
   is how G2(a) was found.
5. **Three-pass `pdflatex`.** 30 pages, 0 overfull hboxes, 19 underfull, 0
   LaTeX warnings, 0 undefined references, 2 `Infinite glue shrinkage` messages
   from the longtables ending at source lines 1775 and 1829. Counts read from
   `main.log`, not from stdout.
6. **PDF metadata.** `pdfinfo` on the built file: Title, Author, Subject and
   Keywords now populated, previously blank.
7. **`scripts/reproduce.py`.** Run at the version 3.4 commit before the tag was
   created. Result recorded in the commit message and in the version 3.4
   release notes.
8. **Line-ending and manifest safety.** `git check-attr text` on every edited
   file, and a check that no `paper/` path appears in
   `gates/results/GATE_19_FROZEN_SOURCE_HASHES.json`. Neither the manuscript
   nor any provenance file is among the 48 SHA-256-asserted paths.

---

# Version 3.3: the literature, audited

Prepared 2026-09-16 against manuscript version 3.2 (repository tag
`gate22-paper-v32-20260916`). The version 3.2 log follows below, unmodified.

**No code, no gate artifact, and no measured value changed in this version.**
The auditor was not re-run, because nothing it reads was touched. What changed
is what the paper says about other people's work, and what one appendix said
about our own instrument.

The pattern is now three for three. Version 2 asserted a rule set its
implementation did not match. Version 3 asserted a reproduction its repository
could not deliver. Version 3.2 asserted a distinction from the literature that
the literature does not support, and shipped an appendix that contradicted the
two disclosures version 3 was written to make. In each case the claim was
checkable, nobody had checked it, and the error ran in the flattering
direction.

---

## Part 0a — Defects found in version 3.2

### F1 — A third-party figure was quoted against the wrong denominator (severity: high)

**Defect.** Section 2.1 read: "Wang et al. run an agentic auditor over 168
benchmarks in nine domains and find over 25.7% carrying critical issues". The
grammatical subject is the benchmark count, so the sentence reads as 25.7% of
168 benchmarks. The abstract of arXiv:2605.26079 states the figure as a share of
tasks: "critical issues including ambiguous task design, execution environment
conflicts, and incorrect ground truths in over **25.7% of the evaluated
tasks**".

**Why it survived three releases.** This is the part worth recording, because
the failure is inside the artifact built to prevent it. The
`supporting_quotes` field for that reference in `REFERENCES_VERIFIED.json` held
a *paraphrase*, not a quotation: "over 25.7% contained critical issues including
ambiguous design, execution conflicts, and incorrect ground truths". The
paraphrase had already dropped "of the evaluated tasks". Every subsequent check
compared the manuscript against the verification record and passed, because the
record and the manuscript agreed with each other and neither agreed with the
source.

**Fix.** The manuscript sentence attributes the figure to the evaluated tasks,
with the denominator emphasised. The `supporting_quotes` entry is now verbatim
from the abstract, and a `correction_v33` field records what the paraphrase
said. Note `V13` in `EVIDENCE_LEDGER_ADDENDUM.json`.

**Impact on measured values.** None. No number this project produced derives
from or is compared against that figure.

**Lesson applied.** A quotations field that is allowed to hold paraphrase is
not a verification record. Every `supporting_quotes` entry in the file was
re-read; this was the only one that was not verbatim.

### F2 — The Related Work distinction was broader than the literature supports (severity: high)

**Defect.** Version 3.2 claimed the defensible distinction was "position in the
evaluation pipeline", and asserted: "Each of these audits inspects evidence that
exists only after a trajectory has been produced". The hostile-questions entry
in Section 6.4 repeated it: "Existing audits read evidence produced by an
execution".

That holds for Bhat et al. (expert re-judgement of completed tasks, rerun
variance), Mohl et al. (transcript scanners) and Zhang et al. (scaffold and
scorer behaviour). It does not hold for the broader frameworks cited in the
same paragraph. Wang et al.'s agentic auditor reports ambiguous task design and
execution-environment conflicts, which are properties of the task definition.
BenchJack red-teams benchmark construction and evaluation infrastructure. Both
inspect the item before an agent runs. The claim put the whole literature into a
post-execution bucket that two of its own citations do not occupy.

**Fix.** Pre-execution auditing is withdrawn as the distinction, in Section 2.1,
in Section 6.4, in the "what this paper does not claim" box, and in the
abstract's framing verb. What replaces it:

> the item-level question of whether the benchmark's expected target value —
> each field, each literal, each construction step — is derivable from the
> method-visible information surface before the first call, under an explicitly
> declared finite derivation grammar.

The unit is one ground-truth value rather than a task, a benchmark or a score,
and the decision is a deterministic per-item rule rather than expert review or
an LLM judge. Section 2.1 now names which audits *are* post-execution and which
are not, rather than generalising over all of them.

**Impact on measured values.** None. This is a positioning claim; 50/310 is
unaffected and is not a novelty claim.

### F3 — The two closest works were missing (severity: high)

**Defect.** Version 3 added six benchmark-validity references after an external
review found the literature nearest the contribution had been omitted. That
search was scoped to tool-calling and agent-benchmark validity. It never reached
the pre-execution and identifiability framings, which is where the two closest
works sit.

**Fix.** Three references added, each verified against a primary record before
being cited:

| Ref | Verification route | Why it matters here |
|---|---|---|
| `luo2026identifiability` (arXiv:2608.13326) | arXiv abstract page, 2026-09-16 | Audits *protocol-level identifiability* before any model inference. Structural identifiability auditing before inference already exists. |
| `tu2026benchguard` (arXiv:2604.24955) | arXiv abstract page, 2026-09-16 | Cross-verifies benchmark artifacts; reports tasks made unsolvable by benchmark defects. |
| `suh2026agentsuite` (ICML 2026) | ICML 2026 conference programme entry, cross-checked against the ICML 2026 downloads index, 2026-09-16 | COBA decomposes a task into User, Environment, Ground Truth, Evaluation. Its Ground Truth component is the object this paper audits. |

`luo2026identifiability` is the one that constrains the paper. The manuscript's
central term is `identifiability`, and that work establishes structural
identifiability auditing of an evaluation design before inference. Section 2.1
now states the collision and claims no priority over it, then states what
actually differs: Luo et al.'s unit is the protocol and its estimand, ours is
the ground-truth target and its construction steps; they ask whether a design
separates policy classes, we ask whether one item's concrete expected value is
derivable from that item's granted surface. The shared word is not a shared
contribution, and the paper now says which of the two it has.

**On the verification discipline.** The external review supplied all three
references with URLs and content claims. None was cited on that basis. Each was
retrieved and read independently, because a reference added on a reviewer's word
is precisely the defect this paper is about — and version 3's Appendix F already
records one citation that entered this manuscript that way. `suh2026agentsuite`
is the weakest of the three and is marked as such: a conference programme entry,
no retrievable arXiv record, camera copy unread. That is the weakest metadata
route anywhere in `REFERENCES_VERIFIED.json`.

Appendix E also now records *why* version 3 missed these, rather than quietly
adding them as though the earlier search had been complete.

### F4 — Appendix A contradicted the two disclosures version 3 was written to make (severity: high)

**Defect.** Version 3 existed to repair two declaration defects: the auditor
evaluates five rules where the frozen rights file declares three, and the
auditor does not parse a rights policy because the builders materialise the
rights ahead of the audit. Section 3.3 and Section 4.1 were updated. **Appendix
A was not.**

Its step 1 still read "Parse the declared information-rights object",
contradicting Section 4.1. Its step 3 listed only `identity`, `visible_split`
and `declared_external_derivation`, omitting `visible_literal` — the undeclared
rule that Section 3.3 reports firing 35 times while the declared rule it shadows
fires zero. A reader treating Appendix A as the algorithm specification would
have found the paper contradicting itself on exactly the two points version 3
was released to fix.

**Fix.** Appendix A is now the `evaluation_order` recorded in
`research/gate19/derivation_grammar.json`, nine steps, checked line by line
against `research/gate19/auditor.py::classify_item`:

```
target_field_declared → target_value_present → identity → visible_literal
→ unobservable_join → visible_split → declared_external_derivation → fail_closed
```

**One correction to the review that prompted this.** The review proposed a
replacement that placed the convention check *after* the admission rules:
"Check derivability under the declared grammar: identity, visible_literal,
visible_split, and declared_external_derivation ... If the target requires an
unobserved construction convention, emit unreachable-convention-unobservable".
The implementation does not do that. `unobservable_join` is evaluated
**between** `visible_literal` and `visible_split`, which the grammar artifact
states explicitly and which the code confirms. Adopting the proposed order would
have replaced one appendix/implementation mismatch with a subtler one.

The appendix therefore also now states what the previous four-step summary could
not express at all: that the order is load-bearing, that a target which is
simultaneously an unobservable join and a visible split is classified
unreachable, and that no item in the frozen register is both. Note `V14`.

**Impact on measured values.** None. The implementation was already correct and
is unchanged. `gates/results/GATE_19_AUDIT.json` is untouched.

### F5 — Two Section 6.1 sentences claimed more than they can carry (severity: medium)

**Defect (a).** "a richer `G_R` could only lower the reported rate". True of a
*monotonic* extension — one that only adds admission rules. A revision that
narrowed an existing rule could raise the rate. As written, the sentence claimed
a bound that holds under enrichment in general, which is not so.

> **Corrected in version 3.4.** This entry, and the sentence version 3.3 wrote
> in its place, both named the wrong direction. A rate that monotonic
> enrichment can only lower is bounded from *above* by the reported value, so
> 16.1% is an upper bound over monotonic enrichments, not a lower one. The 3.3
> fix narrowed the scope of the claim and left its direction inverted. See
> defect G1 in the version 3.4 log above, and note `V15`.

**Defect (b).** "no grammar can derive a symbol it has never seen". False as
stated: a grammar carrying a built-in convention literal can emit `::` without
having observed it. The restriction is what does the work, and the sentence
omitted the restriction.

**Fix.** (a) now says a monotonic extension could only lower the rate and that a
narrowing revision could raise it. (b) now says the 40 stay unreachable *under a
grammar whose construction literals must themselves be evidenced in R*, names
that condition as the load-bearing part, and says plainly that a grammar with
built-in convention literals or an external prior could classify them
differently — and why we do not adopt one. It also points at Section 5.6, which
sits on the same boundary from the other side by testing whether one model's
prior in fact supplies the separator.

**Impact on measured values.** None. Both sentences are about what a
counterfactual grammar would do; neither is a measurement.

### F6 — The conclusion's external-sample sentence was quotable out of context (severity: low)

**Defect.** "The same auditor found no unreachable item in 20 hand-verified real
version pairs." Not false, and Section 5.3 caveats the sample heavily — but the
sentence stands alone in a conclusion and reads as a specificity result, which
version 3 explicitly withdrew.

**Fix.** The conclusion sentence now carries the caveat itself: 15 of the 20
acceptances depended on a supplied observability annotation, so the sample is a
representability check and not an estimate of auditor specificity.

### F7 — The AI-use appendix invoked two organisations the paper does not cite (severity: low)

**Defect.** Appendix F said "in line with ICMJE and COPE guidance". The
manuscript cites neither. For a paper whose discipline is that every claim
traces to a checked source, an appeal to two named authorities with no record
behind it is a loose end in the one appendix about honesty.

**Fix.** The organisation names are removed and the substantive statement stands
on its own: no AI system is listed as an author because authorship carries
accountability a non-human agent cannot hold, and the human author takes
responsibility and discloses the assistance. Adding two non-research
bibliography entries was the alternative and was rejected as weight the paper
does not need for an arXiv preprint. Nothing the appendix asserts changed.

---

## Part 0b — What version 3.3 deliberately did not do

**It did not re-run the auditor, the ablation, or the reproduction harness as a
condition of release.** Nothing they read changed. Re-running them would have
produced identical artifacts and would have implied that this version's
corrections were of a kind that could move a measurement. They were not.

**It did not change the 50/310, the 20/45, the 0/30 `argument_merge`, or the
15/35 `tool_replacement`.** No input, rule, or artifact was touched.

**It did not upgrade the `assidiqi2026referencefree` verification level.** The
review reported locating a public full-text copy and proposed recording that the
full text had been inspected. It could not be retrieved here: IEEE Xplore
returned no body and the ResearchGate copy returned HTTP 403. The DOI does
resolve — it redirects to `ieeexplore.ieee.org/document/11534189` — which
supports the metadata-level claim Appendix E already makes and nothing more.

Recording a full-text inspection that was not performed, in the appendix whose
sole purpose is to record where verification stopped, would be the exact defect
this paper documents. **This is left as an owner action.** If the owner
retrieves that copy, §2.3 and Appendix E have the slot for the stronger
statement, and the change is one sentence in each.

**It did not add a full-text note for `mohl2026transcript`.** The review
proposed recording that the full-text HTML was inspected for the definition of
`ground truth access`, on the grounds that Section 2.1 describes that criterion
specifically while Appendix E claims only abstract-level verification. Checked
and not needed: the abstract names all four criteria verbatim — "ground truth
access, tool failure, guessing vulnerability, and answer format ambiguity" — so
the abstract-level standard already covers what the manuscript says. Re-verified
2026-09-16. No inconsistency existed.

**It did not restate the contribution as a new criterion name.** The review
suggested replacing "oracle identifiability" with "oracle-target derivability"
throughout. The narrowing it is after is real and has been made, but at the
level of what the paper *claims* rather than what it *calls* its criterion:
`identifiability` is the name of a committed artifact's criterion field and
appears throughout the manuscript, so a rename is a large mechanical change with
a new class of inconsistency risk and no gain in honesty over saying plainly, in
Section 2.1 and in the claims box, that this work instantiates identifiability
at item level rather than introducing it.

---

## Part 0c — Verification performed for version 3.3

1. **All three added references retrieved independently**, not accepted from the
   review. Primary records read on 2026-09-16: two arXiv abstract pages and one
   ICML 2026 programme entry, the last cross-checked against the ICML 2026
   downloads index.
2. **The ABA denominator re-read** from the arXiv abstract of 2605.26079 and
   compared against both the manuscript sentence and the
   `REFERENCES_VERIFIED.json` quote. Both were wrong; both corrected.
3. **The Mohl abstract re-read** to test whether Appendix E's provenance claim
   covers Section 2.1's description of `ground truth access`. It does.
4. **Appendix A checked against the implementation**, not against the review's
   proposed text. `research/gate19/derivation_grammar.json`
   `evaluation_order` and `research/gate19/auditor.py::classify_item` agree with
   each other and now agree with the appendix.
5. **ContDa's canonical citation confirmed** from the ACL Anthology page: pages
   21519–21539, DOI `10.18653/v1/2026.findings-acl.1082`. Both added.
6. **`zhu2025abc` author count confirmed as 25** before removing the
   "(25 authors)" annotation — the annotation was correct, and was dropped as
   non-standard bibliography style rather than as an error.
7. **Three-pass `pdflatex` build**, counts read from `main.log`: 29 pages, 0
   overfull hboxes, 19 underfull, 0 LaTeX warnings, 0 undefined references, 2
   `Infinite glue shrinkage` messages from longtable splits. One overfull hbox
   introduced by the three-tag list in Section 8 was found and fixed before the
   count above was taken.
8. **Reference bookkeeping reconciled** across `main.tex` Appendix E ("Sixteen
   of eighteen"), `REFERENCES_VERIFIED.json` (18 entries, 17 at
   `content_claim`), `ARXIV_CHECKLIST.md` (18 entries) and `README.md`.

---

# Version 3.2: the reproduction claim, audited

Prepared 2026-09-16 against manuscript version 3 (repository tag
`gate22-paper-v3-20260914`). The version 3 log follows below, unmodified.

Version 3 was released on the strength of an external review that read only the
shipped package. Before submission we did the one check that review could not
do: clone the tag into an empty directory and run the reproduction harness as a
reader would. **It exited 1.** Section 8 said it exits 0.

The pattern repeats the one that produced version 3, one level further out. The
paper's thesis is that a benchmark should not assert a ground truth its declared
information cannot derive. Version 2 asserted a rule set its implementation did
not match. Version 3 asserted a reproduction its repository could not deliver.
In both cases the claim was checkable, nobody had checked it, and the error ran
in the flattering direction.

---

## Part 0a — Defects found in version 3

### F1 — Section 8 asserted a reproduction a reader could not obtain (severity: high)

**Defect.** Section 8 stated that `scripts/reproduce.py` "exits zero with the
audit artifacts byte-identical to the committed files". Checking out
`gate22-paper-v3-20260914` into a fresh worktree and running it produced exit
code 1, failing at stage 2 and again on the stage 4 `register_sha256`
comparison. The statement was true only in the working tree that produced the
repository.

**Evidence.** `git worktree add --detach <dir> gate22-paper-v3-20260914`, then
`python scripts/reproduce.py` in that directory. Stage 2 reported 126 of 134
entries mismatching; stage 4 differed on exactly one key, `register_sha256`.

**Resolution.** Two independent causes, F2 and F3 below. Section 8 now states
stage by stage what a clone can and cannot verify, and the claim it makes is the
one that survives an external check. A new hostile question in section 7.4
states the limitation in the reader's own words.

### F2 — Line-ending rewrites invalidated published hashes on checkout (severity: high)

**Defect.** 48 paths have their SHA-256 asserted inside a committed artifact:
the 47 tracked entries of `gates/results/GATE_19_FROZEN_SOURCE_HASHES.json`,
and `gates/baselines/GATE_19_EXTERNAL_MCP_PAIRS.json`, whose digest is recorded
as `register_sha256` inside `gates/results/GATE_19_EXTERNAL_AUDIT.json`. The
repository carried no `.gitattributes`, so cloning on Windows with the
Git-for-Windows default `core.autocrlf=true` rewrote every one of them and
invalidated every published digest at once.

**Resolution.** A `.gitattributes` pinning exactly those 48 paths with `-text`,
which disables end-of-line conversion in both directions. A blanket `* -text`
was considered and **rejected**: 191 of 602 tracked files hold CRLF on disk
against an LF blob, so a repository-wide policy would have rewritten all 191 and
buried the fix in unrelated churn. The pinned set is exactly the set of paths
whose bytes something else asserts.

### F3 — 87 of the 134 frozen manifest entries have never been distributed (severity: high)

**Defect.** `gates/artifacts/.gitignore` contains a bare `*`. The 87 manifest
entries beneath it — the raw Gate 07 and Gate 08 measurement archive, roughly
107 MB of request ledgers, per-item traces, offline retrieval runs and router
state — have never been committed, at any tag, including
`gate10-paper-v1-20260911`. No clone has ever been able to verify them, and
stage 2 failed hard on all 87 rather than reporting the situation.

**Resolution.** Stage 2 now distinguishes three cases: a file present but
altered (always a failure), a file missing from anywhere other than the
undistributed archive (always a failure), and a file absent because it was never
distributed (reported as `PASS (PARTIAL)` with the reason and the count).
`--require-full-manifest` restores strict behaviour for a working tree that holds
the archive. The summary line says `ALL AVAILABLE CHECKS PASSED` and names the
partial stage, so a partial run cannot be read as a full one.

**What this does not excuse.** The archive is still not distributed, and section
8 says so rather than implying otherwise. What we can show is that no
reachability number depends on it: the 310-item register is rebuilt by the
committed generator, not read from `gates/artifacts/`, so stages 3, 4 and 5 are
byte-identical from a bare clone.

### F4 — Eight frozen artifacts no longer hashed to their own frozen manifest (severity: high)

**Defect.** Found while fixing F2. `GATE_07_METRICS.json`,
`GATE_07_METRICS_V4.json`, `GATE_07_PROTOCOL.json`, `GATE_07_PROTOCOL_V2.json`,
`GATE_07_PROTOCOL_V3.json`, `GATE_07_PROTOCOL_V4.json`,
`GATE_07_PROTOCOL_V4_FREEZE_LEDGER.json` and `GATE_08_PROTOCOL.json` had been
normalised to LF by Git at an earlier commit. Their **committed bytes did not
hash to the value the frozen manifest records for them.** The working tree still
matched, which is precisely why every previous run passed: the freeze was
verified only against the machine that created it. For `GATE_07_PROTOCOL_V2.json`
the original mixed endings — 389 CRLF and 4 bare LF — cannot be reconstructed
from the blob by any `eol` setting, because the distinction was destroyed at
commit time.

**Resolution.** The bytes of the eight were restored to the form the frozen
manifest was taken over, and all 48 hash-asserted paths pinned with `-text` so
no checkout rewrites them again.

**Why this is a restoration and not an edit of frozen evidence.** The frozen
manifest is the authority; the artifacts had drifted from it, not the reverse.
Before staging, each of the eight was checked two ways: the parsed JSON before
and after is identical, and the two byte streams are identical after normalising
both to LF. The only difference is line endings. **The manifest itself was not
touched** — had we edited `GATE_19_FROZEN_SOURCE_HASHES.json` to match the
drifted artifacts, that would have been the exact move this paper argues against,
and it would have destroyed the evidence that the drift ever happened. After the
restoration, all 47 tracked manifest entries hash to their recorded values from
the committed blobs.

### F5 — REPRODUCE.md described a harness that no longer existed (severity: medium)

**Defect.** Section 8 cites `REPRODUCE.md` as the harness documentation. It
still described four stages, six unit tests, a "Real-Version MCP Negative
Control", and `gate10-paper-v1-20260911` as the canonical tag. Version 3 had
moved to five stages and ten tests, and had explicitly withdrawn the
negative-control reading. A reader following the paper's own pointer would have
been told the wrong thing about the instrument.

**Resolution.** Rewritten against the current harness, with the stage-2
limitation stated in its first section rather than buried.

### F6 — Package metadata, again (severity: low)

**Defect.** The version 3 README reported the build as 26 pages with one
error-level message. That was accurate for version 3. It is not for 3.2, and the
counts in earlier rounds were read from stdout, where these messages **do not
appear at all** — they are written only to `main.log`. A build can look clean on
stdout and carry three error-level messages in its transcript.

**Resolution.** The README now states 27 pages, 0 overfull hboxes, 19 underfull,
0 LaTeX warnings, and 3 `Infinite glue shrinkage` messages, read from `main.log`,
together with the fact that `pdflatex` exits 1 because of them. The three arise
at the end of the three appendix longtables; the version 3.2 text repaginates
them so three split where one split before.

---

## Part 0b — What version 3.2 deliberately did not do

- **The measurement archive was not published.** Distributing 107 MB of raw
  request ledgers and traces is a disclosure decision for the owner, not a
  packaging fix, and those files may carry prompt and response content. The
  limitation is declared instead. The recorded SHA-256 and byte size of all 87
  entries are already in the committed frozen manifest, so the archive is
  hash-attested in public even though it is not distributed.
- **`gates/artifacts/.gitignore` was not changed.** Committing the archive to
  Git would be the wrong mechanism even if the disclosure were agreed.
- **`GATE_19_FROZEN_SOURCE_HASHES.json` was not edited.** See F4.
- **`research/gate19/information_rights.json` was not edited.** Unchanged from
  version 3's reasoning: its commit is cited in the traceability appendix.
- **The superseded tag `gate22-paper-v3-20260914` was not moved or deleted.** It
  was pushed and therefore records what was claimed at that moment. Rewriting a
  published tag to make a later claim true is the move this paper argues against.
  The same applies to `gate22-paper-v31-20260916`, a superseded
  pre-submission state. `gate22-paper-v32-20260916` denotes this version. The
  traceability table lists the three tags that pin distinct things and names the
  two superseded ones in a single line rather than growing a row per attempt.
- **No measured value was recomputed.** The audit artifacts remain bit-identical.

---

## Part 0c — Verification performed for version 3.2

| Check | Result |
|---|---|
| Fresh clone, `core.autocrlf=true`, all five stages | exit 0; stage 2 `PASS (PARTIAL)` 47/134; stages 3 and 4 bit-identical; stage 5 structural match |
| Fresh clone, `--require-full-manifest` | exit 1, as designed |
| Owner working tree, default | 134/134 `UNCHANGED`, exit 0 |
| Owner working tree, `--require-full-manifest` | exit 0 |
| 47 tracked manifest entries vs committed blobs | 47/47 hash to recorded values (was 39/47) |
| 8 restored artifacts, parsed JSON before vs after | identical, 8/8 |
| 8 restored artifacts, bytes after LF-normalising both | identical, 8/8 |
| Three-pass `pdflatex`, read from `main.log` | 27 pages, 0 overfull, 19 underfull, 0 LaTeX warnings, 3 error-level `Infinite glue shrinkage` |

---

# Version 3: defect log and pre-submission audit

Prepared 2026-09-14 against manuscript version 2 (repository tag
`gate21-paper-v2-20260912`). The version 2 log follows below, unmodified.

Version 2 was audited against twelve failure categories before release and
passed. Version 3 exists because an external reviewer read the shipped package
— `main.tex`, the PDF, and the three JSON records, without access to the
repository — and found three things that self-audit had not. All three are
defects of **declaration**: the manuscript described its own instrument
inaccurately. None of them changed a measured value, and we established that
by measurement rather than by argument.

The honest summary is uncomfortable and belongs at the top. The paper's thesis
is that a benchmark's declared information rights should be a committed,
checkable artifact. Its own rights declaration had drifted from its
implementation for two releases, and the drift ran in the direction that
flatters the paper: the declared rule set looked cleaner than the implemented
one. We did not catch it. A reader with strictly less access than us did.

---

## Part 0 — Defects found in version 2

### E1 — The rights declaration under-declares the auditor's grammar (severity: high)

**Defect.** `research/gate19/information_rights.json` lists three
`observable_derivation_rules`: `identity`, `visible_split`,
`declared_external_derivation`. The committed auditor evaluates five operative
rules. Two are undeclared:

- `visible_literal` — a reachability rule: a string target occurring verbatim
  in the method-visible surface is accepted.
- the hidden-join detector — an unreachability rule: a target formed by joining
  two visible source values with a separator absent from the visible surface is
  rejected.

Manuscript version 2 stated "Derivability is decided by three declared rules"
(§3.2) and listed three.

**Evidence.** Read directly from `research/gate19/auditor.py::classify_item`,
whose decision chain is: target-field check → target-value check → `identity` →
`visible_literal` → hidden join → `visible_split` →
`declared_external_derivation` → fail-closed. A census of the committed
`gates/results/GATE_19_AUDIT.json` gives the fire counts:

| rule | status | fires |
|---|---|---|
| `identity` | REACHABLE | 225 |
| `visible_literal` | REACHABLE | **35** |
| `visible_split` | REACHABLE | **0** |
| hidden join | CONVENTION-UNOBSERVABLE | **40** |
| target-field undeclared | TARGET-ABSENT | 10 |

The undeclared reachability rule carries 35 of the 260 acceptances. The
declared rule it shadows never fires. Every one of the 40
convention-unobservable classifications — the substance of the headline — comes
from the other undeclared rule.

**Where the review needed sharpening.** The review described this as "four
derivation paths, paper says three". It is five operative rules against three
declared, and the more damaging half is the unreachability side, which the
review did not reach: the entire 40 rests on a rule the declaration covers only
by a general fail-closed clause.

**Fix.** Two parts, and the first was a decision about what *not* to do.

1. *The frozen rights file was not edited.* It is the artifact the frozen audit
   was produced under, and its commit is cited in the manuscript's traceability
   appendix. Editing it to make the paper's sentence true would have been the
   same class of act the paper criticises. The complete grammar is declared in
   a new committed artifact, `research/gate19/derivation_grammar.json`, which
   names all five operative rules, their fire counts, the fixed delimiter
   alphabet `visible_split` uses, and the evaluation order.
   `GATE_19_AUDIT.json` is bit-identical before and after.

2. *The result was tested for dependence on the undeclared rule*, not argued
   about. `research/gate19/ablation.py` re-runs all 310 items under four
   configurations and asserts, before reporting anything, that its default
   configuration reproduces the committed auditor item for item.

| | Configuration | reach | absent | conv. | unreachable |
|---|---|---|---|---|---|
| V1 | As committed | 260 | 10 | 40 | 50/310 |
| V2 | `visible_literal` removed | 260 | 10 | 40 | 50/310 |
| V3 | `visible_split` evaluated first | 260 | 10 | 40 | 50/310 |
| V4 | `visible_literal` scoped to source values only | 260 | 10 | 40 | 50/310 |

Per-family counts are identical across all four. V2 and V3 reassign exactly the
35 shadowed items to `visible_split` with no status change, which is the
structural reason for the invariance: `visible_literal` is strictly weaker than
`visible_split`, so anything the declared rule accepts the undeclared one
accepts too, and on this register the converse also holds.

Manuscript §3.2 now declares all five rules with their fire counts, §3.3 is a
new subsection reporting the defect and the ablation, §7.1 carries it as a
stated threat, and §7.4 answers it as a hostile question. Ledger records
`B01`–`B04`, `B07`, `B08`. Verification note `V08`.

**Impact on measured values: none.**

---

### E2 — The manuscript misdescribed how the auditor uses the rights object (severity: high)

**Defect.** Version 2 §4.1 said "For each item the auditor parses the rights
object and preserves the original record". It does not.
`classify_item(item, rights)` accepts the argument and never reads it;
`audit_items` reads only `rights["schema"]` to stamp the output. The auditor's
unit tests pass `{"schema": "test.rights.v1"}` and work fine, which is itself
evidence: a policy engine could not.

**Evidence.** `research/gate19/auditor.py`, function body. The `rights`
parameter appears in the signature and in no expression.

**Why this matters beyond wording.** §3.2 says "Changing `R` changes the audit
result, and it should." Read together with the false sentence, that implies a
run-time policy check the implementation does not perform, which would
overstate the generality of the artifact.

**Fix.** §4.1 now states the actual architecture: the rights declaration is
instantiated ahead of the audit by benchmark-specific builders, which
materialise the granted surface into a normalised register
(`visible_source_values`, `visible_text`, `new_contract_fields`); the auditor
verifies derivability over that register. The relativity claim is restated
correctly — changing `R` changes what the builders materialise — and made
executable by a new test,
`test_rights_instantiation_controls_the_visible_surface`, which withdraws a
source value from an item's granted surface and asserts the classification
flips from REACHABLE to UNREACHABLE-CONVENTION-UNOBSERVABLE. The manuscript now
says explicitly that an auditor generic over an arbitrary rights policy is not
claimed.

**Impact on measured values: none.**

---

### E3 — The external 20-pair sample was called a negative control (severity: high)

**Defect.** Version 2 contribution 3 was titled "A real-version negative
control" and concluded: "This shows the auditor does not classify ordinary
interface evolution as defective." The inference is circular for most of the
sample.

**Evidence.** `research/gate19/external_audit.py::build_audit_input` attaches
to every pair `{"status": "observable", "reason": pair["judgement_reason"]}`,
drawn from the register's hand-adjudication fields. The auditor accepts any
item whose external derivation is marked observable. Running the register shows
the split:

| | REACHABLE | by rule |
|---|---|---|
| As published | 20/20 | 15 `declared_external_derivation`, 5 `visible_literal` |
| Annotation withheld | 5/20 | 5 `visible_literal`; 15 fail-closed |

**Where the review overstated, and where it understated.** The review said the
result was 20/20 circular. It is 15/20 — five pairs are accepted by a
mechanical rule with no annotation, which is a real if small independent
result. But those five are weaker than the count suggests, and the review did
not see this: in three of them the target value *is the new tool's own
registered name*, which necessarily appears in the diff that registers it; a
fourth target is the schema status word `required`, and the fifth a resource
description string. They are true mechanical derivations under the declared
grammar, and three of them are near-tautologies.

A note on how this correction was caught, since it bears on the paper's own
thesis. The "four of five" figure was written from a reading of the five pair
records, and a verification script written afterwards — which re-derives every
v3 numeric claim from the committed artifacts rather than from the prose —
found it to be three. The same script also caught a `\ledger` macro corrupted
by an editing pass. Both were fixed before release. This is the third time in
this project that a plausible number survived a human read and was caught only
by a mechanical re-derivation.

**Fix.** The specificity claim is withdrawn, not softened. Contribution 3 is
retitled "A hand-adjudicated external sample" and states the 15/5 split and the
annotation-withheld result in its own text. §5.3 is rewritten, says plainly
that the earlier conclusion does not survive inspection, characterises the five
mechanical acceptances as the floor of what the sample establishes, and names
the strengthening it actually needs — a subset decidable without
`declared_external_derivation` — while explicitly not claiming that subset's
result in advance. The abstract, the "what this paper does not claim" box, the
Figure 2 panel, §4.2, §7.1, and the hostile-questions list are all updated.
Ledger records `B05`, `B06`. Verification note `V09`.

**Impact on measured values: none.** The published 20/20 is unchanged; what it
supports is narrower.

---

### E4 — Related Work omitted the nearest literature (severity: high)

**Defect.** Version 2 positioned against four literatures: agent adaptation,
drift benchmarks, MCP evaluation, and API migration. It cited nothing from
benchmark-validity auditing, which is where its own contribution sits.

**Fix.** A new §2.1, "Benchmark-validity auditing", citing six works verified
on 2026-09-14, and the count of literatures changed from four to five. The
closest is Bhat et al. (arXiv:2607.02577, cs.SE, 2026-06-30), a validity audit
of BFCL v4, τ²-Bench, LiveMCPBench and MCP-Atlas reporting 92 evaluator-human
disagreements across 496 expert-reviewed tasks. Also added: Wang et al.
(arXiv:2605.26079), Mohl et al. (arXiv:2607.27518), Wang et al.
(arXiv:2605.12673), Zhu et al. (arXiv:2507.02825), and — as concurrent work —
Zhang et al. (arXiv:2609.09218).

The section states the distinction we can defend and disclaims the ones we
cannot. Prior audits read evidence that exists only after a trajectory has been
produced and ask whether the score was right; this criterion runs before
execution and asks whether the expected answer is determined. Explicitly
disclaimed: priority over benchmark-validity auditing, and any claim to be
first to find incorrect ground truths in an agent benchmark — Wang et al. and
Bhat et al. both report that class. The "what this paper does not claim" box
carries the disclaimer too.

One contrast is worth its own line because it is exact rather than rhetorical.
Mohl et al. scan for *ground-truth access*: oracle information an agent can
reach but should not. This paper measures the mirror failure on the same axis:
oracle information the agent cannot reach but must. An audit suite checking
only the leakage direction passes every item in the `argument_merge` family.

**Verification standard, stated because it is weaker than version 2's.** All
six were verified by retrieving the arXiv abstract page and reading title, full
author list, submission date, primary category, and abstract. Every figure
attributed to them is quoted from that abstract. Full texts were not read, so
they are cited for the claims their abstracts state and for positioning, not
for methodological detail. Recorded in Appendix G and in
`REFERENCES_VERIFIED.json`.

---

### E5 — "No agent can produce the target except by guessing" overstates (severity: medium-high)

**Defect.** The version 2 introduction claimed impossibility. A pretrained
model carries a prior over naming conventions that is outside the benchmark's
information rights but inside the model, so the target may well be emitted. The
paper's own diagnostic probe tests one model and finds it does not — good
evidence about that model, not a proof.

**Fix.** The claim is restated as identifiability, which is both weaker and
more damaging to the benchmark: the evidence the benchmark supplies does not
determine the target, so a method that produces it did so from information the
benchmark did not provide, and the item's score is not attributable to the
capability it claims to measure. The abstract now defines *oracle
identifiability under declared information rights*. The introduction states the
distinction and points at the probe as evidence rather than proof.

---

### E6 — Reachability was not stated as relative to a derivation grammar (severity: medium)

**Defect.** `Reachable(g | R)` reads as a claim about derivability from `R`.
The auditor is not a theorem prover: it recognises a finite rule set and
nothing else. Case folding, JSON re-serialisation, arithmetic, hashing,
template concatenation, and unit normalisation are all undecided by it, and
under the fail-closed rule an item needing one is classified unreachable.

**Fix.** The criterion is now `Reachable(g | R, G_R)`, with `G_R` a committed
artifact alongside `R`. §3.2 adds a third boundary paragraph listing the
transformations the grammar does not decide and stating the direction of the
resulting bias: the criterion errs toward calling items defective, and a richer
grammar could only lower the reported rate. §7.1 carries it as a threat,
including the argument we believe but have not measured — that the 40 join
failures would survive a richer grammar, since no grammar derives a symbol it
has never seen — labelled as an argument rather than a result.

---

### E7 — Package metadata was stale or wrong in six places (severity: medium)

**Defect and evidence.** A fresh three-pass build of the version 2 `main.tex`
and a reread of the shipped JSON found:

| Claim in the version 2 package | Actual |
|---|---|
| README: "18 pages" | 21 pages |
| README: "0 errors, 0 LaTeX warnings" | 7 overfull hboxes (largest 60.93pt); 3 `! Infinite glue shrinkage` messages |
| README: author block "carries a placeholder" | Author block set to Nguyen Thanh Dat, Ton Duc Thang University |
| README: addendum has "seven numbers" | 9 claim records |
| README: addendum has "five verification notes" | 7 verification notes |
| Checklist Comments field: `gate10-paper-v1-20260911` | That is the evidence freeze, not the manuscript tag |

The reviewer caught the page count, the placeholder, and the tag. The two
addendum miscounts and the error-level messages were found during this
revision.

**Fix.** All six corrected against a fresh build. The README now states the
build exactly, including the `Infinite glue shrinkage` message reproduced in
full, with the bisection result showing it reproduces on a bare
`\documentclass{article}` + `\usepackage{longtable}` document and is therefore
not content-caused. §8 separates the three tags in a table. `main.pdf` is no
longer shipped, which removes the "do not upload this" failure mode entirely.
Verification note `V10`.

---

### E8 — Formatting (severity: low)

Seven overfull hboxes in version 2, largest 60.93pt. Fixed by splitting three
table header rows across two lines, breaking a long case-identifier list and a
long command line, shortening two ledger locators, and adding break
opportunities to one long small-caps status name. Version 3 builds with **0
overfull hboxes**. The abstract's minimum-detectable-difference figures were
moved to §5.7 and replaced with a statement of the criterion that was failed,
since the paper's own threats section says the interval width rather than the
MDE is the decisive quantity.

---

## Part 0b — What version 3 deliberately did not do

- **Did not edit the frozen rights file**, for the reason in E1.
- **Did not re-run any model.** No provider was contacted during this revision.
  The diagnostic probe's 60 requests remain the only provider contact in the
  project, unchanged.
- **Did not rebuild the auditor as a policy engine.** That would make the
  rights object genuinely executable and is the right long-term design, but it
  would invalidate the frozen audit and is not needed for the claims made here.
  §4.1 states what is claimed instead.
- **Did not build the annotation-free external subset.** It is named in §5.3 as
  the strengthening the sample needs, with no promise about its result.
- **Did not withdraw or restate the 50/310 finding**, because four rule
  configurations return it unchanged.

## Part 0c — Reproduction after the version 3 changes

`scripts/reproduce.py` now runs five stages and ten unit tests. Verified
2026-09-14:

```
[1/5] 10 offline unit tests                      PASS
[2/5] 134/134 frozen input files UNCHANGED       PASS
[3/5] 310 items: 260 / 10 / 40, SHA-256 match    BIT-IDENTICAL
[4/5] 20 external pairs, SHA-256 match           BIT-IDENTICAL
[5/5] 4 ablation configurations, all 260/10/40   INVARIANT
```

The two audit artifacts are byte-identical to their committed counterparts
after every change described above. That is the evidence for "no measured value
changed", and it is the reason the frozen rights file was left alone.

---

# Version 2: defect log and pre-submission audit

Prepared 2026-09-12 against manuscript version 1
(`paper/main.tex`, repository tag `gate10-paper-v1-20260911`).

This file records (1) every defect found in version 1 and what was done about
it, and (2) the audit of version 2 against the twelve failure categories the
owner specified. It is part of the provenance trail: a reviewer who wants to
know what was checked, and what was found, should be able to read it here
rather than take the manuscript's word for it.

---

## Part 1 — Defects found in version 1

Each item states the defect, the evidence that established it, and the fix.

### D1 — Citation error: missing co-author (severity: high)

**Defect.** Reference `dig2006api` was listed with a single author, Danny Dig.

**Evidence.** The published article's title page, read from the author-hosted
copy at `dig.cs.illinois.edu/papers/JSME_API_Evolution.pdf`, lists
**Danny Dig and Ralph Johnson**, both at the Department of Computer Science,
University of Illinois at Urbana-Champaign. The publisher DOI returned HTTP
403 to automated retrieval, which is why version 1's metadata check — which
resolved the DOI but could not read the record — did not catch it.

**Fix.** Author list corrected in the bibliography and in
`REFERENCES_VERIFIED.json`. The correction is also stated in the manuscript's
Appendix E, because a paper whose thesis is traceability should not silently
repair its own citation record.

**Related near-miss.** A web search for the same article surfaced two
conflicting figures for the share of breaking changes that are refactorings:
"over 80%" and "94%". The primary source states **over 80%**. The manuscript
quotes only that figure. Had the 94% been taken from the search summary, this
would have been a fabricated statistic with a real citation attached — the
exact failure mode of category 2.

### D2 — Unverified content claims about a cited work (severity: high)

**Defect.** Version 1 described `assidiqi2026referencefree` as injecting
controlled drift "using a known bijective inversion manifest" and as
"explicitly separating adaptation after the drift mapping is available from
autonomous detection plus adaptation". Version 1's Figure 2 additionally
placed an "IEEE normalization" row in the information-rights comparison,
asserting specific values for that system's old-trace, migration-map, and
probing rights.

**Evidence.** `REFERENCES_VERIFIED.json` v1 recorded only that the DOI
resolved and the indexed metadata matched. No primary reading of the abstract
or full text is recorded anywhere. Retrieval was attempted again during this
revision: IEEE Xplore returned no content to automated fetch, and a targeted
search surfaced no accessible primary copy.

**Fix.** Both prose claims removed. The figure row removed rather than kept
with a hedge — an unverified row in a comparison table is load-bearing whether
or not a caveat sits beneath it. The work is now cited at the level its title
and indexed metadata support. The verification limit is stated in
Appendix E of the manuscript, not buried in a JSON file.

### D3 — Mixed denominators in a single clause (severity: medium)

**Defect.** Version 1's Contribution 1 read: "independently reproduces the
10/35 target-absent and 5/15 hidden-convention findings." The two fractions
have different units. 10/35 counts **argument-pair items**; 5/15 counts
**graded cases**. A reader could reasonably infer that 15 of something was the
denominator for both, or that 5/15 was a subset of 35.

**Evidence.** Ledger claims C043 ("10/35 target-absent *tool_replacement pair
findings*") and C044 ("5/15 graded *tool_replacement cases*"). The C2 family
table in `GATE_19C_RESULT.md` records 10 convention-unobservable **pair items**
in that family, not 5 — a third number that the same sentence could be
mistaken for.

**Fix.** Section 3.1 of version 2 defines graded case, argument-pair item, and
required-field item explicitly before any result appears, and every count in
the manuscript names its unit. The two findings are now stated separately.

### D4 — Broken internal promise (severity: medium)

**Defect.** Version 1's body read "commit `653aa81` (full SHA in the
reproducibility appendix)", but the appendix listed short SHAs only. The
promised full hashes appeared nowhere in the document.

**Fix.** Appendix C of version 2 gives the full 40-character commit hash for
every cited artifact.

### D5 — Inconsistent commit identifier (severity: low)

**Defect.** `research/gate19/auditor.py` was cited as commit `6adf136b` in the
body and `6adf136` in the appendix table — 8 hex characters in one place, 7 in
the other, for the same object.

**Fix.** All commit identifiers in version 2 are full 40-character hashes,
verified with `git log -1 --format=%H -- <path>` for each file.

### D6 — A propagated hash transcription error (severity: medium)

**Defect.** `GATE_19_RESULT.md` section O0 records the SHA-256 of
`GATE_19_FROZEN_SOURCE_HASHES.json` as `...5e55b8e2eb...`. The committed file
digests to `...5e55e8d2eb...`. Two characters are transposed in the prose
summary. The ledger record C045 and `GATE_19C_RESULT.md` both carry the
correct value, so the repository contains two different digests for one file.

**Evidence.** Digest computed directly over the committed file:
`e2e7ed915e55e8d2eb57378a3b53ebf106bc8d3c4141c7b6791d652c5c86e115`.

**Fix.** The manuscript cites the verified digest and records the discrepancy
explicitly in Appendix C. A traceability scheme that tolerates an unexplained
hash mismatch is not doing the job it claims to do, so this is stated rather
than quietly resolved. Recorded as `V02` in `EVIDENCE_LEDGER_ADDENDUM.json`.

### D7 — A caveat lost between artifact and manuscript (severity: medium)

**Defect.** `GATE_19C_RESULT.md` states under Limitations: "The power
calculation is a planning analysis over retained argument-pair item counts,
while first-attempt execution is case-level; this mismatch is reported
explicitly." Version 1 of the manuscript did not carry that limitation.

**Why it matters.** This is the classic multi-agent summarisation failure: a
caveat present in the source artifact is dropped when the result is written up,
and the write-up then reads as more confident than the evidence. Here the
omission was in the paper's favour in one direction and against it in another,
which is precisely why it needed stating rather than judging.

**Fix.** Section 7.2 of version 2 states the unit mismatch, and states which
way it cuts: because case-level retention is strictly lower than item-level
retention on the affected families, the mismatch makes the cancellation
decision more conservative, not less.

### D8 — Under-reported second measurement surface (severity: medium)

**Defect.** Version 1 mentioned the required-field audit only through its
consequence (0/15 strict complete-call retention) and never gave its totals.
The audit covers 45 items and finds 20 of them unreachable — a second,
independent defect surface with its own denominator.

**Fix.** Section 5.2 of version 2 reports the required-field audit in full,
with per-family figures and the literal values involved. Recorded as `A01` in
`EVIDENCE_LEDGER_ADDENDUM.json`.

### D9 — Reproducibility detail omitted (severity: low)

**Defect.** Version 1 described the diagnostic probe without naming the model,
and described the power anchors without naming the baseline arms. Neither could
be reproduced or challenged from the manuscript alone.

**Fix.** Version 2 names the probe model
(`nvidia/nemotron-3-super-120b-a12b:free`), its rate governor (3.2 s minimum
interval, 19 rpm, no fallback, reasoning effort disabled, 60-request budget),
and the four baseline arms with their model identifiers
(`llm_old_new_history` on `openai/gpt-oss-120b`, `llm_reasoning` on
`openai/gpt-oss-20b`, `lexical_name` deterministic offline). Recorded as `A04`
and `A05`.

### D10 — Selective omission of an inconvenient number (severity: medium)

**Defect.** The diagnostic probe has two strata. Version 1 reported the
`::` emission rate for both (0/28 and 0/29) and omitted the exact-gold rate,
which is 0.0000 in the hidden-sandbox stratum but **0.1379 (4 of 29)** in the
arbitrary-separator stratum. The omitted number is the only figure in the
probe that complicates a clean null reading.

**Why it was omitted.** Not, as far as we can tell, deliberately: the frozen
Gate 10 ledger has no record for it, and the ledger's own policy says any
number without a record must be removed before commit. The rule designed to
prevent fabrication also, in this one case, removed a true and relevant
observation.

**Fix.** Version 2 reports it, notes that 0.1379 sits close to the
pre-registered chance baseline of 1/9 = 0.1111, and states that n = 29 cannot
distinguish the two. The ledger is extended rather than the number dropped.
Recorded as `A02`.

### D11 — Bitmap figures with unreadable provenance (severity: low)

**Defect.** Version 1 shipped three PNG figures generated by a script. The
values inside them could not be read from the manuscript source, the
information-rights figure contained the unverified row described in D2, and a
raster figure in a preprint is a known submission hazard.

**Fix.** Version 2 renders every figure natively in LaTeX/TikZ. The source has
no external image dependency, and every value in every figure is readable as
text in `main.tex`. Recorded as `V05`.

---

## Part 2 — Version 2 audit against the twelve failure categories

### 1. Factual errors

Every numeric claim was read from its committed artifact during this revision
rather than carried over from version 1's prose. The per-family reachability
table was re-derived independently from the machine-readable auditor output
(`GATE_19_AUDIT.json`) and cross-checked against the prose table in
`GATE_19C_RESULT.md`; all figures match (`V01`). Arithmetic checks performed:
310 designed pairs sum across families; 260 reachable sum across families;
50 = 10 target-absent + 40 convention-unobservable; 50/310 = 16.1%;
45 = 15 + 5 + 25 required-field items; 146 = 99 + 30 + 17 hash inventory;
85 = 17 baseline arms x 5 affected cases; 57 = 28 + 29 valid JSON outputs;
p_bar values reproduce from the arm rates; the pooled p_bar reproduces as a
retained-n weighted mean.

No date, dataset name, or sample size is stated that is not in a cited
artifact. No third-party result is restated as our own.

### 2. Citation not supporting the claim

Every reference was re-checked at two levels: bibliographic metadata, and the
specific statement the manuscript makes about it. Seven of nine were verified
at both levels by reading the primary abstract or full text. Two carry a
narrower status and say so. One author list was corrected (D1). One set of
content claims was removed as unverified (D2).

Where the manuscript draws its own inference from a cited result — the
BigBag 78.6%-vs-33.3% transfer argument, and the observation about effect
scoring in DynamicMCPBench — the text marks it as the authors' analysis rather
than attributing it to the source.

### 3. Weak evidence synthesis

Related Work is organised by what each literature grants the evaluated system,
not by paper. Each subsection ends with the specific relationship to this
work: probing methods hold different rights (§2.1); schema-hiding relocates
the rights boundary rather than removing it (§2.2); effect scoring loosens the
path while reachability auditing validates the target (§2.3); source migration
holds information an agent scored before its first call does not (§2.4).
Disagreements are not manufactured; no cited work is described as wrong.

### 4. False novelty

The manuscript states in a boxed paragraph on page 1 what it does not claim.
MCPEvol-Bench is cited explicitly as preceding this work. The criterion is
described as adjacent to test-set validity, not as a replacement for it, and
what is claimed as new is narrowed to the operational parts: a declared rights
object, per-item derivability auditing, typed failure classes, a fail-closed
rule, and a committed implementation. The words "first", "novel",
"state-of-the-art" and "outperforms" do not appear as claims anywhere in the
manuscript.

### 5. Logic and argumentation

The central negative result is stated as a design decision, not a null
finding: no comparison ran, so no equivalence is claimed. The three-way
distinction between derivability, semantic correctness, and capability is
stated explicitly in §3.3, and the criterion is described as necessary but not
sufficient. The asymmetry between `argument_split` (clean) and
`argument_merge` (wholly unreachable) is explained by a mechanism — the
delimiter is present in the observed value for splitting and absent for
joining — rather than reported as a bare contrast.

The one place where a causal story was previously asserted (the RISK-0022
mechanism claim) is now the subject of §5.5, which shows the story was wrong
and replaces it with the scorer-granularity explanation the raw rows support.

### 6. Methodology and reproducibility

The manuscript states: the declared information rights and their four granted
artifacts; the eight excluded artifact classes; the three derivation rules; the
fail-closed rule; the three auditor statuses and the order in which checks are
applied; the exclusion policy and its additive nature; the probe's model, rate
governor, budget, and reasoning setting; the four baseline arms and their model
identifiers; the frozen statistical decision rule with alpha, target power,
and effect size; and the hash-manifest verification at both gate closures.

Pre-registration is documented: the criterion and exclusion policy were frozen
in one gate, the power rule in the next, before any power number was computed.

### 7. Statistics

MDE is defined where it first appears (smallest absolute arm difference
detectable at alpha = 0.05 with power 0.80 at the stated n). Absolute
differences are never described as relative. Wilson intervals are reported with
their full widths, and the observation that the zero-success interval at n = 15
is already wider than the entire pre-registered effect band is stated as the
decisive fact rather than the MDE table alone. The unit mismatch between the
pair-level power analysis and case-level execution scoring is disclosed (D7),
with its direction stated. No p-value is reported anywhere, and no result is
called "significant".

### 8. Internal inconsistency

Checked mechanically and by reading: the abstract's figures against the
results sections; the four contributions in §1.3 against the four objects in
the conclusion; every denominator against §3.1's definitions; every table
caption against its table; every figure caption against the values inside the
figure; every `\ref` resolved (final compile reports zero LaTeX warnings, so
no undefined or multiply-defined labels and no unresolved citations); every
`\cite` key present in the bibliography and every bibliography entry cited.

Acronyms and names are stable: the three statuses, the three item units, and
the family names use one spelling throughout.

### 9. Multi-agent error propagation

This was the most productive category. Four of the eleven defects above are
propagation failures rather than authoring failures: a caveat dropped between
artifact and write-up (D7); a hash transcribed wrongly in one artifact and
correctly in two others, with the manuscript free to pick either (D6); a
mechanism claim that survived in a risk register for weeks because nobody
re-read the rows (§5.5 of the manuscript); and a number omitted because a
well-intentioned rule required it (D10).

The countermeasure applied here is that no number was accepted from version 1's
prose. Each was re-read from the artifact the ledger names, and where two
artifacts disagreed, the file itself was hashed and the discrepancy recorded.

### 10. Writing

Every section opens on specific content. The manuscript opens on a concrete
register item with real values rather than on the state of the field. No
paragraph consists only of source summary. Filler transitions were removed.
Claims of the form "plays a crucial role" or "performs excellently" do not
appear. Hedging is calibrated: "we claim", "we do not claim", "this shows",
and "this does not show" are used deliberately and differently.

The conclusion does not paraphrase the abstract; it states what the audit cost
and what a benchmark author should do about it.

### 11. Scope and claims

Generalisation boundaries are stated four times: in the boxed paragraph on
page 1, in Contribution 3, in §5.3 on the control, and in §7.1. The
self-authored provenance of the benchmark is named as the central limitation
rather than listed among others. The self-audit problem — auditor, benchmark,
and corrected register all originating with the same authors — is stated in
§7.3, along with the observation that pre-registration and hash freezing do not
substitute for a second party running the auditor.

### 12. Document integrity

Compiled clean: 0 errors, 0 LaTeX warnings, 18 pages. All figures and tables
are referenced in the text. No placeholder text (`[REF]`, `[X%]`, `TODO`,
"insert figure here") remains; the one intentional placeholder is the author
block, which names itself as the owner's to supply. No meta-text from the
drafting process survives. No Markdown syntax leaked into the LaTeX. Citation
style is uniform. The bibliography has no duplicates. The one non-ASCII author
name is encoded as a LaTeX accent macro rather than a raw byte.

An AI-use disclosure appears as Appendix F, consistent with ICMJE and COPE
guidance that AI cannot be an author and that generative-AI use in manuscript
preparation should be disclosed.

---

## Part 2b — Hostile pre-submission self-audit of version 2

Version 2 was then audited again, this time against an arXiv-oriented hostile
review protocol rather than the twelve-category list. It found five further
defects in version 2 itself. They are recorded here because a paper arguing
for self-auditing should show what its own self-audit caught.

### S1 — Unearned "independently" (severity: high)

**Defect.** Contribution 1 read "Running the auditor independently reproduces
the two findings that originally motivated it", then gave both the 10/35
target-absent count and the 5/15 convention count.

**Evidence.** `research/gate08/metrics/diagnostics.py` contains an earlier
`oracle_reachability()` whose entire test is
`new_arg not in fields.get(new_tool, set())`. It detects the target-absent
class and nothing else. So two independent implementations do agree on 10/35 —
but the manuscript never told the reader that a prior implementation existed,
leaving "independently" with nothing to refer to. For the convention class the
word was simply wrong: the earlier diagnostic cannot detect it, and the 5/15
had been established by reading the sandbox source, not by an independent
check.

**Fix.** Contribution 1 now names the earlier diagnostic, states what it can
and cannot detect, and separates the two claims: agreement between two
implementations on the first class, mechanisation of the second. Recorded as
`A09`.

### S2 — The generator was never described (severity: high)

**Defect.** The paper's central argument is that a *generator* produced
unreachable oracles, yet Section 4.2 described the sandbox only as
"self-authored and deterministic". A reader could not tell whether the 50
failures were systematic generator behaviour or scattered authoring slips —
which is exactly what determines how much the result means.

**Evidence.** `research/gate07/dataset/operators.py` is a 291-line operator
library with `GENERATOR_SEED = 20260827`, `GRADED_PER_FAMILY = 15`, and
`HELD_OUT_PER_FAMILY = 3`. The held-out split existed and was never mentioned,
despite train/test separation being a standard methodology checkpoint.

**Fix.** Section 4.2 now states the generator, the seed, the per-family counts,
the held-out split, and quotes the sandbox code path that produces the `::`
separator. This strengthens the result rather than weakening it: the failures
are the systematic output of two mutation operators, which is why they cluster
perfectly instead of appearing at low rates everywhere. Recorded as `A08`.

### S3 — "Perfectly clean" contradicted by a table on the same page (severity: medium)

**Defect.** Section 5.1 said "nine of eleven families are perfectly clean"
while Table 2's rightmost column, directly above, showed
`added_required_field` retaining 0 of 15 strict cases.

**Fix.** The sentence now says "on this surface nine of eleven families are
clean", states explicitly that clean-on-this-surface is not clean, and
forward-references Section 5.2.

### S4 — The total row mixed denominators (severity: medium)

**Defect.** Table 2's total row gave 180 graded cases (12 families) alongside
310 pair items (11 families). In a paper whose stated thesis includes unit
discipline, that is an unforced error.

**Fix.** The row is now labelled "Total (11 pair families)" with 165 cases, so
every column in it refers to the same population; the caption states the
12-family, 180-case totals separately.

### S5 — A recommendation presented as a finding (severity: low)

**Defect.** Section 5.4 called the suggestion that benchmarks publish their
correspondence register "a small, concrete finding". It is a recommendation
derived from one failed attempt on two releases.

**Fix.** It is now labelled a recommendation, with the basis stated.

### Also added, not defects

- **Statistical honesty about the power model.** Section 7.2 now states that a
  two-sample normal approximation is untrustworthy at $n=15$ with an observed
  rate of zero, and that the decision rests on the interval width rather than
  the MDE. The MDE table is presented as what the frozen rule computed, not as
  a valid approximation at these counts.
- **A re-run command.** Section 8 now gives the exact invocation of the
  auditor, which the manuscript previously described as re-runnable without
  saying how.
- **Three source files added to the provenance table**:
  `research/gate08/metrics/diagnostics.py`,
  `research/gate07/dataset/operators.py`, and
  `research/gate07/sandbox/operations.py`.

### Checked and found sound

Repository public and browsable; tag `gate10-paper-v1-20260911` present on the
remote and resolving to `ff5e2b15…`, matching the manuscript. Abstract 244
words / 1649 characters, inside arXiv's 1920-character metadata limit. Every
abstract and conclusion claim traced to a Results subsection; none stronger
than its evidence. Citations and bibliography match in both directions. No
undefined references, no orphaned labels. Sentence-length distribution varied
(median 18, range 4–68). No `Moreover`/`Furthermore`/`Additionally` filler. No
"novel", "unique", "SOTA", or "outperforms" used as a claim. arXiv's current
policy — significant text-to-text generative AI use must be reported, and AI
cannot be an author — is satisfied by Appendix F.

## Part 3 — What remains open

These are not defects; they are limits a reviewer should know about.

1. **`assidiqi2026referencefree` content is unverified.** If the full text
   becomes available, §2.2 and Table 1 can be extended. Until then no content
   claim should be reinstated.
2. **No independent reproduction.** The auditor has not been run by anyone
   outside the project. This is stated in §7.3 and is the single most valuable
   thing a reader could do with the artifact.
3. **Author block is a placeholder.** Names, affiliations, ORCIDs, and the
   corresponding author must be supplied before submission.
4. **No licence is asserted in the source.** The arXiv licence choice is
   irrevocable per version and is the owner's decision; see
   `ARXIV_CHECKLIST.md`.
5. **Two references were verified from abstracts, not full text**
   (`chen2025toolevo`, `wu2026contda`). The manuscript's claims about them are
   confined to what those abstracts state directly.
