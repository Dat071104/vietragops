"""Gate 05 Phase 5.4: MCP auth, origin validation, scope enforcement, host
binding guard, and audit trail tests. Protocol-level tests (initialize,
tools/list, tool calls) live in `test_mcp_server.py`; shared fixtures live
in `mcp_test_helpers.py`.
"""

from __future__ import annotations

import asyncio

import httpx2
import pytest

from app.core.config import ROOT
from app.mcp.server import McpConfigurationError, build_mcp_server
from rag.generation.context_builder import ContextBuilder
from rag.retrieval.index_store import ChunkIndexStore
from tests.mcp_test_helpers import (
    TEST_BEARER_TOKEN,
    BackgroundMcpServer,
    authed_session,
    close_session,
    make_lifecycle_service,
    make_test_app,
)


# --- auth / origin rejection (transport-level, no MCP session reached) ---


def test_unauthenticated_request_is_rejected(mcp_live_server):
    server, _built = mcp_live_server

    async def scenario():
        async with httpx2.AsyncClient(timeout=10) as client:
            return await client.post(
                f"{server.base_url}/mcp/",
                headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json"},
                json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            )

    response = asyncio.run(scenario())
    assert response.status_code == 401


def test_malformed_authorization_header_is_rejected(mcp_live_server):
    server, _built = mcp_live_server

    async def scenario():
        async with httpx2.AsyncClient(timeout=10) as client:
            return await client.post(
                f"{server.base_url}/mcp/",
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "Authorization": "NotBearer garbage",
                },
                json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            )

    response = asyncio.run(scenario())
    assert response.status_code == 401


def test_wrong_bearer_token_is_rejected(mcp_live_server):
    server, _built = mcp_live_server

    async def scenario():
        async with httpx2.AsyncClient(timeout=10) as client:
            return await client.post(
                f"{server.base_url}/mcp/",
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer definitely-not-the-configured-token",
                },
                json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            )

    response = asyncio.run(scenario())
    assert response.status_code == 401


def test_no_bearer_token_configured_denies_every_request(tmp_path):
    """Fail closed: an unconfigured server-owned token means no presented
    token can ever authenticate (never a wildcard/always-allow fallback)."""
    app, _built = make_test_app(tmp_path, bearer_token=None)
    server = BackgroundMcpServer(app)
    server.start()

    async def scenario():
        async with httpx2.AsyncClient(timeout=10) as client:
            return await client.post(
                f"{server.base_url}/mcp/",
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer anything-at-all",
                },
                json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            )

    try:
        response = asyncio.run(scenario())
    finally:
        server.stop()
    assert response.status_code == 401


def test_wrong_origin_header_is_rejected(mcp_live_server):
    server, _built = mcp_live_server

    async def scenario():
        async with httpx2.AsyncClient(timeout=10) as client:
            return await client.post(
                f"{server.base_url}/mcp/",
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {TEST_BEARER_TOKEN}",
                    "Origin": "http://evil.example.com",
                },
                json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            )

    response = asyncio.run(scenario())
    assert response.status_code in (401, 403, 421)


# --- host binding guard ---


def test_non_localhost_host_is_rejected_at_construction(tmp_path):
    store = ChunkIndexStore.from_jsonl(ROOT / "data" / "chunks" / "chunks_500.jsonl")
    context_builder = ContextBuilder(store)
    lifecycle_service = make_lifecycle_service(tmp_path)

    with pytest.raises(McpConfigurationError):
        build_mcp_server(
            context_builder=context_builder,
            lifecycle_service=lifecycle_service,
            store=store,
            bearer_token=TEST_BEARER_TOKEN,
            host="0.0.0.0",
        )


# --- audit trail ---


def test_audit_log_records_authorized_tool_calls_without_secrets(mcp_live_server):
    server, built = mcp_live_server

    async def scenario():
        session, transport_cm, http_client = await authed_session(server.base_url, TEST_BEARER_TOKEN)
        try:
            await session.call_tool("index_status", {})
        finally:
            await close_session(session, transport_cm, http_client)

    asyncio.run(scenario())

    records = built.audit.snapshot()
    assert any(r["tool_name"] == "index_status" and r["authorized"] is True and r["status"] == "ok" for r in records)
    for record in records:
        assert set(record) == {"timestamp", "request_id", "tool_name", "authorized", "status"}
        for value in record.values():
            assert TEST_BEARER_TOKEN not in str(value)


def test_audit_log_records_denied_calls_and_is_bounded(mcp_live_server_with_protected_tool):
    server, built = mcp_live_server_with_protected_tool

    async def scenario():
        session, transport_cm, http_client = await authed_session(server.base_url, TEST_BEARER_TOKEN)
        try:
            await session.call_tool("admin_retire_document_version", {"version_id": "x"})
        finally:
            await close_session(session, transport_cm, http_client)

    asyncio.run(scenario())

    records = built.audit.snapshot()
    assert any(
        r["tool_name"] == "admin_retire_document_version" and r["authorized"] is False and r["status"] == "denied"
        for r in records
    )
    assert len(built.audit) <= 500
