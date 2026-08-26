from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from rag.lifecycle.errors import LifecycleError
from rag.lifecycle.extraction import count_markdown_tables, sha256_file, sha256_text
from rag.lifecycle.publish import apply_live_state, read_chunk_lines, read_manifest_rows
from rag.lifecycle.registry import LifecycleRegistry
from rag.lifecycle.service import LifecycleService
from rag.loaders.docx_loader import load_docx
from rag.preprocessing.section_detector import build_sections


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "gate02"
FIXTURE_MANIFEST = FIXTURE_ROOT / "fixture_manifest.json"


def _make_service(tmp_path: Path, *, pdf_parser: str = "markitdown") -> LifecycleService:
    return LifecycleService(
        registry=LifecycleRegistry(tmp_path / "registry.db"),
        originals_dir=tmp_path / "originals",
        candidates_dir=tmp_path / "candidates",
        live_manifest_path=tmp_path / "live" / "manifest.csv",
        live_chunks_path=tmp_path / "live" / "chunks_500.jsonl",
        max_upload_bytes=1_000_000,
        pdf_parser_policy=pdf_parser,
    )


def _upload_fixture(service: LifecycleService, fixture_name: str):
    path = FIXTURE_ROOT / fixture_name
    mime = (
        "application/pdf"
        if path.suffix == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    receiver = service.begin_intake(filename=fixture_name, content_type=mime)
    receiver.feed(path.read_bytes())
    return service.complete_intake(receiver)


def _record(service: LifecycleService, version_id: str) -> tuple[object, dict]:
    version = service.get_version_or_raise(version_id)
    record = json.loads(Path(version.candidate_extraction_path).read_text(encoding="utf-8"))
    return version, record


def test_fixture_manifest_is_local_and_checksums_match():
    manifest = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["generator_revision"] == "gate02-local-fixtures-v1"
    assert all("external_tools" not in item["path"] for item in manifest["fixtures"])

    for item in manifest["fixtures"]:
        path = FIXTURE_ROOT / item["path"]
        assert path.is_file()
        assert sha256_file(path) == item["sha256"]


def test_normal_pdf_uses_markitdown_canonical_pipeline_and_checksum_linkage(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload_fixture(service, "normal.pdf")
    version, record = _record(service, outcome.version_id)

    assert outcome.parse_status == "ok"
    assert outcome.review_status == "candidate"
    assert record["parser_name"] == "markitdown"
    assert record["parser_version"] == "0.1.7"
    assert record["parser_provenance"] == "markitdown@9dc0d6579b8739c9d0671ff205e071e3053c7df1"
    assert record["parser_policy"] == "markitdown_default"
    assert record["conversion_status"] == "ok"
    assert record["parse_status"] == "ok"
    assert record["conversion_duration_ms"] >= 0
    assert record["section_count"] > 0
    assert record["table_count"] == 0

    original = Path(version.original_path)
    canonical = Path(version.candidate_canonical_path)
    extraction = Path(version.candidate_extraction_path)
    assert original.read_bytes() == (FIXTURE_ROOT / "normal.pdf").read_bytes()
    assert record["original_sha256"] == version.checksum == sha256_file(original)
    assert record["canonical_path"] == str(canonical)
    canonical_text = canonical.read_text(encoding="utf-8")
    assert canonical.parent == extraction.parent
    assert record["canonical_sha256"] == sha256_text(canonical_text)
    assert record["character_count"] == len(canonical_text)
    assert record["table_count"] == count_markdown_tables(canonical_text)
    assert len(read_manifest_rows(tmp_path / "live" / "manifest.csv")) == 0
    assert read_chunk_lines(tmp_path / "live" / "chunks_500.jsonl") == []


def test_table_heavy_pdf_records_deterministic_table_measure(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload_fixture(service, "table_heavy.pdf")
    version, record = _record(service, outcome.version_id)

    assert outcome.parse_status == "ok"
    assert record["parser_name"] == "markitdown"
    assert record["table_count"] == 1
    assert record["table_count_rule"]
    assert record["section_count"] == len(
        json.loads(Path(version.candidate_processed_path).read_text(encoding="utf-8"))["sections"]
    )


def test_docx_markitdown_success_is_compared_with_existing_docx_loader(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload_fixture(service, "docx_policy.docx")
    version, record = _record(service, outcome.version_id)

    assert outcome.parse_status == "ok"
    assert record["parser_name"] == "markitdown"
    assert record["parser_policy"] == "markitdown_docx"
    assert record["canonical_path"]
    assert record["table_count"] == 1

    legacy = load_docx(Path(version.original_path))
    legacy_sections = build_sections(legacy["blocks"], version.document_id, "docx_policy")
    assert legacy_sections
    assert legacy["blocks"]
    assert record["character_count"] > 0


@pytest.mark.parametrize(
    ("fixture_name", "expected_warning"),
    [("malformed.pdf", "malformed_pdf"), ("scanned_no_text.pdf", "empty_markdown"), ("malformed.docx", "malformed_docx")],
)
def test_malformed_or_unusable_candidates_cannot_be_reviewed_or_published(
    tmp_path, fixture_name: str, expected_warning: str | None
):
    service = _make_service(tmp_path)
    outcome = _upload_fixture(service, fixture_name)
    version, record = _record(service, outcome.version_id)

    assert outcome.parse_status == "failed"
    assert version.review_status == "candidate"
    assert record["parse_status"] == "failed"
    assert record["conversion_status"] in {"failed", "empty"}
    assert record["warnings"]
    if expected_warning is not None:
        assert expected_warning in record["warnings"]

    with pytest.raises(LifecycleError) as review_error:
        service.review(version.version_id)
    assert review_error.value.code == "not_parsed"

    with pytest.raises(LifecycleError) as publish_error:
        service.publish(version.version_id)
    assert publish_error.value.code == "invalid_transition"
    assert read_manifest_rows(tmp_path / "live" / "manifest.csv") == []


def test_corrupt_extraction_record_is_failed_during_review(tmp_path):
    service = _make_service(tmp_path)
    outcome = _upload_fixture(service, "normal.pdf")
    version = service.get_version_or_raise(outcome.version_id)
    Path(version.candidate_extraction_path).write_text("{", encoding="utf-8")

    with pytest.raises(LifecycleError) as excinfo:
        service.review(version.version_id)

    assert excinfo.value.code == "candidate_unusable"
    failed = service.get_version_or_raise(version.version_id)
    assert failed.parse_status == "failed"
    assert "corrupt_extraction_record" in json.loads(failed.parse_warnings)
    with pytest.raises(LifecycleError):
        service.publish(version.version_id)


def test_candidate_processing_does_not_touch_live_artifacts(tmp_path):
    service = _make_service(tmp_path)
    live_manifest = tmp_path / "live" / "manifest.csv"
    live_chunks = tmp_path / "live" / "chunks_500.jsonl"
    apply_live_state(
        manifest_path=live_manifest,
        chunks_path=live_chunks,
        document_id="preexisting-live",
        manifest_row={
            "doc_id": "preexisting-live",
            "title": "Existing",
            "source_url": "https://example.test/existing",
            "source_type": "markdown",
            "domain": "test",
            "authority_level": "official",
            "language": "",
            "published_at": "",
            "crawled_at": "",
            "file_path": "existing.md",
            "checksum": "0" * 64,
            "status": "active",
            "notes": "",
        },
        chunk_records=[{"chunk_id": "preexisting-live-c001", "doc_id": "preexisting-live", "text": "existing"}],
    )
    before_manifest = live_manifest.read_bytes()
    before_chunks = live_chunks.read_bytes()

    outcome = _upload_fixture(service, "normal.pdf")

    assert outcome.parse_status == "ok"
    assert live_manifest.read_bytes() == before_manifest
    assert live_chunks.read_bytes() == before_chunks
    with live_manifest.open(encoding="utf-8", newline="") as handle:
        assert all(row["doc_id"] != outcome.document_id for row in csv.DictReader(handle))


def test_pypdf_is_an_explicit_recorded_fallback_policy(tmp_path):
    service = _make_service(tmp_path, pdf_parser="pypdf")
    outcome = _upload_fixture(service, "normal.pdf")
    version, record = _record(service, outcome.version_id)

    assert outcome.parse_status == "ok"
    assert record["parser_name"] == "pypdf"
    assert record["parser_policy"] == "pypdf_explicit_fallback"
    assert record["conversion_status"] == "legacy"
    assert "explicit_pypdf_fallback" in record["warnings"]
    assert version.candidate_canonical_path is None
    service.review(version.version_id)
    assert service.publish(version.version_id).review_status == "published"
