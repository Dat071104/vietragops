"""Private, candidate-only Firecrawl import for the Gate 09R cloud API."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import socket
import tempfile
from typing import Callable
import uuid

from rag.ingestion.firecrawl import ADAPTER_VERSION, FirecrawlAdapter
from rag.lifecycle.gcs_registry import GcsLifecycleRegistry
from rag.lifecycle.gcs_storage import GcsReleaseStore, ObjectStore
from rag.lifecycle.web_import import (
    FIRECRAWL_PARSER_PROVENANCE,
    WebImportOutcome,
    WebSearchOutcome,
    document_id_for_url,
)
from rag.lifecycle.web_pipeline import WEB_PARSER_POLICY, process_web_candidate
from rag.lifecycle.web_safety import (
    DomainPolicy,
    WebSafetyError,
    bounded_search_limit,
    enforce_domain_policy,
    resolve_and_reject_private_targets,
    validate_query,
    validate_url_syntax,
)


class GcsWebImportService:
    """Wires Firecrawl into GCS-backed candidate storage only."""

    def __init__(
        self,
        *,
        registry: GcsLifecycleRegistry,
        objects: ObjectStore,
        adapter: FirecrawlAdapter,
        allowed_domains_csv: str,
        denied_domains_csv: str,
        max_search_results: int,
        dns_resolver: Callable[..., list] = socket.getaddrinfo,
    ) -> None:
        self._registry = registry
        self._objects = objects
        self._releases = GcsReleaseStore(objects)
        self._adapter = adapter
        self._policy = DomainPolicy.from_env_values(allowed_domains_csv, denied_domains_csv)
        self._max_search_results = max_search_results
        self._dns_resolver = dns_resolver

    def search_preview(self, query: str, *, limit: int | None = None) -> WebSearchOutcome:
        try:
            validated_query = validate_query(query)
        except WebSafetyError as exc:
            self._registry.record_acquisition_attempt(action="search", status_class="blocked_target", error_code=exc.code)
            return WebSearchOutcome(status="blocked_target", error_code=exc.code)
        bounded_limit = bounded_search_limit(limit, configured_max=self._max_search_results)
        result = self._adapter.search_preview(validated_query, limit=bounded_limit)
        self._registry.record_acquisition_attempt(
            action="search",
            status_class=result.status,
            error_code=result.error_code,
            http_status=result.http_status,
            credits_used=result.credits_used,
        )
        return WebSearchOutcome(status=result.status, descriptors=result.descriptors, error_code=result.error_code)

    def import_url(self, raw_url: str, *, title: str | None = None) -> WebImportOutcome:
        try:
            validated = validate_url_syntax(raw_url)
            enforce_domain_policy(validated.host, self._policy)
            resolve_and_reject_private_targets(validated.host, resolver=self._dns_resolver)
        except WebSafetyError as exc:
            self._registry.record_acquisition_attempt(
                action="scrape", canonical_url=raw_url, status_class="blocked_target", error_code=exc.code
            )
            return WebImportOutcome(status="blocked_target", error_code=exc.code)

        canonical_url = validated.canonical_url
        document_id, url_hash = document_id_for_url(canonical_url)
        scrape = self._adapter.scrape_markdown(canonical_url)
        self._registry.record_acquisition_attempt(
            action="scrape",
            canonical_url=canonical_url,
            domain=validated.host,
            status_class=scrape.status,
            error_code=scrape.error_code,
            http_status=scrape.http_status,
            retry_after_seconds=scrape.retry_after_seconds,
            credits_used=scrape.credits_used,
            document_id=document_id,
        )
        if not scrape.ok:
            return WebImportOutcome(status=scrape.status, document_id=document_id, error_code=scrape.error_code)

        display_title = title or validated.host
        self._registry.get_or_create_document(
            document_id=document_id,
            title=display_title,
            source_url=canonical_url,
            publisher=None,
            domain=validated.host,
            authority_level="unknown",
        )
        assert scrape.markdown is not None
        content_checksum = hashlib.sha256(scrape.markdown.encode("utf-8")).hexdigest()
        existing = self._registry.find_version_by_checksum(document_id, content_checksum)
        if existing is not None:
            self._registry.record_note(existing.version_id, "recrawl_no_change", f"url={canonical_url}")
            return WebImportOutcome(
                status="no_change",
                document_id=document_id,
                version_id=existing.version_id,
                parse_status=existing.parse_status,
                review_status=existing.review_status,
                is_new_version=False,
            )

        prior_versions = self._registry.list_versions(document_id)
        prior_version_id = prior_versions[-1].version_id if prior_versions else None
        version_id = uuid.uuid4().hex
        original_name = f"sources/original/{version_id}.md"
        self._objects.put_immutable(
            original_name,
            scrape.markdown.encode("utf-8"),
            content_type="text/markdown",
        )
        version = self._registry.create_version(
            version_id=version_id,
            document_id=document_id,
            checksum=content_checksum,
            extension=".md",
            original_path=self._releases.uri(original_name),
            original_filename=None,
            content_type="text/markdown",
            size_bytes=len(scrape.markdown.encode("utf-8")),
        )

        with tempfile.TemporaryDirectory(prefix="vietragops-gcs-web-") as temp_root:
            root = Path(temp_root)
            candidate = process_web_candidate(
                document_id=document_id,
                version_id=version_id,
                canonical_url=canonical_url,
                raw_markdown=scrape.markdown,
                title=display_title,
                domain=validated.host,
                parser_provenance=FIRECRAWL_PARSER_PROVENANCE,
                candidate_dir=root / "candidate",
                originals_dir=root / "originals",
                adapter_version=ADAPTER_VERSION,
            )
            extraction = json.loads(candidate.extraction_path.read_text(encoding="utf-8"))
            extraction["original_path"] = self._releases.uri(original_name)
            extraction["canonical_path"] = self._releases.uri(f"candidates/{version_id}/canonical.md")
            candidate.extraction_path.write_text(
                json.dumps(extraction, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
            )
            for name, path, content_type in (
                ("processed.jsonl", candidate.processed_path, "application/x-ndjson"),
                ("chunks_500.jsonl", candidate.chunks_path, "application/x-ndjson"),
                ("canonical.md", candidate.canonical_path, "text/markdown"),
                ("extraction.json", candidate.extraction_path, "application/json"),
            ):
                self._objects.put_immutable(
                    f"candidates/{version_id}/{name}", path.read_bytes(), content_type=content_type
                )

        version = self._registry.update_candidate_artifacts(
            version_id,
            parse_status=candidate.parse_status,
            candidate_processed_path=self._releases.uri(f"candidates/{version_id}/processed.jsonl"),
            candidate_chunks_path=self._releases.uri(f"candidates/{version_id}/chunks_500.jsonl"),
            candidate_canonical_path=self._releases.uri(f"candidates/{version_id}/canonical.md"),
            candidate_extraction_path=self._releases.uri(f"candidates/{version_id}/extraction.json"),
            parse_warnings=json.dumps(candidate.warnings) if candidate.warnings else None,
        )
        self._registry.create_web_provenance(
            version_id=version_id,
            canonical_url=canonical_url,
            url_hash=url_hash,
            retrieved_at=_now_iso(),
            firecrawl_action_id=scrape.action_id,
            http_status=scrape.http_status,
            status_class=scrape.status,
            credits_used=scrape.credits_used,
            content_checksum=content_checksum,
            domain=validated.host,
            adapter_version=ADAPTER_VERSION,
            parser_policy=WEB_PARSER_POLICY,
            prior_version_id=prior_version_id,
            diff_path=None,
        )
        return WebImportOutcome(
            status="ok",
            document_id=document_id,
            version_id=version.version_id,
            parse_status=version.parse_status,
            review_status=version.review_status,
            is_new_version=True,
            prior_version_id=prior_version_id,
        )


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
