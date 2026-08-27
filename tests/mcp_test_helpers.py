"""Shared fixtures/helpers for the Gate 05 MCP test suite (test_mcp_server.py,
test_mcp_security.py). Not a test module itself -- no `test_*` name, so
pytest never collects it directly.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import socket
import threading
import time

import pytest
import uvicorn
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from starlette.applications import Starlette

from app.core.config import ROOT
from app.mcp.server import build_mcp_server
from rag.generation.context_builder import ContextBuilder
from rag.lifecycle.registry import LifecycleRegistry
from rag.lifecycle.service import LifecycleService
from rag.retrieval.index_store import ChunkIndexStore

TEST_BEARER_TOKEN = "gate05-test-token"  # test fixture value only, never a real secret


def make_lifecycle_service(tmp_path) -> LifecycleService:
    registry = LifecycleRegistry(tmp_path / "registry.db")
    return LifecycleService(
        registry=registry,
        originals_dir=tmp_path / "originals",
        candidates_dir=tmp_path / "candidates",
        live_manifest_path=tmp_path / "live" / "manifest.csv",
        live_chunks_path=tmp_path / "live" / "chunks.jsonl",
        max_upload_bytes=1_000_000,
    )


def make_test_app(tmp_path, *, bearer_token: str | None = TEST_BEARER_TOKEN, enable_protected_probe_tool: bool = False):
    store = ChunkIndexStore.from_jsonl(ROOT / "data" / "chunks" / "chunks_500.jsonl")
    context_builder = ContextBuilder(store)
    lifecycle_service = make_lifecycle_service(tmp_path)
    built = build_mcp_server(
        context_builder=context_builder,
        lifecycle_service=lifecycle_service,
        store=store,
        bearer_token=bearer_token,
        enable_protected_probe_tool=enable_protected_probe_tool,
    )

    @asynccontextmanager
    async def _lifespan(_app):
        async with built.mcp_server.session_manager.run():
            yield

    app = Starlette(routes=[], lifespan=_lifespan)
    app.mount("/mcp", built.asgi_app)
    return app, built


class BackgroundMcpServer:
    """A real Streamable HTTP server on a dynamic localhost port, run in a
    background daemon thread. No subprocess is spawned (so nothing can flash
    a console window); `stop()` reliably joins the thread."""

    def __init__(self, app):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        self.port = sock.getsockname()[1]
        self.base_url = f"http://127.0.0.1:{self.port}"
        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="warning", lifespan="on")
        self._server = uvicorn.Server(config)
        self._sockets = [sock]
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        asyncio.run(self._server.serve(sockets=self._sockets))

    def start(self):
        self._thread.start()
        deadline = time.time() + 10
        while not self._server.started and time.time() < deadline:
            time.sleep(0.02)
        if not self._server.started:
            raise RuntimeError("Background MCP test server failed to start in time")

    def stop(self):
        self._server.should_exit = True
        self._thread.join(timeout=10)


@pytest.fixture
def mcp_live_server(tmp_path):
    app, built = make_test_app(tmp_path)
    server = BackgroundMcpServer(app)
    server.start()
    try:
        yield server, built
    finally:
        server.stop()


@pytest.fixture
def mcp_live_server_with_protected_tool(tmp_path):
    app, built = make_test_app(tmp_path, enable_protected_probe_tool=True)
    server = BackgroundMcpServer(app)
    server.start()
    try:
        yield server, built
    finally:
        server.stop()


async def authed_session(base_url: str, token: str):
    import httpx2

    http_client = httpx2.AsyncClient(headers={"Authorization": f"Bearer {token}"}, timeout=30)
    transport_cm = streamable_http_client(f"{base_url}/mcp/", http_client=http_client)
    read, write = await transport_cm.__aenter__()
    session = ClientSession(read, write)
    await session.__aenter__()
    await session.initialize()
    return session, transport_cm, http_client


async def close_session(session, transport_cm, http_client):
    await session.__aexit__(None, None, None)
    await transport_cm.__aexit__(None, None, None)
    await http_client.aclose()
