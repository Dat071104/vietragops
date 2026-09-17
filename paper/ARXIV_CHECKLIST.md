# arXiv preparation checklist — manuscript version 3.5

Prepared 2026-09-16. **This package does not submit anything.** Submission is
the owner's separate action.

## Recommended metadata

| Field | Value |
|---|---|
| Title | `Unreachable Oracles: Auditing Ground-Truth Derivability in a Synthetic Tool-Drift Benchmark for LLM Agents` |
| Abstract | Copy the abstract from `main.tex` exactly. Strip the LaTeX markup (`\emph`, `\texttt`, `\dfam`, `\%` → `%`) — arXiv's metadata field is plain text. |
| Authors | **Nguyen Thanh Dat**, sole author. Affiliation: Ton Duc Thang University, Ho Chi Minh City, Vietnam. Set in `main.tex`. No AI system is listed as an author. |
| Contact email | Use the **institutional address** (`@student.tdtu.edu.vn`) for the arXiv account, not a personal one — it is what makes endorsement straightforward. The address goes in arXiv metadata only; the manuscript deliberately carries name and affiliation without an email, so there is no placeholder to forget. |
| ORCID | Optional but recommended. Free to register at orcid.org and it permanently disambiguates the name, which matters for a common Vietnamese name. |
| Primary category | `cs.SE` (Software Engineering) — the central claim is benchmark validity, auditing, and software/API evolution measurement. |
| Cross-lists | `cs.CL` (LLM-agent and tool-use readership), `cs.AI` (agent evaluation). |
| Alternative | `cs.CL` as primary if NLP review context is preferred. This changes the readership, not the paper's scope or claims. |
| ACM/MSC class | Leave blank unless a target venue requires one. |
| Comments field | `31 pages, 2 figures. Measurement and benchmark-validity case study. Manuscript artifact tag: gate22-paper-v35-20260917. Measurement evidence frozen at gate10-paper-v1-20260911.` |
| Artifact URL | `https://github.com/Dat071104/vietragops` |
| Licence | **`CC BY 4.0`** — decided. Rationale and the one caveat are below. |

**Title note.** The title is unchanged from version 2. Version 2 changed the subtitle from "Synthetic Tool-Drift
Benchmarks" (plural) to "a Synthetic Tool-Drift Benchmark" (singular). The
plural implied a result about a class of benchmarks; the paper measures one.
The singular is what the evidence supports.

## Files to upload

Upload **`main.tex` only.**

The manuscript has no `.bib` dependency (the bibliography is inline as
`thebibliography`) and no image dependency (all figures are TikZ). Nothing else
in this package belongs in the arXiv submission:

- `CHANGES_AND_AUDIT.md`, `EVIDENCE_LEDGER_ADDENDUM.json`,
  `REFERENCES_VERIFIED.json`, `README.md`, and this checklist are provenance
  records for the authors and the repository, not part of the paper.
- **No PDF is shipped with version 3.5, and none should be uploaded.** arXiv
  compiles `main.tex` itself and asks that generated output not be included
  alongside the source, so a `main.pdf` next to `main.tex` is both unnecessary
  and an invitation to submit the wrong file. Version 2 shipped one and had to
  warn against it; version 3.2 shipped none; version 3.3 shipped one under
  `build/` with a warning; versions 3.4 and 3.5 ship none. The version 3.5
  release archive is `main.tex` and nothing else, which makes the archive the
  submission rather than a package containing it.
- Do not upload `main.aux`, `main.log`, `main.out`, `main.toc` or any other
  build by-product. arXiv strips or rejects them, and a local three-pass build
  leaves all of them in the directory.
- Do not upload raw gate artifacts, `_agent_ops/` files, or anything from the
  deployment.

Run arXiv's **Check Files** step and confirm it detects `main.tex` as the
top-level TeX file.

## Endorsement

arXiv requires endorsement before a user's first paper, and separately for a
first submission to a new category. An institutional email address can expedite
this. Without one, the submitting author may request personal endorsement from
an established arXiv author in the subject area.

1. Register and verify the submitting author account; select the intended
   primary category.
2. Start a new submission so arXiv issues an endorsement request if it needs
   one.
3. Identify a qualified endorser from related arXiv papers — preferably someone
   known personally and working in the area. Do not mass-contact candidates.
4. Send the six-character endorsement code through the arXiv form.
5. Repeat for any additional category that requires separate endorsement.

One positive endorsement is required per endorsement category. The endorser
checks topical appropriateness. **Endorsement is not peer review**, and the
manuscript says so about itself.

Source: <https://info.arxiv.org/help/endorsement.html>

## Licence — decided: CC BY 4.0

**Why this one.** The paper's entire argument is that other benchmark authors
should run this audit on their own ground truth. A licence that restricts
reuse would work against the contribution. CC BY 4.0 permits redistribution,
adaptation, and commercial reuse with attribution, and the repository it points
at is already public. The author is sole author and owns the rights to
everything in the manuscript, so there is no co-author or employer consent to
obtain.

**The one caveat, stated plainly.** The choice is **irrevocable for that
version**. It cannot be narrowed later; the only remedy is submitting a new
version under a different licence, which does not retract the first. If this
work is ever extended into a journal submission, check that venue's policy on
prior CC BY posting first — most in software engineering accept it, but confirm
rather than assume.

**If in doubt**, arXiv's non-exclusive licence to distribute is the
conservative alternative: it still allows arXiv to host the paper but reserves
everything else. It is the weaker choice for this particular paper's purpose,
and is noted only so the decision is made knowingly.

Source: <https://info.arxiv.org/help/license/index.html>

## Upload checklist

- [x] Author block set: Nguyen Thanh Dat, Ton Duc Thang University. No AI
      system listed as an author.
- [x] Correspondence address on the title page and in Section 8:
      `nguyentdat071104@gmail.com`, added in version 3.5. Versions 1 through
      3.4 carried none, which left a paper that invites a reader to dispute its
      numbers with no address to dispute them to. Confirm this is an address
      that will still be read years from now, because a preprint outlives a
      mailbox.
- [x] Build verified: 31 pages, 0 overfull hboxes, 19 underfull, 0 LaTeX
      warnings, 0 undefined references. Three benign `Infinite glue shrinkage`
      messages from longtable page splitting, at source lines 1782, 1836 and
      1886, which make `pdflatex` exit with status 1 while still producing a
      correct PDF; see README for the bisection that shows they are not
      content-caused. Read these counts from `main.log`, not from stdout —
      they never appear on stdout. Version 3.5 added one page, from the extra
      row in the Section 8 tag table; the repagination splits the Appendix D
      ledger table across a page again, which is where the third glue message
      comes from. It introduced no overfull box.
- [x] PDF document metadata set via `\hypersetup`: title, author, subject,
      keywords. Previously blank. This affects the rendered file only; arXiv
      takes its own metadata from the submission form, so the two must still be
      kept consistent by hand.
- [x] Bibliography: 19 entries, all verified against a primary record on
      2026-09-12, 2026-09-14, 2026-09-16, or 2026-09-17. Verification levels
      recorded per reference in `REFERENCES_VERIFIED.json`. One entry
      (`suh2026agentsuite`) rests on an ICML 2026 conference programme entry
      rather than a publisher PDF or arXiv record; that is disclosed in its own
      entry and in Appendix E. One entry (`li2026genebench`) is verified from
      its full text, which is a stronger standard than the rest of the 2026
      references received.
- [ ] Confirm your university has no policy requiring notification before an
      affiliated preprint is posted. Most do not; it takes one email to check,
      and it is much easier to ask before than to amend after.
- [ ] Confirm the title matches the metadata field exactly, including the
      singular "Benchmark".
- [ ] Paste the abstract as plain text; confirm no LaTeX markup survived.
- [ ] Select `cs.SE` primary with `cs.CL` and `cs.AI` cross-lists, or record
      the owner's approved alternative.
- [ ] Confirm the licence choice, understanding it is irrevocable.
- [ ] Upload `main.tex` and nothing else.
- [ ] Run Check Files; confirm `main.tex` is detected as top-level.
- [ ] Review the generated PDF end to end: title, abstract, author block,
      both TikZ figures, all four numbered tables (rights, per-family audit,
      power, 35-row register), the two uncaptioned appendix longtables, and
      the bibliography.
- [ ] Confirm the artifact URL resolves and that BOTH tags are present on the
      public remote: `gate10-paper-v1-20260911` (measurement evidence freeze,
      cited throughout the traceability appendix) and
      `gate22-paper-v32-20260916` (this manuscript's artifact tag). Both are
      created and pushed.
- [ ] Optional sanity check before submitting, and the one that caught the
      version 3 defect: clone the public repository into an empty directory,
      check out `gate22-paper-v32-20260916`, and run `python
      scripts/reproduce.py`. Expect exit 0, stage 2 reported as `PASS
      (PARTIAL)` with 47/134 entries present, and stages 3 and 4 bit-identical.
      Anything else contradicts section 8.
- [ ] Complete endorsement if arXiv requests it.
- [ ] Submit only after separate owner approval.

## Open items carried from the audit

These are stated in the manuscript itself and are listed here so they are not
forgotten at submission time:

1. One reference (`assidiqi2026referencefree`) has unverified content and is
   cited at title level only. If the full text becomes available before
   submission, §2.3 and Table 1 can be strengthened.

2. The six benchmark-validity references added in version 3, and the three
   added in version 3.3, were verified at abstract level, not full text. This
   is recorded in Appendix E of the manuscript and in
   `REFERENCES_VERIFIED.json`; it is a weaker standard than some version 2
   references received and is disclosed rather than smoothed over.
   `suh2026agentsuite` is weaker still — a conference programme entry, no
   retrievable arXiv record, camera copy unread. The single version 3.4
   addition (`li2026genebench`) is the exception: DOI resolved, bioRxiv API
   record read, and the publisher-hosted PDF retrieved and its design-constraint
   table read directly.

2a. Version 3.3 withdrew pre-execution auditing as the paper's distinction,
   after an external review pointed at `luo2026identifiability` (structural
   identifiability auditing before inference) and at task-definition auditing
   in `wang2026autoaudit` and `wang2026benchjack`. The surviving claim is the
   item-level derivability question stated in §2.1. If a reviewer pushes on
   novelty, that narrower statement — not "first pre-execution audit" — is the
   one to defend.

2b. Version 3.4 withdrew the last general form of the novelty claim, after a
   pre-submission review pointed at GeneBench, whose design constraints require
   that a graded target be recoverable from agent-visible data. Recoverability
   as a principle is therefore not this paper's to claim. What is defensible is
   the operationalisation: item-level, deterministic, under a declared
   information-rights object and finite derivation grammar, with every typed
   outcome committed as an artifact. If a reviewer pushes on novelty, defend
   that and nothing wider.

3. The external 20-pair sample supports representability, not specificity
   (§5.3). The strengthening it needs is a subset decidable without
   `declared_external_derivation`. That subset does not exist yet and the
   manuscript does not promise its result.
4. The auditor has not been independently reproduced. This is disclosed in
   §7.3.
5. The AI-use disclosure appendix should be checked against any
   venue-specific policy if the paper is later submitted to a journal.

Submission guidance: <https://info.arxiv.org/help/submit/index.html>
Category taxonomy: <https://arxiv.org/category_taxonomy>
