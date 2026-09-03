"""Backward-compatible import path for the single CareerPilot MCP server."""

from app.mcp.server import mcp

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
