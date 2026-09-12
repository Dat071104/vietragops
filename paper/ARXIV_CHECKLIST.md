# arXiv preparation checklist — manuscript version 2

Prepared 2026-09-12. **This package does not submit anything.** Submission is
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
| Comments field | `Measurement and benchmark-validity case study. Artifact tag: gate10-paper-v1-20260911.` |
| Artifact URL | `https://github.com/Dat071104/vietragops` |
| Licence | **`CC BY 4.0`** — decided. Rationale and the one caveat are below. |

**Title note.** Version 2 changes the subtitle from "Synthetic Tool-Drift
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
- [ ] Confirm the artifact URL resolves and the tag
      `gate10-paper-v1-20260911` is present on the public remote.
- [ ] Complete endorsement if arXiv requests it.
- [ ] Submit only after separate owner approval.

## Open items carried from the audit

These are stated in the manuscript itself and are listed here so they are not
forgotten at submission time:

1. One reference (`assidiqi2026referencefree`) has unverified content and is
   cited at title level only. If the full text becomes available before
   submission, §2.2 and Table 1 can be strengthened.
2. The auditor has not been independently reproduced. This is disclosed in
   §7.3.
3. The AI-use disclosure in Appendix F should be checked against any
   venue-specific policy if the paper is later submitted to a journal.

Submission guidance: <https://info.arxiv.org/help/submit/index.html>
Category taxonomy: <https://arxiv.org/category_taxonomy>
