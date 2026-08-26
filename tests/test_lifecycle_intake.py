from __future__ import annotations

import pytest

from rag.lifecycle.errors import LifecycleError
from rag.lifecycle.intake import IntakeReceiver
from rag.lifecycle.naming import normalize_filename, validate_content_type, validate_format


HTML_BYTES = b"<html><body><h1>Title</h1><p>Body text.</p></body></html>"
PDF_BYTES = b"%PDF-1.4\n%mock pdf content for tests\n"
DOCX_BYTES = b"PK\x03\x04" + b"\x00" * 32


def _receive(filename: str, content_type: str, content: bytes, max_bytes: int = 1_000_000):
    receiver = IntakeReceiver(filename=filename, content_type=content_type, max_bytes=max_bytes)
    receiver.feed(content)
    return receiver.finalize()


# --- filename normalization: traversal / separators / empty / reserved / malformed extension ---


@pytest.mark.parametrize(
    "raw_filename",
    [
        "../secret.html",
        "..\\secret.html",
        "a/b.html",
        "a\\b.html",
        "..",
        ".",
        "",
        "   ",
        "C:\\Windows\\win.html",
        "report.html\x00.pdf",
    ],
)
def test_normalize_filename_rejects_traversal_and_separators(raw_filename):
    with pytest.raises(LifecycleError):
        normalize_filename(raw_filename)


@pytest.mark.parametrize("raw_filename", [None, ""])
def test_normalize_filename_rejects_empty(raw_filename):
    with pytest.raises(LifecycleError) as excinfo:
        normalize_filename(raw_filename)
    assert excinfo.value.code == "empty_filename"


@pytest.mark.parametrize("raw_filename", ["CON.html", "con.pdf", "LPT1.txt", "com1.md"])
def test_normalize_filename_rejects_reserved_windows_names(raw_filename):
    with pytest.raises(LifecycleError) as excinfo:
        normalize_filename(raw_filename)
    assert excinfo.value.code == "reserved_name"


@pytest.mark.parametrize("raw_filename", ["noext", "trailing.", "archive.tar.gz", "report.exe"])
def test_normalize_filename_rejects_malformed_or_unsupported_extension(raw_filename):
    with pytest.raises(LifecycleError):
        normalize_filename(raw_filename)


def test_normalize_filename_accepts_safe_name():
    slug, extension = normalize_filename("Admission Handbook 2026.html")
    assert extension == ".html"
    assert slug == "admission-handbook-2026"


# --- MIME allowlist ---


def test_validate_content_type_rejects_mismatched_mime():
    with pytest.raises(LifecycleError) as excinfo:
        validate_content_type("application/octet-stream", ".html")
    assert excinfo.value.code == "unsupported_content_type"


def test_validate_content_type_accepts_matching_mime():
    validate_content_type("text/html; charset=utf-8", ".html")


# --- deterministic format check ---


def test_validate_format_rejects_fake_pdf():
    with pytest.raises(LifecycleError) as excinfo:
        validate_format(".pdf", b"not really a pdf")
    assert excinfo.value.code == "format_validation_failed"


def test_validate_format_rejects_non_utf8_text():
    with pytest.raises(LifecycleError):
        validate_format(".txt", b"\xff\xfe not utf-8")


def test_validate_format_accepts_real_magic_bytes():
    validate_format(".pdf", PDF_BYTES)
    validate_format(".docx", DOCX_BYTES)
    validate_format(".html", HTML_BYTES)


# --- oversized input / bounded storage ---


def test_intake_rejects_oversized_upload_without_buffering_everything():
    receiver = IntakeReceiver(filename="big.txt", content_type="text/plain", max_bytes=10)
    with pytest.raises(LifecycleError) as excinfo:
        receiver.feed(b"x" * 11)
    assert excinfo.value.code == "file_too_large"


def test_intake_rejects_upload_exceeding_bound_across_multiple_chunks():
    receiver = IntakeReceiver(filename="big.txt", content_type="text/plain", max_bytes=10)
    receiver.feed(b"x" * 6)
    with pytest.raises(LifecycleError) as excinfo:
        receiver.feed(b"x" * 6)
    assert excinfo.value.code == "file_too_large"


def test_intake_accepts_upload_exactly_at_bound():
    receiver = IntakeReceiver(filename="exact.txt", content_type="text/plain", max_bytes=10)
    receiver.feed(b"x" * 10)
    result = receiver.finalize()
    assert result.size_bytes == 10


def test_intake_rejects_empty_upload():
    receiver = IntakeReceiver(filename="empty.txt", content_type="text/plain", max_bytes=10)
    with pytest.raises(LifecycleError) as excinfo:
        receiver.finalize()
    assert excinfo.value.code == "empty_upload"


# --- checksum behavior / duplicate idempotence at the checksum layer ---


def test_intake_checksum_is_sha256_hex_and_deterministic():
    result_a = _receive("doc.txt", "text/plain", b"identical content")
    result_b = _receive("doc.txt", "text/plain", b"identical content")
    assert result_a.checksum == result_b.checksum
    assert len(result_a.checksum) == 64
    import hashlib

    assert result_a.checksum == hashlib.sha256(b"identical content").hexdigest()


def test_intake_checksum_differs_for_different_content():
    result_a = _receive("doc.txt", "text/plain", b"version one")
    result_b = _receive("doc.txt", "text/plain", b"version two")
    assert result_a.checksum != result_b.checksum
