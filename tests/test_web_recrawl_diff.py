from __future__ import annotations

import csv
import json
from pathlib import Path

import httpx
import pytest

from rag.ingestion.firecrawl import FirecrawlAdapter
from rag.lifecycle.registry import LifecycleRegistry
from rag.lifecycle.service import LifecycleService
from rag.lifecycle.web_import import WebImportService, document_id_for_url


ALLOWED_DOMAIN = "example.gov.vn"
ALLOWED_URL = f"https://{ALLOWED_DOMAIN}/policy-a"
UPPERCASE_URL = f"HTTPS://{ALLOWED_DOMAIN}/policy-a"  # same page, different case


def _public_resolver(*addresses: str):
    def _resolver(host, port, family=None, socktype=None):
        return [(2, 1, 6, "", (addr, port)) for addr in addresses]

    return _resolver


def _service(tmp_path, handler):
    registry = LifecycleRegistry(tmp_path / "registry.db")
    adapter = FirecrawlAdapter(
        transport=httpx.MockTransport(handler),
        api_key_reader=lambda: "test-key-not-real",
        sleep_fn=lambda _s: None,
    )
    service = WebImportService(
        registry=registry,
        adapter=adapter,
        originals_dir=tmp_path / "originals",
        candidates_dir=tmp_path / "candidates",
        allowed_domains_csv=ALLOWED_DOMAIN,
        denied_domains_csv="",
        max_search_results=5,
        dns_resolver=_public_resolver("93.184.216.34"),
    )
    return service, registry


def _markdown_handler(markdown_by_call: list[str]):
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        index = min(calls["count"], len(markdown_by_call) - 1)
        calls["count"] += 1
        return httpx.Response(200, json={"data": {"markdown": markdown_by_call[index]}, "id": f"job-{index}"})

    return handler


# -- canonicalization before lookup ------------------------------------------


def test_url_is_canonicalized_before_lookup(tmp_path):
    markdown = "# Policy A\n\nBody text."
    service, registry = _service(tmp_path, _markdown_handler([markdown, markdown]))

    first = service.import_url(ALLOWED_URL)
    second = service.import_url(UPPERCASE_URL)

    assert first.document_id == second.document_id
    assert second.status == "no_change"
    assert second.version_id == first.version_id


# -- unchanged recrawl is idempotent -----------------------------------------


def test_unchanged_recrawl_is_idempotent_no_change_event(tmp_path):
    markdown = "# Policy A\n\nUnchanged body text."
    service, registry = _service(tmp_path, _markdown_handler([markdown, markdown, markdown]))

    first = service.import_url(ALLOWED_URL)
    second = service.import_url(ALLOWED_URL)
    third = service.import_url(ALLOWED_URL)

    assert first.is_new_version is True
    assert second.status == "no_change"
    assert second.version_id == first.version_id
    assert third.status == "no_change"
    assert third.version_id == first.version_id

    versions = registry.list_versions(first.document_id)
    assert len(versions) == 1  # never grew

    events = registry.list_events(first.version_id)
    event_types = [e["event_type"] for e in events]
    assert event_types.count("recrawl_no_change") == 2

    attempts = registry.list_acquisition_attempts(document_id=first.document_id)
    no_change_attempts = [a for a in attempts if a["action"] == "recrawl_no_change"]
    assert len(no_change_attempts) == 2


# -- changed recrawl creates a new linked version + diff ---------------------


def test_changed_recrawl_creates_new_version_with_prior_link_and_diff(tmp_path):
    original = "# Policy A\n\n## Section One\n\nOriginal content here.\n\n## Section Two\n\nStays the same."
    updated = "# Policy A\n\n## Section One\n\nUPDATED content here.\n\n## Section Two\n\nStays the same.\n\n## Section Three\n\nNew section."
    service, registry = _service(tmp_path, _markdown_handler([original, updated]))

    first = service.import_url(ALLOWED_URL)
    second = service.import_url(ALLOWED_URL)

    assert second.status == "ok"
    assert second.is_new_version is True
    assert second.version_id != first.version_id
    assert second.prior_version_id == first.version_id

    versions = registry.list_versions(first.document_id)
    assert len(versions) == 2

    provenance = registry.get_web_provenance(second.version_id)
    assert provenance["prior_version_id"] == first.version_id
    assert provenance["diff_path"] is not None

    diff_record = json.loads(Path(provenance["diff_path"]).read_text(encoding="utf-8"))
    assert diff_record["schema"] == "vietragops.web_candidate_diff"
    assert diff_record["changed_count"] >= 1  # Section One changed
    assert diff_record["added_count"] >= 1  # Section Three added
    assert diff_record["removed_count"] == 0
    assert "Section Three" in " ".join(diff_record["added_sections"])


# -- existing published version is untouched by a recrawl -------------------


def test_recrawl_never_changes_an_already_published_version(tmp_path):
    original = "# Policy A\n\nOriginal published content."
    updated = "# Policy A\n\nCompletely different updated content."
    service, registry = _service(tmp_path, _markdown_handler([original, updated]))

    first = service.import_url(ALLOWED_URL)
    live_manifest = tmp_path / "live" / "manifest.csv"
    live_chunks = tmp_path / "live" / "chunks.jsonl"
    lifecycle_service = LifecycleService(
        registry=registry,
        originals_dir=tmp_path / "originals",
        candidates_dir=tmp_path / "candidates",
        live_manifest_path=live_manifest,
        live_chunks_path=live_chunks,
        max_upload_bytes=25 * 1024 * 1024,
    )
    lifecycle_service.review(first.version_id)
    lifecycle_service.publish(first.version_id)

    with live_manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        rows_before = list(csv.DictReader(handle))
    chunks_before = live_chunks.read_text(encoding="utf-8")

    second = service.import_url(ALLOWED_URL)
    assert second.status == "ok"
    assert second.is_new_version is True
    # the new version must remain an unreviewed candidate
    assert second.review_status == "candidate"

    with live_manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        rows_after = list(csv.DictReader(handle))
    chunks_after = live_chunks.read_text(encoding="utf-8")

    assert rows_before == rows_after
    assert chunks_before == chunks_after

    published_version = registry.get_published_version(first.document_id)
    assert published_version.version_id == first.version_id  # unchanged


# -- a new recrawl candidate must be reviewed before publish -----------------


def test_new_recrawl_candidate_requires_review_before_publish(tmp_path):
    original = "# Policy A\n\nOriginal."
    updated = "# Policy A\n\nUpdated."
    service, registry = _service(tmp_path, _markdown_handler([original, updated]))

    first = service.import_url(ALLOWED_URL)
    second = service.import_url(ALLOWED_URL)

    lifecycle_service = LifecycleService(
        registry=registry,
        originals_dir=tmp_path / "originals",
        candidates_dir=tmp_path / "candidates",
        live_manifest_path=tmp_path / "live" / "manifest.csv",
        live_chunks_path=tmp_path / "live" / "chunks.jsonl",
        max_upload_bytes=25 * 1024 * 1024,
    )
    with pytest.raises(Exception):
        lifecycle_service.publish(second.version_id)  # not reviewed yet

    reviewed = lifecycle_service.review(second.version_id)
    assert reviewed.review_status == "reviewed"
    published = lifecycle_service.publish(second.version_id)
    assert published.review_status == "published"


# -- failed recrawl (adapter error) never disturbs existing versions --------


def test_failed_recrawl_does_not_create_or_alter_any_version(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"markdown": "# Policy A\n\nOriginal content."}})

    service, registry = _service(tmp_path, handler)
    first = service.import_url(ALLOWED_URL)

    def failing_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "internal"})

    service._adapter = FirecrawlAdapter(
        transport=httpx.MockTransport(failing_handler),
        api_key_reader=lambda: "test-key-not-real",
        sleep_fn=lambda _s: None,
        max_retries=0,
    )

    second = service.import_url(ALLOWED_URL)
    assert second.status == "upstream_error"
    assert second.version_id is None

    versions = registry.list_versions(first.document_id)
    assert len(versions) == 1
    assert versions[0].version_id == first.version_id
