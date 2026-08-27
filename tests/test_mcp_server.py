"""Gate 05 Phase 5.3: local MCP surface protocol tests -- initialize,
tools/list, and each approved tool call, plus the protected probe tool's
registration behavior. Security/auth/audit tests live in
`test_mcp_security.py`; shared fixtures live in `mcp_test_helpers.py`.

Runs a real Streamable HTTP server on a dynamic OS-assigned localhost port
(in a background daemon thread -- no subprocess/console window, reliably
joined on teardown), and talks to it with the real `mcp` client SDK.

Uses an isolated `tmp_path` lifecycle service throughout -- the real 37-doc
corpus/lifecycle registry are never touched by these tests. The protected
probe tool is only ever exercised on its denied path, per the Gate 05
contract ("do not perform a live mutation").
"""

from __future__ import annotations

import asyncio

from tests.mcp_test_helpers import TEST_BEARER_TOKEN, authed_session, close_session


def test_initialize_and_tools_list_succeeds_with_valid_bearer_token(mcp_live_server):
    server, _built = mcp_live_server

    async def scenario():
        session, transport_cm, http_client = await authed_session(server.base_url, TEST_BEARER_TOKEN)
        try:
            tools = await session.list_tools()
            return sorted(tool.name for tool in tools.tools)
        finally:
            await close_session(session, transport_cm, http_client)

    names = asyncio.run(scenario())
    assert names == ["document_status", "index_status", "retrieve_context"]


def test_retrieve_context_tool_returns_version_aware_chunks(mcp_live_server):
    server, _built = mcp_live_server

    async def scenario():
        session, transport_cm, http_client = await authed_session(server.base_url, TEST_BEARER_TOKEN)
        try:
            result = await session.call_tool("retrieve_context", {"question": "Cấu trúc email sinh viên là gì?", "top_k": 3})
            return result
        finally:
            await close_session(session, transport_cm, http_client)

    result = asyncio.run(scenario())
    assert result.is_error is False
    assert result.content and result.content[0].type == "text"


def test_index_status_tool_reports_real_index_identity(mcp_live_server):
    server, _built = mcp_live_server

    async def scenario():
        session, transport_cm, http_client = await authed_session(server.base_url, TEST_BEARER_TOKEN)
        try:
            result = await session.call_tool("index_status", {})
            return result
        finally:
            await close_session(session, transport_cm, http_client)

    result = asyncio.run(scenario())
    assert result.is_error is False
    assert "index_version" in result.content[0].text
    assert "chunk_count" in result.content[0].text


def test_document_status_tool_reports_lifecycle_versions(mcp_live_server):
    server, _built = mcp_live_server

    async def scenario():
        session, transport_cm, http_client = await authed_session(server.base_url, TEST_BEARER_TOKEN)
        try:
            result = await session.call_tool("document_status", {"doc_id": "no-such-doc"})
            return result
        finally:
            await close_session(session, transport_cm, http_client)

    result = asyncio.run(scenario())
    assert result.is_error is False
    assert '"versions": []' in result.content[0].text


def test_protected_probe_tool_is_not_registered_when_disabled(mcp_live_server):
    server, _built = mcp_live_server

    async def scenario():
        session, transport_cm, http_client = await authed_session(server.base_url, TEST_BEARER_TOKEN)
        try:
            tools = await session.list_tools()
            return [tool.name for tool in tools.tools]
        finally:
            await close_session(session, transport_cm, http_client)

    names = asyncio.run(scenario())
    assert "admin_retire_document_version" not in names


def test_protected_probe_tool_denies_the_real_configured_token(mcp_live_server_with_protected_tool):
    """The one deliberately protected, scope-gated tool: registered when
    enabled, but the real bearer token this gate ever configures only ever
    grants `mcp:read`, never `mcp:admin` -- so only the denied path is
    reachable. No lifecycle mutation happens (isolated tmp_path registry,
    and the call is expected to fail before reaching the handler body)."""
    server, _built = mcp_live_server_with_protected_tool

    async def scenario():
        session, transport_cm, http_client = await authed_session(server.base_url, TEST_BEARER_TOKEN)
        try:
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            result = await session.call_tool("admin_retire_document_version", {"version_id": "does-not-exist"})
            return names, result
        finally:
            await close_session(session, transport_cm, http_client)

    names, result = asyncio.run(scenario())
    assert "admin_retire_document_version" in names
    assert result.is_error is True
