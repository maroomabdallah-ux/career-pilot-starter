from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.config import settings


def build_mcp_client(access_token: str) -> MultiServerMCPClient:
    """Build a request-scoped client carrying the current user's access token."""
    return MultiServerMCPClient(
        {
            "career-pilot-core": {
                "transport": "http",
                "url": settings.MCP_CORE_SERVER_URL,
                "headers": {"Authorization": f"Bearer {access_token}"},
            }
        }
    )
