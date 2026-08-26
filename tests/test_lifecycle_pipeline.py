from __future__ import annotations

import json

from rag.lifecycle.pipeline import process_candidate


MARKDOWN_CONTENT = """# Quy dinh hoc vu

## Dieu 1: Pham vi ap dung

Quy dinh nay ap dung cho toan bo sinh vien chinh quy.

## Dieu 2: Dieu kien tot nghiep

Sinh vien can hoan thanh 130 tin chi de tot nghiep.
"""

HTML_CONTENT = """<html><head><title>Chinh sach thu vien</title></head>
<body><main>
<h1>Chinh sach thu vien</h1>
<p>Thu vien mo cua tu 7 gio sang den 9 gio toi.</p>
<h2>Muon sach</h2>
<p>Sinh vien duoc muon toi da 5 cuon sach mot lan.</p>
</main></body></html>"""


def _write(tmp_path, name: str, content: str):
    original = tmp_path / "originals" / name
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_text(content, encoding="utf-8")
    return original


def test_process_candidate_parses_markdown_into_sections_and_chunks(tmp_path):
    original = _write(tmp_path, "policy.md", MARKDOWN_CONTENT)
    candidate_dir = tmp_path / "candidates" / "v1"

    result = process_candidate(
        document_id="quy-dinh-hoc-vu",
        version_id="v1",
        original_path=original,
        extension=".md",
        title="Quy dinh hoc vu",
        source_url="https://example.edu/quy-dinh",
        domain="student_guide",
        authority_level="official",
        candidate_dir=candidate_dir,
    )

    assert result.parse_status == "ok"
    assert result.warnings == []
    assert len(result.processed_doc["sections"]) >= 1
    assert len(result.chunks) >= 1
    assert all(chunk["doc_id"] == "quy-dinh-hoc-vu" for chunk in result.chunks)
    assert all(chunk["domain"] == "student_guide" for chunk in result.chunks)


def test_process_candidate_writes_only_under_candidate_dir(tmp_path):
    original = _write(tmp_path, "policy.md", MARKDOWN_CONTENT)
    candidate_dir = tmp_path / "candidates" / "v1"

    result = process_candidate(
        document_id="quy-dinh-hoc-vu",
        version_id="v1",
        original_path=original,
        extension=".md",
        title="Quy dinh hoc vu",
        source_url=None,
        domain=None,
        authority_level=None,
        candidate_dir=candidate_dir,
    )

    assert result.processed_path == candidate_dir / "processed.jsonl"
    assert result.chunks_path == candidate_dir / "chunks_500.jsonl"
    assert result.canonical_path is None
    assert result.extraction_path == candidate_dir / "extraction.json"
    assert result.processed_path.exists()
    assert result.chunks_path.exists()
    assert result.extraction_path.exists()
    # Only files under candidate_dir were created by this call.
    created_files = {p for p in (tmp_path / "candidates").rglob("*") if p.is_file()}
    assert created_files == {result.processed_path, result.chunks_path, result.extraction_path}
    # Unknown provenance is represented as "unknown", never invented as something specific.
    assert result.processed_doc["sections"]
    manifest_row_domain = json.loads(result.chunks_path.read_text(encoding="utf-8").splitlines()[0])["domain"]
    assert manifest_row_domain == "unknown"


def test_process_candidate_html_extracts_headings_and_paragraphs(tmp_path):
    original = _write(tmp_path, "library.html", HTML_CONTENT)
    candidate_dir = tmp_path / "candidates" / "v2"

    result = process_candidate(
        document_id="chinh-sach-thu-vien",
        version_id="v2",
        original_path=original,
        extension=".html",
        title="library",
        source_url="https://example.edu/thu-vien",
        domain="facility",
        authority_level="official",
        candidate_dir=candidate_dir,
    )

    assert result.parse_status == "ok"
    joined_text = " ".join(chunk["text"] for chunk in result.chunks)
    assert "Thu vien mo cua" in joined_text
    assert all(chunk["source_type"] == "html" for chunk in result.chunks)


def test_process_candidate_marks_failed_when_no_sections_are_built(tmp_path):
    original = _write(tmp_path, "empty.md", "   \n\n   \n")
    candidate_dir = tmp_path / "candidates" / "v3"

    result = process_candidate(
        document_id="empty-doc",
        version_id="v3",
        original_path=original,
        extension=".md",
        title="Empty",
        source_url=None,
        domain=None,
        authority_level=None,
        candidate_dir=candidate_dir,
    )

    assert result.parse_status == "failed"
    assert "no_sections_built" in result.warnings
    assert result.chunks == []
    # Candidate artifacts are still written (inspectable), just with parse_status=failed.
    assert result.processed_path.exists()
    assert result.chunks_path.read_text(encoding="utf-8") == ""


def test_process_candidate_handles_missing_original_without_raising(tmp_path):
    missing = tmp_path / "originals" / "does-not-exist.md"
    candidate_dir = tmp_path / "candidates" / "v4"

    result = process_candidate(
        document_id="missing-doc",
        version_id="v4",
        original_path=missing,
        extension=".md",
        title="Missing",
        source_url=None,
        domain=None,
        authority_level=None,
        candidate_dir=candidate_dir,
    )

    assert result.parse_status == "failed"
    assert any(warning.startswith("parser_exception:") for warning in result.warnings)


def test_process_candidate_is_retryable_and_overwrites_candidate_dir_atomically(tmp_path):
    original = _write(tmp_path, "policy.md", "   ")
    candidate_dir = tmp_path / "candidates" / "v5"

    first = process_candidate(
        document_id="retry-doc",
        version_id="v5",
        original_path=original,
        extension=".md",
        title="Retry",
        source_url=None,
        domain=None,
        authority_level=None,
        candidate_dir=candidate_dir,
    )
    assert first.parse_status == "failed"

    # Original is corrected in place (immutable-artifact concern belongs to the
    # caller; here we only prove re-running the pipeline is safe and idempotent).
    original.write_text(MARKDOWN_CONTENT, encoding="utf-8")
    second = process_candidate(
        document_id="retry-doc",
        version_id="v5",
        original_path=original,
        extension=".md",
        title="Retry",
        source_url=None,
        domain=None,
        authority_level=None,
        candidate_dir=candidate_dir,
    )
    assert second.parse_status == "ok"
    assert len(second.chunks) >= 1
    # The candidate files reflect only the latest run.
    reloaded = json.loads(candidate_dir.joinpath("processed.jsonl").read_text(encoding="utf-8"))
    assert reloaded["parse_status"] == "ok"
