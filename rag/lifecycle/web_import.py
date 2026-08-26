"""Admin-controlled bounded web discovery/import into the candidate lifecycle.

``search query -> preview descriptors -> operator selects one URL -> scrape
-> candidate``. Nothing here ever touches the live manifest/chunks; only the
existing ``LifecycleService.publish`` does that, after an explicit human
review of the resulting candidate version. Recrawling the same URL is
idempotent when the content is unchanged and creates a new, still-candidate
version (linked to the prior one) when it has changed.
"""

from __future__ import annotations

import hashlib
import json
import socket
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from rag.ingestion.firecrawl import ADAPTER_VERSION, FirecrawlAdapter, SearchDescriptor
from rag.lifecycle.web_diff import compute_section_diff, write_diff_artifact
from rag.lifecycle.registry import LifecycleRegistry, now_iso
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


FIRECRAWL_PARSER_PROVENANCE = "firecrawl_api@v2"


def document_id_for_url(canonical_url: str) -> tuple[str, str]:
    """Stable web document identity derived only from the canonical URL.

    Never derived from title, so the same page always maps to the same
    document regardless of how its title changes over time.
    """

    url_hash = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()
    return f"web-{url_hash[:24]}", url_hash


@dataclass(frozen=True)
class WebSearchOutcome:
    status: str
    descriptors: tuple[SearchDescriptor, ...] = ()
    error_code: str | None = None


@dataclass(frozen=True)
class WebImportOutcome:
    status: str  # "ok" | "no_change" | a web-safety/firecrawl status class
    document_id: str | None = None
    version_id: str | None = None
    parse_status: str | None = None
    review_status: str | None = None
    is_new_version: bool = False
    prior_version_id: str | None = None
    error_code: str | None = None


class WebImportService:
    """Wires URL safety + the Firecrawl adapter into the existing lifecycle registry."""

    def __init__(
        self,
        *,
        registry: LifecycleRegistry,
        adapter: FirecrawlAdapter,
        originals_dir: Path,
        candidates_dir: Path,
        allowed_domains_csv: str,
        denied_domains_csv: str,
        max_search_results: int,
        dns_resolver: Callable[..., list] = socket.getaddrinfo,
    ) -> None:
        self._registry = registry
        self._adapter = adapter
        self._originals_dir = Path(originals_dir)
        self._candidates_dir = Path(candidates_dir)
        self._policy = DomainPolicy.from_env_values(allowed_domains_csv, denied_domains_csv)
        self._max_search_results = max_search_results
        self._dns_resolver = dns_resolver

    # -- search -----------------------------------------------------------

    def search_preview(self, query: str, *, limit: int | None = None) -> WebSearchOutcome:
        """Return descriptors only. Never imports or scrapes any result."""

        try:
            validated_query = validate_query(query)
        except WebSafetyError as exc:
            self._registry.record_acquisition_attempt(
                action="search", status_class="blocked_target", error_code=exc.code
            )
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

    # -- import / recrawl ---------------------------------------------------

    def import_url(self, raw_url: str, *, title: str | None = None) -> WebImportOutcome:
        """Validate -> scrape -> build/attach a candidate version.

        Calling this again on the same URL is how a recrawl happens: unchanged
        content is idempotent (no new version); changed content creates a new
        candidate version linked to the prior one. Either way the result stays
        a candidate; nothing here reviews or publishes it.
        """

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
        # authority_level is always "unknown" here and is never accepted from
        # a caller/operator argument -- only a future reviewed server-owned
        # policy may raise it.
        self._registry.get_or_create_document(
            document_id=document_id,
            title=display_title,
            source_url=canonical_url,
            publisher=None,
            domain=validated.host,
            authority_level="unknown",
        )

        content_checksum = hashlib.sha256(scrape.markdown.encode("utf-8")).hexdigest()
        existing = self._registry.find_version_by_checksum(document_id, content_checksum)
        if existing is not None:
            self._registry.record_note(existing.version_id, "recrawl_no_change", f"url={canonical_url}")
            self._registry.record_acquisition_attempt(
                action="recrawl_no_change",
                canonical_url=canonical_url,
                domain=validated.host,
                status_class="ok",
                document_id=document_id,
                version_id=existing.version_id,
            )
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
        candidate_result = process_web_candidate(
            document_id=document_id,
            version_id=version_id,
            canonical_url=canonical_url,
            raw_markdown=scrape.markdown,
            title=display_title,
            domain=validated.host,
            parser_provenance=FIRECRAWL_PARSER_PROVENANCE,
            candidate_dir=self._candidates_dir / version_id,
            originals_dir=self._originals_dir,
            adapter_version=ADAPTER_VERSION,
        )

        version = self._registry.create_version(
            version_id=version_id,
            document_id=document_id,
            checksum=candidate_result.original_sha256,
            extension=".md",
            original_path=str(candidate_result.raw_original_path),
            original_filename=None,
            content_type="text/markdown",
            size_bytes=len(scrape.markdown.encode("utf-8")),
        )
        version = self._registry.update_candidate_artifacts(
            version.version_id,
            parse_status=candidate_result.parse_status,
            candidate_processed_path=str(candidate_result.processed_path),
            candidate_chunks_path=str(candidate_result.chunks_path),
            candidate_canonical_path=str(candidate_result.canonical_path),
            candidate_extraction_path=str(candidate_result.extraction_path),
            parse_warnings=json.dumps(candidate_result.warnings) if candidate_result.warnings else None,
        )
        diff_path: str | None = None
        if prior_version_id is not None:
            diff_path = self._write_recrawl_diff(
                document_id=document_id,
                title=display_title,
                prior_version_id=prior_version_id,
                new_version_id=version.version_id,
                new_candidate_dir=self._candidates_dir / version_id,
            )

        self._registry.create_web_provenance(
            version_id=version.version_id,
            canonical_url=canonical_url,
            url_hash=url_hash,
            retrieved_at=now_iso(),
            firecrawl_action_id=scrape.action_id,
            http_status=scrape.http_status,
            status_class=scrape.status,
            credits_used=scrape.credits_used,
            content_checksum=content_checksum,
            domain=validated.host,
            adapter_version=ADAPTER_VERSION,
            parser_policy=WEB_PARSER_POLICY,
            prior_version_id=prior_version_id,
            diff_path=diff_path,
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

    def _write_recrawl_diff(
        self,
        *,
        document_id: str,
        title: str,
        prior_version_id: str,
        new_version_id: str,
        new_candidate_dir: Path,
    ) -> str | None:
        """Deterministic changed-section summary against the prior version.

        Never blocks the import: if the prior version's canonical Markdown is
        unavailable for any reason, no diff artifact is written and the new
        candidate version is still created (a missing diff is a known
        limitation, not a reason to fail the recrawl).
        """

        prior_version = self._registry.get_version(prior_version_id)
        if prior_version is None or not prior_version.candidate_canonical_path:
            return None
        prior_canonical_path = Path(prior_version.candidate_canonical_path)
        if not prior_canonical_path.is_file():
            # The recorded path exists in the registry but the file itself is
            # gone; a diff computed against a missing prior would report every
            # new section as "added" instead of the documented no-diff case.
            self._registry.record_note(new_version_id, "recrawl_diff_unavailable", f"prior={prior_version_id}")
            return None
        new_canonical_path = new_candidate_dir / "canonical.md"

        diff = compute_section_diff(
            prior_canonical_path=prior_canonical_path,
            new_canonical_path=new_canonical_path,
            document_id=document_id,
            title=title,
        )
        diff_path = new_candidate_dir / "diff.json"
        write_diff_artifact(diff_path, diff)
        self._registry.record_note(
            new_version_id,
            "recrawl_diff",
            f"prior={prior_version_id} added={len(diff.added_sections)} "
            f"removed={len(diff.removed_sections)} changed={len(diff.changed_sections)}",
        )
        return str(diff_path)
