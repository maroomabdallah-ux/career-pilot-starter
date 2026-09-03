from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from app.mcp.context import run_tool
from app.mcp.schemas import CareerKnowledgeOutput, json_output
from app.services.career_knowledge import CareerKnowledgeService


def register(server: FastMCP) -> None:
    @server.tool(structured_output=True)
    async def search_my_career_knowledge(
        query: Annotated[str, Field(min_length=2, max_length=500)],
        domain: str | None = None,
        company: str | None = None,
        project: str | None = None,
        limit: Annotated[int, Field(ge=1, le=6)] = 5,
    ) -> list[dict[str, Any]]:
        """Search only the authenticated user's saved career knowledge."""

        async def operation(session, user):
            chunks = await CareerKnowledgeService(session, user.id).retrieve(
                query, domain=domain, company=company, project=project, limit=limit
            )
            outputs = []
            for chunk in chunks:
                metadata = chunk.metadata_json or {}
                outputs.append(
                    CareerKnowledgeOutput(
                        content=chunk.content,
                        domain=metadata.get("domain"),
                        company=metadata.get("company"),
                        project=metadata.get("project"),
                        source_type=metadata.get("source_type"),
                        document_title=metadata.get("document_title"),
                    )
                )
            return json_output(outputs)

        return await run_tool("search_my_career_knowledge", operation)
