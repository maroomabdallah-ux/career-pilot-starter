from mcp.server.fastmcp import FastMCP

mcp = FastMCP("CareerPilot Core Tools")


@mcp.tool()
def ping() -> str:
    """Simple starter MCP tool."""
    return "CareerPilot MCP server is ready."


if __name__ == "__main__":
    mcp.run(transport="http")
