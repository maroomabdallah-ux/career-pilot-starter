from typing import Any

from mcp.server.fastmcp import FastMCP

from app.mcp.context import run_tool
from app.mcp.schemas import json_output
from app.schemas.job import JobResult, JobSearchCriteria
from app.services.job_search import JobSearchService
from app.services.me import MeService
from app.services.skill import SkillService

job_search = JobSearchService()


def register(server: FastMCP) -> None:
    @server.tool(structured_output=True)
    async def search_jobs(criteria: JobSearchCriteria) -> dict[str, Any]:
        """Search configured real job sources for the authenticated user."""

        async def operation(session, user):
            skills = await MeService(session, user).list_children(
                SkillService(session), "list_skills"
            )
            result = await job_search.search(criteria, [skill.name for skill in skills])
            return result.model_dump(mode="json")

        return await run_tool("search_jobs", operation)

    @server.tool(structured_output=True)
    async def get_job_details(source: str, external_id: str) -> dict[str, Any]:
        """Return a job seen in the authenticated MCP server's short-lived search cache."""

        async def operation(_session, _user):
            result = job_search.get_details(source, external_id)
            if not result:
                raise ValueError("Job details are unavailable or expired; run the search again")
            return json_output(JobResult.model_validate(result))

        return await run_tool("get_job_details", operation)
