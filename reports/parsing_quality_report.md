# Parsing Quality Report

## Overview

- Processed documents: 37
- Parse success: 37 / 37
- Success rate: 100%
- Total sections generated: 481
- Average sections per document: 13
- PDF documents with page references preserved: 5 / 5

## Format coverage

- HTML: 32 documents
- PDF: 5 documents
- DOCX: 0 documents in current corpus
- TXT/Markdown: 0 documents in current corpus

## Parse failures

- No parse failures remained after the Phase 2 self-fix loop.

## Table handling notes

- HTML tables are converted to markdown when their structure is simple enough to preserve row/column meaning.
- Complex nested HTML tables fall back to line-oriented text instead of unreadable giant markdown grids.
- PDF extraction preserves table text only as sequential text; all 5 PDF documents carry the warning `pdf_table_extraction_limited`.

## Documents needing manual review

- `it_cs_curriculum_2015`: curriculum table content is preserved as readable line-oriented text, but row/column structure should be spot-checked manually.
- `it_cs_curriculum_2018`: same table-heavy structure as above; useful content is preserved, but formatting is not fully table-native.
- `admission_handbook_2025`: parsed successfully with page references, but long handbook sections should be spot-checked for heading boundaries.
- `ug_training_reg_k2020_pdf`: regulation PDF parsed well, but legal clause boundaries should be manually spot-checked.
- `ug_training_reg_k2021_pdf`: regulation PDF parsed well, but legal clause boundaries should be manually spot-checked.

## Examples of good parsed output

- `ug_course_registration_guide`
  - Preserves procedural headings and operational guidance for course registration.
- `ug_training_reg_k2021_pdf`
  - Preserves page references and legal headings such as `Điều 1. Phạm vi và đối tượng áp dụng`.
- `admission_handbook_2025`
  - Preserves multi-page handbook sections with page numbers and long-form guidance text.

## Examples of problematic but usable output

- `tdtu_major_catalog`
  - Catalog-style page parses into fallback text sections because it is mostly headings and links.
- `it_cs_curriculum_2018`
  - Table-heavy curriculum content is readable, but not represented as a fully faithful markdown table.

## Notes for Phase 3

- Chunking should treat legal markers such as `Chương`, `Điều`, and numbered clauses as strong split boundaries.
- Table-heavy curriculum pages may benefit from conservative chunk sizes so course rows stay grouped.
- PDF handbook sections can produce many short sections, so Phase 3 should balance section fidelity with chunk compactness.
