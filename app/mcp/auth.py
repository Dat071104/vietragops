"""Server-owned bearer auth for the local MCP surface.

Single, static, server-owned token (no OAuth, no token issuer, no cloud
identity -- explicitly out of scope for this gate). A configured token is
granted the base `mcp:read` scope only; `mcp:admin` is never granted through
this path, so the one protected probe tool (Phase 5.4) can only ever be
reached in a denied state via the real configured token.
"""

from __future__ import annotations

import hmac

from mcp.server.auth.provider import AccessToken, TokenVerifier

READ_SCOPE = "mcp:read"
ADMIN_SCOPE = "mcp:admin"


class StaticBearerTokenVerifier(TokenVerifier):
    """Verifies a single server-owned bearer token via constant-time compare.

    Never logs or echoes the configured or presented token value.
    """

    def __init__(self, configured_token: str | None, scopes: tuple[str, ...] = (READ_SCOPE,)) -> None:
        self._configured_token = configured_token or ""
        self._scopes = list(scopes)

    def configured(self) -> bool:
        return bool(self._configured_token)

    async def verify_token(self, token: str) -> AccessToken | None:
        if not self._configured_token or not token:
            return None
        if not hmac.compare_digest(token, self._configured_token):
            return None
        return AccessToken(
            token=token,
            client_id="local-operator",
            scopes=list(self._scopes),
            expires_at=None,
        )
