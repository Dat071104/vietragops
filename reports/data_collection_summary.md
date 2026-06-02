# Data Collection Summary

## Overview

- Phase 1 collected 37 public Vietnamese academic and policy documents into `data/raw/`.
- Sources were limited to public official TDTU domains and one official faculty domain: `undergrad.tdtu.edu.vn`, `www.tdtu.edu.vn`, `it.tdtu.edu.vn`, and `admission.tdtu.edu.vn`.
- The manifest at `data/manifests/documents_manifest.csv` includes source URLs, local file paths, SHA256 checksums, authority labels, and status labels for every collected document.

## Source list

- `undergrad.tdtu.edu.vn`: undergraduate academics hub, academic guidance, timetable guidance, course registration guidance, graduation conditions, support pages, and undergraduate regulations.
- `www.tdtu.edu.vn`: main university undergraduate overview, academic guidance, training regulations, and major catalog pages.
- `it.tdtu.edu.vn`: Computer Science program overview, curriculum pages, and expected learning outcomes pages published by the Faculty of Information Technology.
- `admission.tdtu.edu.vn`: public admission/student handbook PDFs for 2022 and 2025.

## Document count by domain

- `student_guide`: 9
- `curriculum`: 9
- `training_regulation`: 5
- `academic_schedule`: 3
- `academic_policy`: 2
- `admission`: 2
- `course_registration`: 2
- `regulation`: 2
- `student_account`: 1
- `email_usage`: 1
- `graduation_requirement`: 1

## Document count by authority

- `official`: 31
- `faculty`: 6

## Status summary

- `active`: 30
- `outdated`: 7
- `duplicate`: 0
- `manual_review`: 0

## Duplicates found

- No duplicate checksum groups were found across the 37 downloaded files.

## Manual review list

- No documents were labeled `manual_review` in the manifest.
- `published_at` remains blank for 28 rows because the public pages do not expose a reliable publication timestamp in page metadata; obvious dates were inferred only when a page or URL made them explicit.

## Rejected sources and reasons

- `stdportal.tdtu.edu.vn` and other student-system pages were excluded because they are login-gated or operate on personal student data.
- English mirror pages on TDTU subdomains were excluded from the primary corpus because Phase 1 targets Vietnamese academic/policy documents.
- IT faculty recruitment/training announcements were excluded because they are not core academic policy or curriculum sources.
- Generic university news and marketing pages were excluded when they did not contain stable academic-policy or curriculum content.

## Next risks for Phase 2

- Many HTML pages include navigation and promotional boilerplate that will need safe removal during parsing.
- The corpus mixes current and outdated regulations, so Phase 2 metadata preservation is important for later source-priority logic.
- PDF files will need page-aware extraction and table handling to avoid losing regulation structure.
- Some guidance pages discuss actions performed inside protected student systems; later generation logic must distinguish public guidance from private-data requests.
