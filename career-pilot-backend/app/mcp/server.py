from __future__ import annotations

from typing import Any

import jwt
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

from app.core.config import settings
from app.core.security import decode_token
from app.mcp.tools import register_tools


class CareerPilotTokenVerifier:
    """Validate existing CareerPilot access JWTs without retaining token material."""

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            payload: dict[str, Any] = decode_token(token, "access")
        except (jwt.PyJWTError, KeyError, ValueError):
            return None
        subject = payload.get("sub")
        expires_at = payload.get("exp")
        if not isinstance(subject, str):
            return None
        return AccessToken(
            token=token,
            client_id="careerpilot-backend",
            scopes=["careerpilot:read"],
            expires_at=int(expires_at) if expires_at is not None else None,
            resource=settings.MCP_CORE_SERVER_URL,
            subject=subject,
            claims={"type": "access"},
        )


def create_mcp_server() -> FastMCP:
    server = FastMCP(
        "CareerPilot Core Tools",
        instructions="Authenticated, user-scoped, read-only CareerPilot business tools.",
        token_verifier=CareerPilotTokenVerifier(),
        auth=AuthSettings(
            issuer_url=settings.MCP_AUTH_ISSUER_URL,
            resource_server_url=settings.MCP_CORE_SERVER_URL,
            required_scopes=["careerpilot:read"],
        ),
        host=settings.MCP_HOST,
        port=settings.MCP_PORT,
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
    )
    register_tools(server)
    return server


mcp = create_mcp_server()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
