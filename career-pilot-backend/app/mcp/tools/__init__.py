from mcp.server.fastmcp import FastMCP

from app.mcp.tools import jobs, profile, profile_write, rag, resume


def register_tools(server: FastMCP) -> None:
    profile.register(server)
    profile_write.register(server)
    rag.register(server)
    resume.register(server)
    jobs.register(server)
