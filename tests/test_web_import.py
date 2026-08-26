from __future__ import annotations

import csv
import json

import httpx
import pytest

from rag.ingestion.firecrawl import FirecrawlAdapter
from rag.lifecycle.registry import LifecycleRegistry
from rag.lifecycle.service import LifecycleService
from rag.lifecycle.web_import import WebImportService, document_id_for_url


ALLOWED_DOMAIN = "example.gov.vn"
ALLOWED_URL = f"https://{ALLOWED_DOMAIN}/policy-a"


def _public_resolver(*addresses: str):
    def _resolver(host, port, family=None, socktype=None):
        return [(2, 1, 6, "", (addr, port)) for addr in addresses]

    return _resolver


def _service(tmp_path, handler, *, allowed=ALLOWED_DOMAIN, denied="", resolver=None):
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
        allowed_domains_csv=allowed,
        denied_domains_csv=denied,
        max_search_results=5,
        dns_resolver=resolver or _public_resolver("93.184.216.34"),
    )
    return service, registry


def _ok_scrape_handler(markdown: str = "# Policy A\n\nBody paragraph text.", action_id: str = "job-1"):
    def handler(request: httpx.Request) -> httpx.Response:
        if "/search" in str(request.url):
            return httpx.Response(200, json={"data": {"web": []}})
        return httpx.Response(200, json={"data": {"markdown": markdown}, "id": action_id})

    return handler


# -- search never imports/scrapes -------------------------------------------


def test_search_preview_returns_descriptors_and_never_creates_a_document(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/search" in str(request.url)
        return httpx.Response(
            200,
            json={"data": {"web": [{"title": "Policy A", "url": ALLOWED_URL, "description": "desc"}]}},
        )

    service, registry = _service(tmp_path, handler)
    outcome = service.search_preview("education policy")

    assert outcome.status == "ok"
    assert len(outcome.descriptors) == 1
    document_id, _ = document_id_for_url(ALLOWED_URL)
    assert registry.get_document(document_id) is None


# -- allowed URL becomes a candidate; live corpus untouched ------------------


def test_allowed_url_becomes_candidate_without_touching_live_corpus(tmp_path):
    live_manifest = tmp_path / "live" / "manifest.csv"
    live_chunks = tmp_path / "live" / "chunks.jsonl"
    live_manifest.parent.mkdir(parents=True)
    live_manifest.write_text(
        "doc_id,title,source_url,source_type,domain,authority_level,language,published_at,crawled_at,"
        "file_path,checksum,status,notes\n",
        encoding="utf-8",
    )
    live_chunks.write_text("", encoding="utf-8")
    before_manifest = live_manifest.read_bytes()
    before_chunks = live_chunks.read_bytes()

    service, registry = _service(tmp_path, _ok_scrape_handler())
    outcome = service.import_url(ALLOWED_URL)

    assert outcome.status == "ok"
    assert outcome.is_new_version is True
    document_id, _ = document_id_for_url(ALLOWED_URL)
    assert outcome.document_id == document_id
    version = registry.get_version(outcome.version_id)
    assert version.parse_status == "ok"
    assert version.review_status == "candidate"

    document = registry.get_document(document_id)
    assert document.authority_level == "unknown"
    assert document.source_url == ALLOWED_URL

    assert live_manifest.read_bytes() == before_manifest
    assert live_chunks.read_bytes() == before_chunks


# -- blocked/private URL never reaches the adapter ---------------------------


def test_disallowed_domain_never_reaches_adapter(tmp_path):
    called = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["count"] += 1
        return httpx.Response(200, json={"data": {"markdown": "should never be requested"}})

    service, registry = _service(tmp_path, handler, allowed="other.gov.vn")
    outcome = service.import_url(ALLOWED_URL)

    assert outcome.status == "blocked_target"
    assert outcome.error_code == "domain_not_allowlisted"
    assert called["count"] == 0
    attempts = registry.list_acquisition_attempts(canonical_url=ALLOWED_URL)
    assert len(attempts) == 1
    assert attempts[0]["status_class"] == "blocked_target"


def test_private_ip_target_never_reaches_adapter(tmp_path):
    called = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["count"] += 1
        return httpx.Response(200, json={"data": {"markdown": "should never be requested"}})

    service, registry = _service(
        tmp_path, handler, resolver=_public_resolver("10.0.0.5")
    )
    outcome = service.import_url(ALLOWED_URL)

    assert outcome.status == "blocked_target"
    assert outcome.error_code == "private_network_target"
    assert called["count"] == 0


def test_localhost_url_is_rejected_before_domain_policy(tmp_path):
    called = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["count"] += 1
        return httpx.Response(200, json={"data": {"markdown": "x"}})

    service, _ = _service(tmp_path, handler, allowed="localhost")
    outcome = service.import_url("https://localhost/admin")

    assert outcome.status == "blocked_target"
    assert outcome.error_code == "blocked_hostname"
    assert called["count"] == 0


# -- failed/empty markdown is never reviewable/publishable -------------------


def test_empty_markdown_result_is_not_reviewable(tmp_path):
    # Passes the adapter's non-blank check (it has a '#' character) but
    # normalizes/section-builds down to nothing usable.
    service, registry = _service(tmp_path, _ok_scrape_handler(markdown="# \n"))
    outcome = service.import_url(ALLOWED_URL)

    assert outcome.status == "ok"  # scrape succeeded at the HTTP level
    assert outcome.parse_status == "failed"

    lifecycle_service = LifecycleService(
        registry=registry,
        originals_dir=tmp_path / "originals",
        candidates_dir=tmp_path / "candidates",
        live_manifest_path=tmp_path / "live" / "manifest.csv",
        live_chunks_path=tmp_path / "live" / "chunks.jsonl",
        max_upload_bytes=25 * 1024 * 1024,
    )
    with pytest.raises(Exception):
        lifecycle_service.review(outcome.version_id)


def test_firecrawl_failure_status_never_creates_a_version(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(402, json={"error": "insufficient credits"})

    service, registry = _service(tmp_path, handler)
    outcome = service.import_url(ALLOWED_URL)

    assert outcome.status == "credit_exhausted"
    assert outcome.version_id is None
    document_id, _ = document_id_for_url(ALLOWED_URL)
    document = registry.get_document(document_id)
    assert document is None or registry.list_versions(document_id) == []


# -- provenance / checksum / timestamp persisted ------------------------------


def test_provenance_records_checksum_timestamp_and_action_id(tmp_path):
    service, registry = _service(tmp_path, _ok_scrape_handler(action_id="job-42"))
    outcome = service.import_url(ALLOWED_URL)

    provenance = registry.get_web_provenance(outcome.version_id)
    assert provenance is not None
    assert provenance["canonical_url"] == ALLOWED_URL
    assert provenance["firecrawl_action_id"] == "job-42"
    assert provenance["domain"] == ALLOWED_DOMAIN
    assert provenance["status_class"] == "ok"
    assert len(provenance["content_checksum"]) == 64  # sha256 hex
    assert provenance["retrieved_at"]  # non-empty ISO timestamp
    assert provenance["prior_version_id"] is None


# -- distinct 429 / credit-exhaustion outcomes -------------------------------


def test_rate_limited_and_credit_exhausted_are_recorded_distinctly(tmp_path):
    def rate_limited_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "3"}, json={"error": "rate_limited"})

    service, registry = _service(tmp_path, rate_limited_handler)
    outcome = service.import_url(ALLOWED_URL)
    assert outcome.status == "rate_limited"
    attempts = registry.list_acquisition_attempts(canonical_url=ALLOWED_URL)
    assert attempts[-1]["status_class"] == "rate_limited"
    assert attempts[-1]["retry_after_seconds"] == 3.0

    def credit_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(402, json={"error": "insufficient credits"})

    service2, registry2 = _service(tmp_path / "second", credit_handler)
    outcome2 = service2.import_url(ALLOWED_URL)
    assert outcome2.status == "credit_exhausted"
    attempts2 = registry2.list_acquisition_attempts(canonical_url=ALLOWED_URL)
    assert attempts2[-1]["status_class"] == "credit_exhausted"
    assert attempts2[-1]["status_class"] != attempts[-1]["status_class"]


# -- authority is never auto-marked official ---------------------------------


def test_import_url_signature_never_accepts_authority_level(tmp_path):
    import inspect

    signature = inspect.signature(WebImportService.import_url)
    assert "authority_level" not in signature.parameters
    assert "publisher" not in signature.parameters


def test_document_authority_level_is_always_unknown(tmp_path):
    service, registry = _service(tmp_path, _ok_scrape_handler())
    outcome = service.import_url(ALLOWED_URL)
    document = registry.get_document(outcome.document_id)
    assert document.authority_level == "unknown"


# -- true integration: a successful web candidate reuses the existing
#    LifecycleService review -> publish -> live-manifest flow unchanged ------


def test_successful_web_candidate_can_be_reviewed_and_published_via_existing_lifecycle_service(tmp_path):
    service, registry = _service(tmp_path, _ok_scrape_handler(markdown="# Policy A\n\nSome real body text here."))
    outcome = service.import_url(ALLOWED_URL, title="Policy A")
    assert outcome.status == "ok"
    assert outcome.parse_status == "ok"

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

    reviewed = lifecycle_service.review(outcome.version_id)
    assert reviewed.review_status == "reviewed"
    published = lifecycle_service.publish(outcome.version_id)
    assert published.review_status == "published"

    with live_manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert any(row["doc_id"] == outcome.document_id and row["authority_level"] == "unknown" for row in rows)
    chunk_lines = [json.loads(line) for line in live_chunks.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(chunk["doc_id"] == outcome.document_id for chunk in chunk_lines)


# -- CLI output never includes raw markdown ----------------------------------


def test_cli_import_output_never_includes_raw_markdown(tmp_path, monkeypatch, capsys):
    from scripts import web_import as cli

    secret_markdown = "# Secret Heading\n\nThis exact sentence must never be printed."
    service, _ = _service(tmp_path, _ok_scrape_handler(markdown=secret_markdown))
    monkeypatch.setattr(cli, "get_web_import_service", lambda: service)

    exit_code = cli.main(["import", "--url", ALLOWED_URL])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Secret Heading" not in captured.out
    assert "This exact sentence" not in captured.out
    assert "status=ok" in captured.out
    assert "version_id=" in captured.out


def test_cli_search_output_never_includes_scraped_content(tmp_path, monkeypatch, capsys):
    from scripts import web_import as cli

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"data": {"web": [{"title": "T", "url": ALLOWED_URL, "description": "D"}]}}
        )

    service, _ = _service(tmp_path, handler)
    monkeypatch.setattr(cli, "get_web_import_service", lambda: service)

    exit_code = cli.main(["search", "--query", "policy"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert ALLOWED_URL in captured.out
    assert "result(s)" in captured.out
