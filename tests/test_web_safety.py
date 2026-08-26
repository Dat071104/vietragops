from __future__ import annotations

import socket

import pytest

from rag.lifecycle.web_safety import (
    DomainPolicy,
    WebSafetyError,
    bounded_search_limit,
    enforce_domain_policy,
    resolve_and_reject_private_targets,
    validate_query,
    validate_url_syntax,
)


# -- scheme / syntax -------------------------------------------------------


@pytest.mark.parametrize("scheme", ["http", "file", "ftp", "data", "javascript"])
def test_rejects_non_https_schemes(scheme):
    with pytest.raises(WebSafetyError) as exc:
        validate_url_syntax(f"{scheme}://example.gov.vn/a")
    assert exc.value.code == "scheme_not_https"


def test_rejects_userinfo():
    with pytest.raises(WebSafetyError) as exc:
        validate_url_syntax("https://user:pass@example.gov.vn/a")
    assert exc.value.code == "userinfo_not_allowed"


def test_rejects_fragment():
    with pytest.raises(WebSafetyError) as exc:
        validate_url_syntax("https://example.gov.vn/a#section")
    assert exc.value.code == "fragment_not_allowed"


def test_rejects_non_default_port():
    with pytest.raises(WebSafetyError) as exc:
        validate_url_syntax("https://example.gov.vn:8443/a")
    assert exc.value.code == "non_default_port"


def test_rejects_encoded_host_ambiguity():
    with pytest.raises(WebSafetyError) as exc:
        validate_url_syntax("https://exa%2dmple.gov.vn/a")
    assert exc.value.code == "encoded_host_not_allowed"


def test_rejects_whitespace_in_url():
    with pytest.raises(WebSafetyError) as exc:
        validate_url_syntax("https://example.gov.vn/a b")
    assert exc.value.code == "malformed_url"


def test_rejects_empty_url():
    with pytest.raises(WebSafetyError) as exc:
        validate_url_syntax("   ")
    assert exc.value.code == "empty_url"


def test_accepts_plain_https_url_and_canonicalizes():
    result = validate_url_syntax("HTTPS://Example.GOV.VN/A/b?x=1")
    assert result.canonical_url == "https://example.gov.vn/A/b?x=1"
    assert result.host == "example.gov.vn"


# -- blocked hostnames ------------------------------------------------------


@pytest.mark.parametrize(
    "host",
    ["localhost", "sub.localhost", "metadata.google.internal", "metadata"],
)
def test_rejects_blocked_hostnames(host):
    with pytest.raises(WebSafetyError) as exc:
        validate_url_syntax(f"https://{host}/a")
    assert exc.value.code == "blocked_hostname"


# -- private/reserved IP literals in the URL --------------------------------


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",       # loopback
        "169.254.169.254", # link-local / cloud metadata
        "10.0.0.5",        # RFC1918
        "172.16.0.5",      # RFC1918
        "192.168.1.5",     # RFC1918
        "0.0.0.0",         # unspecified
        "224.0.0.1",       # multicast
        "240.0.0.1",       # reserved
        "::1",             # IPv6 loopback
        "fc00::1",         # IPv6 ULA
        "fe80::1",         # IPv6 link-local
    ],
)
def test_rejects_private_and_reserved_ip_literals(ip):
    host = f"[{ip}]" if ":" in ip else ip
    validated = validate_url_syntax(f"https://{host}/a")
    with pytest.raises(WebSafetyError) as exc:
        resolve_and_reject_private_targets(validated.host)
    assert exc.value.code == "private_network_target"


def test_accepts_public_ip_literal():
    validated = validate_url_syntax("https://93.184.216.34/a")
    resolved = resolve_and_reject_private_targets(validated.host)
    assert resolved == ("93.184.216.34",)


# -- DNS-time private resolution (mocked) -----------------------------------


def _fake_getaddrinfo(*addresses):
    def _resolver(host, port, family, socktype):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (addr, port)) for addr in addresses]

    return _resolver


def test_rejects_hostname_resolving_to_private_address():
    with pytest.raises(WebSafetyError) as exc:
        resolve_and_reject_private_targets("evil.example.com", resolver=_fake_getaddrinfo("10.0.0.1"))
    assert exc.value.code == "private_network_target"


def test_rejects_hostname_resolving_to_metadata_address():
    with pytest.raises(WebSafetyError) as exc:
        resolve_and_reject_private_targets("evil.example.com", resolver=_fake_getaddrinfo("169.254.169.254"))
    assert exc.value.code == "private_network_target"


def test_rejects_if_any_resolved_address_is_private():
    with pytest.raises(WebSafetyError) as exc:
        resolve_and_reject_private_targets(
            "mixed.example.com", resolver=_fake_getaddrinfo("93.184.216.34", "127.0.0.1")
        )
    assert exc.value.code == "private_network_target"


def test_accepts_hostname_resolving_only_to_public_addresses():
    resolved = resolve_and_reject_private_targets(
        "good.example.com", resolver=_fake_getaddrinfo("93.184.216.34", "93.184.216.35")
    )
    assert resolved == ("93.184.216.34", "93.184.216.35")


def test_dns_resolution_failure_is_rejected():
    def _raising_resolver(host, port, family, socktype):
        raise OSError("name resolution failed")

    with pytest.raises(WebSafetyError) as exc:
        resolve_and_reject_private_targets("nonexistent.example.com", resolver=_raising_resolver)
    assert exc.value.code == "dns_resolution_failed"


# -- domain allow/deny policy ------------------------------------------------


def test_default_empty_allowlist_denies_all():
    policy = DomainPolicy.from_env_values("", "")
    with pytest.raises(WebSafetyError) as exc:
        enforce_domain_policy("example.gov.vn", policy)
    assert exc.value.code == "domain_not_allowlisted"


def test_allowlisted_domain_and_subdomain_pass():
    policy = DomainPolicy.from_env_values("example.gov.vn", "")
    enforce_domain_policy("example.gov.vn", policy)
    enforce_domain_policy("docs.example.gov.vn", policy)


def test_denylist_wins_even_if_allowlisted():
    policy = DomainPolicy.from_env_values("example.gov.vn", "example.gov.vn")
    with pytest.raises(WebSafetyError) as exc:
        enforce_domain_policy("example.gov.vn", policy)
    assert exc.value.code == "domain_denied"


def test_domain_not_on_allowlist_is_rejected():
    policy = DomainPolicy.from_env_values("example.gov.vn", "")
    with pytest.raises(WebSafetyError) as exc:
        enforce_domain_policy("other.gov.vn", policy)
    assert exc.value.code == "domain_not_allowlisted"


# -- query / search bounds ---------------------------------------------------


def test_query_length_bound():
    with pytest.raises(WebSafetyError) as exc:
        validate_query("x" * 301)
    assert exc.value.code == "query_too_long"


def test_empty_query_rejected():
    with pytest.raises(WebSafetyError) as exc:
        validate_query("   ")
    assert exc.value.code == "empty_query"


def test_search_limit_defaults_and_is_capped():
    assert bounded_search_limit(None, configured_max=5) == 5
    assert bounded_search_limit(100, configured_max=5) == 5
    assert bounded_search_limit(2, configured_max=5) == 2
    assert bounded_search_limit(0, configured_max=5) == 1
