from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.config import settings


def build_mcp_client() -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {"career-pilot-core": {"transport": "http", "url": settings.MCP_CORE_SERVER_URL}}
    )
