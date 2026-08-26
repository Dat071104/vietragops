"""Bounded URL/domain safety checks for admin-controlled web import.

Every check here runs BEFORE any Firecrawl network call and before DNS
resolution is trusted. Domain policy is server-owned configuration only --
nothing here accepts a caller-supplied allow/deny list, custom headers,
cookies, or a proxy.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlsplit


MAX_QUERY_LENGTH = 300
DEFAULT_SEARCH_LIMIT = 5

_LOCALHOST_SUFFIXES = (".localhost",)
_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata",
}
_ENCODED_CHAR_RE = re.compile(r"%[0-9a-fA-F]{2}")
_VALID_HOST_RE = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


class WebSafetyError(ValueError):
    """Deterministic rejection of an unsafe URL, domain, or query."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class DomainPolicy:
    """Server-owned domain allow/deny lists. Default-deny when empty."""

    allowed_domains: frozenset[str]
    denied_domains: frozenset[str]

    @staticmethod
    def from_env_values(allowed_csv: str, denied_csv: str) -> "DomainPolicy":
        return DomainPolicy(
            allowed_domains=_parse_domain_csv(allowed_csv),
            denied_domains=_parse_domain_csv(denied_csv),
        )


@dataclass(frozen=True)
class ValidatedURL:
    canonical_url: str
    scheme: str
    host: str
    path: str
    query: str


def _parse_domain_csv(value: str) -> frozenset[str]:
    return frozenset(item.strip().casefold().rstrip(".") for item in (value or "").split(",") if item.strip())


def _domain_matches(host: str, candidates: frozenset[str]) -> bool:
    normalized = host.casefold().rstrip(".")
    for candidate in candidates:
        if normalized == candidate or normalized.endswith("." + candidate):
            return True
    return False


def validate_query(query: str, *, max_length: int = MAX_QUERY_LENGTH) -> str:
    stripped = (query or "").strip()
    if not stripped:
        raise WebSafetyError("empty_query", "Search query must not be empty.")
    if len(stripped) > max_length:
        raise WebSafetyError("query_too_long", f"Search query exceeds {max_length} characters.")
    return stripped


def bounded_search_limit(requested: int | None, *, configured_max: int) -> int:
    """Never exceed the server-configured cap, regardless of caller request."""

    ceiling = max(1, configured_max)
    if requested is None:
        return min(DEFAULT_SEARCH_LIMIT, ceiling)
    return max(1, min(requested, ceiling))


def validate_url_syntax(raw_url: str) -> ValidatedURL:
    """Reject scheme/userinfo/fragment/port/encoding issues.

    This function performs no DNS lookup or domain-policy check; call
    ``enforce_domain_policy`` and ``resolve_and_reject_private_targets``
    afterward.
    """

    candidate = (raw_url or "").strip()
    if not candidate:
        raise WebSafetyError("empty_url", "URL must not be empty.")
    if any(ch.isspace() for ch in candidate) or "\x00" in candidate:
        raise WebSafetyError("malformed_url", "URL must not contain whitespace or control characters.")

    parts = urlsplit(candidate)
    if parts.scheme.casefold() != "https":
        raise WebSafetyError("scheme_not_https", "Only https:// URLs are allowed.")
    if parts.fragment:
        raise WebSafetyError("fragment_not_allowed", "URL fragments are not allowed.")
    if "@" in parts.netloc:
        raise WebSafetyError("userinfo_not_allowed", "URL must not contain embedded userinfo.")
    try:
        port = parts.port
    except ValueError as exc:
        raise WebSafetyError("malformed_url", "URL port is malformed.") from exc
    if port is not None and port != 443:
        raise WebSafetyError("non_default_port", "Only the default HTTPS port is allowed.")

    host = parts.hostname
    if not host:
        raise WebSafetyError("missing_host", "URL must have a host.")
    if _ENCODED_CHAR_RE.search(parts.netloc):
        raise WebSafetyError("encoded_host_not_allowed", "Percent-encoding is not allowed in the host component.")

    if not _is_ip_literal(host) and not _VALID_HOST_RE.match(host):
        raise WebSafetyError("malformed_host", "Host is not a valid DNS name or IP literal.")

    normalized_host = host.casefold().rstrip(".")
    if normalized_host in _BLOCKED_HOSTNAMES or normalized_host.endswith(_LOCALHOST_SUFFIXES):
        raise WebSafetyError("blocked_hostname", "This hostname is never allowed.")

    path = parts.path or "/"
    query = parts.query
    canonical = f"https://{normalized_host}{path}"
    if query:
        canonical = f"{canonical}?{query}"
    return ValidatedURL(canonical_url=canonical, scheme="https", host=normalized_host, path=path, query=query)


def enforce_domain_policy(host: str, policy: DomainPolicy) -> None:
    """Denylist always wins. Empty allowlist means deny-all by default."""

    if _domain_matches(host, policy.denied_domains):
        raise WebSafetyError("domain_denied", f"Domain '{host}' is explicitly denied.")
    if not policy.allowed_domains:
        raise WebSafetyError("domain_not_allowlisted", "No domains are allowlisted; default policy denies all.")
    if not _domain_matches(host, policy.allowed_domains):
        raise WebSafetyError("domain_not_allowlisted", f"Domain '{host}' is not on the server-owned allowlist.")


def resolve_and_reject_private_targets(
    host: str, *, resolver: Callable[..., list] = socket.getaddrinfo
) -> tuple[str, ...]:
    """Resolve ``host`` at request time; reject if any resolved address is
    not globally routable. Handles a literal IP host the same way."""

    if _is_ip_literal(host):
        _reject_if_not_globally_routable(host)
        return (host,)

    try:
        infos = resolver(host, 443, 0, socket.SOCK_STREAM)
    except OSError as exc:
        raise WebSafetyError("dns_resolution_failed", f"Could not resolve host '{host}'.") from exc

    resolved: list[str] = []
    for info in infos:
        sockaddr = info[4]
        address = sockaddr[0]
        _reject_if_not_globally_routable(address)
        resolved.append(address)
    if not resolved:
        raise WebSafetyError("dns_resolution_empty", f"Host '{host}' resolved to no addresses.")
    return tuple(dict.fromkeys(resolved))


def _is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _reject_if_not_globally_routable(address: str) -> None:
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError as exc:
        raise WebSafetyError("invalid_ip_address", f"'{address}' is not a valid IP address.") from exc
    if (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_multicast
        or parsed.is_reserved
        or parsed.is_unspecified
    ):
        raise WebSafetyError("private_network_target", f"Target address '{address}' is not globally routable.")
