from __future__ import annotations

import asyncio

import httpx2
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app.mcp.server import McpConfigurationError, build_mcp_server
from tests.mcp_test_helpers import make_lifecycle_service
from rag.generation.context_builder import ContextBuilder
from rag.retrieval.index_store import ChunkIndexStore
from app.core.config import ROOT


def _build_cloud(tmp_path, monkeypatch):
    monkeypatch.setenv("K_SERVICE", "vietragops-api")
    store = ChunkIndexStore.from_jsonl(ROOT / "data" / "chunks" / "chunks_500.jsonl")
    return build_mcp_server(
        context_builder=ContextBuilder(store),
        lifecycle_service=make_lifecycle_service(tmp_path),
        store=store,
        bearer_token=None,
        host="0.0.0.0",
        allowed_hosts=("api.example",),
        allowed_origins=("https://demo.example",),
        cloud_iam=True,
        require_origin=True,
    )


def test_cloud_mcp_requires_cloud_run_platform_auth_and_exact_lists(tmp_path, monkeypatch):
    monkeypatch.delenv("K_SERVICE", raising=False)
    store = ChunkIndexStore.from_jsonl(ROOT / "data" / "chunks" / "chunks_500.jsonl")
    with pytest.raises(McpConfigurationError):
        build_mcp_server(
            context_builder=ContextBuilder(store),
            lifecycle_service=make_lifecycle_service(tmp_path),
            store=store,
            bearer_token=None,
            host="0.0.0.0",
            allowed_hosts=("api.example",),
            allowed_origins=("https://demo.example",),
            cloud_iam=True,
            require_origin=True,
        )


def test_cloud_mcp_rejects_missing_and_wrong_origin_before_protocol(tmp_path, monkeypatch):
    built = _build_cloud(tmp_path, monkeypatch)

    async def scenario():
        transport = httpx2.ASGITransport(app=built.asgi_app)
        async with httpx2.AsyncClient(transport=transport, base_url="http://api.example") as client:
            common = {"Host": "api.example", "Content-Type": "application/json"}
            missing = await client.post("/", headers=common, json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
            wrong_headers = {**common, "Origin": "https://evil.example"}
            wrong = await client.post("/", headers=wrong_headers, json={"jsonrpc": "2.0", "id": 2, "method": "ping"})
            return missing.status_code, wrong.status_code

    missing_status, wrong_status = asyncio.run(scenario())
    assert missing_status == 403
    assert wrong_status == 403


def test_cloud_mcp_stateless_json_protocol_supports_sequential_calls(tmp_path, monkeypatch):
    built = _build_cloud(tmp_path, monkeypatch)

    async def scenario():
        async with built.mcp_server.session_manager.run():
            transport = httpx2.ASGITransport(app=built.asgi_app)
            async with httpx2.AsyncClient(
                transport=transport,
                base_url="http://api.example",
                headers={"Host": "api.example", "Origin": "https://demo.example"},
            ) as client:
                async with streamable_http_client("http://api.example/", http_client=client) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        tools = await session.list_tools()
                        result = await session.call_tool("index_status", {})
                        return sorted(tool.name for tool in tools.tools), result.is_error

    names, is_error = asyncio.run(scenario())
    assert names == ["document_status", "index_status", "retrieve_context"]
    assert is_error is False
