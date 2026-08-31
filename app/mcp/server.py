"""Gate 05 local MCP server construction.

Localhost-only Streamable HTTP surface: exact host/origin allowlisting via
the SDK's built-in DNS-rebinding protection, server-owned bearer auth (no
OAuth/issuer), server-side scope enforcement per tool call, and a bounded
audit trail. Reuses the existing Gate 04 retrieval/lifecycle/version-trace
architecture as the sole source of truth -- no parallel data path.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from starlette.responses import PlainTextResponse

from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend, RequireAuthMiddleware
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.routing import Mount

from app.mcp.audit import McpAuditLog
from app.mcp.auth import StaticBearerTokenVerifier
from app.mcp.tools import register_tools
from rag.generation.context_builder import ContextBuilder
from rag.lifecycle.service import LifecycleService
from rag.retrieval.index_store import ChunkIndexStore

LOCALHOST_HOST_VALUES = {"127.0.0.1", "localhost", "::1"}

LOCALHOST_TRANSPORT_SECURITY = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=["127.0.0.1", "127.0.0.1:*", "localhost", "localhost:*", "[::1]", "[::1]:*"],
    allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"],
)


class RequiredOriginMiddleware:
    """Reject missing or unapproved Origin headers for the cloud MCP service."""

    def __init__(self, app, allowed_origins: tuple[str, ...]) -> None:
        self.app = app
        self.allowed_origins = frozenset(allowed_origins)

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        headers = {
            key.decode("latin-1").casefold(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        origin = headers.get("origin", "").strip()
        if not origin or origin not in self.allowed_origins:
            response = PlainTextResponse("Origin is not allowed.", status_code=403)
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


class McpConfigurationError(RuntimeError):
    """Raised when the MCP surface is configured to do something this gate forbids."""


@dataclass
class BuiltMcpServer:
    mcp_server: MCPServer
    asgi_app: Starlette
    audit: McpAuditLog
    token_verifier: StaticBearerTokenVerifier


def build_mcp_server(
    *,
    context_builder: ContextBuilder,
    lifecycle_service: LifecycleService,
    store: ChunkIndexStore,
    bearer_token: str | None,
    host: str = "127.0.0.1",
    enable_protected_probe_tool: bool = False,
    audit_log_maxlen: int = 500,
    streamable_http_path: str = "/",
    allowed_origins: tuple[str, ...] = (),
    allowed_hosts: tuple[str, ...] = (),
    cloud_iam: bool = False,
    require_origin: bool = False,
) -> BuiltMcpServer:
    if host not in LOCALHOST_HOST_VALUES and not cloud_iam:
        raise McpConfigurationError(
            f"Refusing to configure the MCP surface for non-localhost host {host!r}; "
            "this gate requires 127.0.0.1-only binding."
        )
    if cloud_iam and not host:
        raise McpConfigurationError("Cloud MCP requires an explicit listener host.")
    if cloud_iam and not allowed_hosts:
        raise McpConfigurationError("Cloud MCP requires an exact allowed Host list.")
    if cloud_iam and not allowed_origins:
        raise McpConfigurationError("Cloud MCP requires an exact allowed Origin list.")
    if cloud_iam and not os.environ.get("K_SERVICE"):
        raise McpConfigurationError("Cloud IAM MCP mode is only valid inside Cloud Run.")

    audit = McpAuditLog(maxlen=audit_log_maxlen)
    token_verifier = StaticBearerTokenVerifier(bearer_token)

    # `MCPServer`'s own `token_verifier`/`auth_server_provider` constructor
    # args hard-require full OAuth `AuthSettings` (`issuer_url`, etc.) --
    # explicitly out of scope for this gate. So auth is composed manually
    # below, entirely outside `MCPServer`, using the SDK's own middleware
    # classes directly.
    mcp_server = MCPServer(
        name="vietragops-mcp",
        instructions="Read-only VietRAGOps retrieval and lifecycle status tools.",
    )
    register_tools(
        mcp_server,
        audit=audit,
        context_builder=context_builder,
        lifecycle_service=lifecycle_service,
        store=store,
        enable_protected_probe_tool=enable_protected_probe_tool,
        platform_authenticated=cloud_iam,
    )

    # Real MCP protocol/session handling from the SDK, unguarded at this
    # layer (no `auth=`/`token_verifier=` given to `MCPServer`, since that
    # path requires OAuth `AuthSettings`/`issuer_url` -- out of scope here).
    transport_security = (
        TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=list(allowed_hosts),
            allowed_origins=list(allowed_origins),
        )
        if cloud_iam
        else LOCALHOST_TRANSPORT_SECURITY
    )
    inner_app = mcp_server.streamable_http_app(
        streamable_http_path=streamable_http_path,
        host=host,
        transport_security=transport_security,
    )
    # Guard it with the SDK's own auth middleware, composed directly instead
    # of through `MCPServer`'s OAuth-only convenience path: `RequireAuthMiddleware`
    # (401 if unauthenticated) wraps the inner app; `AuthenticationMiddleware`
    # + `BearerAuthBackend` verify the bearer token and populate
    # `scope["user"]`; `AuthContextMiddleware` publishes it to the contextvar
    # `get_access_token()` reads inside each tool call. `required_scopes=[]`
    # at the transport level -- scopes are enforced per-tool in `tools.py`
    # instead, so `tools/list` itself only needs valid authentication.
    guarded_inner_app = inner_app if cloud_iam else RequireAuthMiddleware(inner_app, required_scopes=[])
    if require_origin:
        guarded_inner_app = RequiredOriginMiddleware(guarded_inner_app, allowed_origins)
    asgi_app = Starlette(
        routes=[Mount("/", app=guarded_inner_app)],
        middleware=[
            Middleware(AuthenticationMiddleware, backend=BearerAuthBackend(token_verifier)),
            Middleware(AuthContextMiddleware),
        ],
    )

    return BuiltMcpServer(mcp_server=mcp_server, asgi_app=asgi_app, audit=audit, token_verifier=token_verifier)
