from typing import Any

from mcp.server.fastmcp import FastMCP

from app.mcp.context import run_tool
from app.mcp.schemas import (
    EducationOutput,
    ExperienceOutput,
    ProfileOutput,
    ProjectOutput,
    SkillOutput,
    json_output,
)
from app.services.education import EducationService
from app.services.experience import ExperienceService
from app.services.me import MeService
from app.services.project import ProjectService
from app.services.skill import SkillService


def register(server: FastMCP) -> None:
    @server.tool(structured_output=True)
    async def get_my_profile() -> dict[str, Any]:
        """Return the authenticated user's compact Career Profile."""
        return await run_tool(
            "get_my_profile",
            lambda session, user: _profile(session, user),
        )

    @server.tool(structured_output=True)
    async def get_my_skills() -> list[dict[str, Any]]:
        """Return only skills owned by the authenticated user's Career Profile."""
        return await run_tool(
            "get_my_skills",
            lambda session, user: _children(
                session, user, SkillService(session), "list_skills", SkillOutput
            ),
        )

    @server.tool(structured_output=True)
    async def get_my_experience() -> list[dict[str, Any]]:
        """Return the authenticated user's experience entries."""
        return await run_tool(
            "get_my_experience",
            lambda session, user: _children(
                session, user, ExperienceService(session), "list_experiences", ExperienceOutput
            ),
        )

    @server.tool(structured_output=True)
    async def get_my_education() -> list[dict[str, Any]]:
        """Return the authenticated user's education entries."""
        return await run_tool(
            "get_my_education",
            lambda session, user: _children(
                session, user, EducationService(session), "list_education", EducationOutput
            ),
        )

    @server.tool(structured_output=True)
    async def get_my_projects() -> list[dict[str, Any]]:
        """Return the authenticated user's project entries."""
        return await run_tool(
            "get_my_projects",
            lambda session, user: _children(
                session, user, ProjectService(session), "list_projects", ProjectOutput
            ),
        )


async def _profile(session, user) -> dict[str, Any]:
    item = await MeService(session, user).profile()
    return json_output(ProfileOutput.model_validate(item))


async def _children(session, user, service, method: str, schema) -> list[dict[str, Any]]:
    items = await MeService(session, user).list_children(service, method)
    return json_output([schema.model_validate(item) for item in items])
