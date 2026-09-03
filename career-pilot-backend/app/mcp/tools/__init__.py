from mcp.server.fastmcp import FastMCP

from app.mcp.tools import profile, rag, resume


def register_tools(server: FastMCP) -> None:
    profile.register(server)
    rag.register(server)
    resume.register(server)
