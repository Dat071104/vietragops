"""Gate 05 MCP tools: narrow, read-oriented, reusing Gate 04's retrieval,
lifecycle, and version-trace architecture as the single source of truth.

Every tool is wrapped by `guarded_tool`, which enforces the required scope
server-side (never trusting client-declared capability alone) and records a
minimal audit event before the handler runs.
"""

from __future__ import annotations

import functools
import inspect
import uuid
from typing import Any, Awaitable, Callable

from mcp.server.auth.middleware.auth_context import get_access_token

from app.mcp.audit import McpAuditLog
from app.mcp.auth import ADMIN_SCOPE, READ_SCOPE
from rag.generation.context_builder import ContextBuilder
from rag.lifecycle.errors import LifecycleError
from rag.lifecycle.service import LifecycleService
from rag.retrieval.index_store import ChunkIndexStore


class ScopeDeniedError(PermissionError):
    """Raised when the authenticated caller lacks a tool's required scope."""


def guarded_tool(
    tool_name: str,
    required_scope: str,
    audit: McpAuditLog,
    *,
    platform_authenticated: bool = False,
) -> Callable:
    """Enforce `required_scope` server-side and audit every call, regardless
    of what a client claims it is permitted to do."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request_id = uuid.uuid4().hex
            access_token = get_access_token()
            platform_read_allowed = platform_authenticated and required_scope == READ_SCOPE and access_token is None
            if not platform_read_allowed and (access_token is None or required_scope not in access_token.scopes):
                audit.record(request_id=request_id, tool_name=tool_name, authorized=False, status="denied")
                raise ScopeDeniedError(f"Missing required scope '{required_scope}' for tool '{tool_name}'.")
            try:
                result = fn(*args, **kwargs)
                if inspect.isawaitable(result):
                    result = await result
            except Exception:
                audit.record(request_id=request_id, tool_name=tool_name, authorized=True, status="error")
                raise
            audit.record(request_id=request_id, tool_name=tool_name, authorized=True, status="ok")
            return result

        return wrapper

    return decorator


def register_tools(
    mcp_server: Any,
    *,
    audit: McpAuditLog,
    context_builder: ContextBuilder,
    lifecycle_service: LifecycleService,
    store: ChunkIndexStore,
    enable_protected_probe_tool: bool,
    platform_authenticated: bool = False,
) -> None:
    """Register the approved coarse tool set on `mcp_server`.

    `enable_protected_probe_tool` only controls whether the one deliberately
    protected, scope-gated probe tool is registered at all -- it never
    changes what scope it requires, and nothing in this gate's configuration
    surface ever grants `mcp:admin`, so even when enabled it only proves the
    denied path (see Phase 5.4 in the Gate 05 contract).
    """

    @mcp_server.tool(name="retrieve_context", description="Retrieve version-aware evidence chunks for a question (read-only).")
    @guarded_tool("retrieve_context", READ_SCOPE, audit, platform_authenticated=platform_authenticated)
    def retrieve_context(question: str, top_k: int = 5) -> dict:
        bundle = context_builder.build(question, top_k=top_k)
        return {
            "chunks": [
                {
                    "doc_id": chunk.get("doc_id"),
                    "chunk_id": chunk.get("chunk_id"),
                    "source_url": chunk.get("source_url"),
                    "text": chunk.get("text"),
                    "support_score": chunk.get("support_score"),
                    "version": chunk.get("version"),
                }
                for chunk in bundle.chunks
            ],
            "retrieval_debug": bundle.retrieval_debug,
        }

    @mcp_server.tool(name="document_status", description="Read-only lifecycle/version status for one document id.")
    @guarded_tool("document_status", READ_SCOPE, audit, platform_authenticated=platform_authenticated)
    def document_status(doc_id: str) -> dict:
        try:
            versions = lifecycle_service.list_versions(doc_id)
        except LifecycleError as exc:
            return {"doc_id": doc_id, "error_code": exc.code, "error_message": exc.message, "versions": []}
        return {
            "doc_id": doc_id,
            "versions": [
                {
                    "version_id": version.version_id,
                    "checksum": version.checksum,
                    "review_status": version.review_status,
                    "parse_status": version.parse_status,
                }
                for version in versions
            ],
        }

    @mcp_server.tool(name="index_status", description="Read-only live index identity and size (Gate 04 version trace).")
    @guarded_tool("index_status", READ_SCOPE, audit, platform_authenticated=platform_authenticated)
    def index_status() -> dict:
        doc_count = len({chunk.doc_id for chunk in store})
        return {
            "index_version": store.index_version,
            "chunk_count": len(store),
            "document_count": doc_count,
        }

    if enable_protected_probe_tool:

        @mcp_server.tool(
            name="admin_retire_document_version",
            description="PROTECTED (mcp:admin, never granted by this gate's configuration): retires one document version.",
        )
        @guarded_tool("admin_retire_document_version", ADMIN_SCOPE, audit)
        def admin_retire_document_version(version_id: str) -> dict:
            version = lifecycle_service.retire(version_id)
            return {"version_id": version.version_id, "review_status": version.review_status}
