from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP

from app.mcp.context import run_tool
from app.mcp.schemas import ResumeOutput, ResumeSummaryOutput, json_output
from app.services.resume import ResumeService


def register(server: FastMCP) -> None:
    @server.tool(structured_output=True)
    async def list_my_resumes() -> list[dict[str, Any]]:
        """List compact Resume metadata owned by the authenticated user."""

        async def operation(session, user):
            items = await ResumeService(session, user.id).list()
            return json_output([ResumeSummaryOutput.model_validate(item) for item in items])

        return await run_tool("list_my_resumes", operation)

    @server.tool(structured_output=True)
    async def get_my_resume(resume_id: UUID) -> dict[str, Any]:
        """Return one structured Resume after enforcing authenticated ownership."""

        async def operation(session, user):
            item = await ResumeService(session, user.id).get(resume_id)
            return json_output(ResumeOutput.model_validate(item))

        return await run_tool("get_my_resume", operation)
