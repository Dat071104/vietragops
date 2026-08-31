from __future__ import annotations

import socket

from rag.ingestion.firecrawl import FirecrawlScrapeResult
from rag.lifecycle.gcs_registry import GcsLifecycleRegistry
from rag.lifecycle.gcs_storage import MemoryObjectStore
from rag.lifecycle.gcs_web_import import GcsWebImportService


class StubFirecrawl:
    def __init__(self, markdown: str = "# Official\n\nAllowlisted policy content.") -> None:
        self.markdown = markdown
        self.calls: list[str] = []

    def scrape_markdown(self, url: str) -> FirecrawlScrapeResult:
        self.calls.append(url)
        return FirecrawlScrapeResult(status="ok", markdown=self.markdown, action_id="test-action")

    def search_preview(self, query: str, *, limit: int):
        raise AssertionError("search is not used by this test")


def _service(adapter: StubFirecrawl):
    objects = MemoryObjectStore()
    registry = GcsLifecycleRegistry(objects)
    service = GcsWebImportService(
        registry=registry,
        objects=objects,
        adapter=adapter,
        allowed_domains_csv="undergrad.tdtu.edu.vn",
        denied_domains_csv="",
        max_search_results=5,
        dns_resolver=lambda *args: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )
    return service, registry, objects


def test_cloud_web_import_stays_candidate_and_records_provenance():
    adapter = StubFirecrawl()
    service, registry, objects = _service(adapter)

    outcome = service.import_url("https://undergrad.tdtu.edu.vn/policy", title="Official policy")

    assert outcome.status == "ok"
    assert outcome.parse_status == "ok"
    assert outcome.review_status == "candidate"
    assert len(adapter.calls) == 1
    version = registry.get_version(outcome.version_id)
    assert version is not None
    assert version.review_status == "candidate"
    assert version.original_path.startswith("gs://test-bucket/sources/original/")
    assert registry.get_web_provenance(outcome.version_id)["firecrawl_action_id"] == "test-action"
    assert any(name.startswith(f"candidates/{outcome.version_id}/") for name in objects._objects)
    assert registry.get_active_release_id() is None


def test_cloud_web_import_is_idempotent_for_unchanged_content():
    adapter = StubFirecrawl()
    service, registry, _objects = _service(adapter)
    first = service.import_url("https://undergrad.tdtu.edu.vn/policy")
    second = service.import_url("https://undergrad.tdtu.edu.vn/policy")

    assert first.status == "ok"
    assert second.status == "no_change"
    assert second.version_id == first.version_id
    assert len(registry.list_versions(first.document_id)) == 1
    assert len(adapter.calls) == 2


def test_cloud_web_import_rejects_non_allowlisted_domain_before_scrape():
    adapter = StubFirecrawl()
    service, _registry, _objects = _service(adapter)

    outcome = service.import_url("https://evil.example/policy")

    assert outcome.status == "blocked_target"
    assert outcome.error_code == "domain_not_allowlisted"
    assert adapter.calls == []
