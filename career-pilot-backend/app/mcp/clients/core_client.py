from contextlib import asynccontextmanager
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp import ClientSession

from app.core.config import settings


def build_mcp_client(access_token: str) -> MultiServerMCPClient:
    """Build a request-scoped client carrying the current user's access token."""
    return MultiServerMCPClient(
        {
            "career-pilot-core": {
                "transport": "streamable_http",
                "url": settings.MCP_CORE_SERVER_URL,
                "headers": {"Authorization": f"Bearer {access_token}"},
            }
        }
    )


class CareerPilotMCPReadSession:
    """Typed read gateway over one initialized MCP session."""

    def __init__(self, session: ClientSession):
        self.session = session

    async def call(self, tool: str, arguments: dict[str, Any] | None = None) -> Any:
        result = await self.session.call_tool(tool, arguments or {})
        if result.isError:
            message = " ".join(
                block.text for block in result.content if getattr(block, "type", None) == "text"
            )
            raise RuntimeError(message or f"MCP tool {tool} failed")
        structured = result.structuredContent
        if structured is None:
            raise RuntimeError(f"MCP tool {tool} returned no structured data")
        return structured.get("result", structured)

    async def get_profile(self):
        return await self.call("get_my_profile")

    async def get_skills(self):
        return await self.call("get_my_skills")

    async def get_experience(self):
        return await self.call("get_my_experience")

    async def get_education(self):
        return await self.call("get_my_education")

    async def get_projects(self):
        return await self.call("get_my_projects")

    async def search_career_knowledge(self, **arguments):
        return await self.call("search_my_career_knowledge", arguments)

    async def list_resumes(self):
        return await self.call("list_my_resumes")

    async def get_resume(self, resume_id):
        return await self.call("get_my_resume", {"resume_id": str(resume_id)})

    async def search_jobs(self, criteria):
        return await self.call("search_jobs", {"criteria": criteria})

    async def get_job_details(self, source, external_id):
        return await self.call("get_job_details", {"source": source, "external_id": external_id})

    async def update_profile(self, changes):
        return await self.call("update_my_profile", {"changes": changes})

    async def add_skill(self, data):
        return await self.call("add_my_skill", {"data": data})

    async def update_skill(self, item_id, changes):
        return await self.call("update_my_skill", {"skill_id": str(item_id), "changes": changes})

    async def delete_skill(self, item_id):
        return await self.call("delete_my_skill", {"skill_id": str(item_id)})

    async def add_profile_child(self, domain, data):
        return await self.call(f"add_my_{domain}", {"data": data})

    async def update_profile_child(self, domain, item_id, changes):
        return await self.call(f"update_my_{domain}", {"item_id": str(item_id), "changes": changes})

    async def delete_profile_child(self, domain, item_id):
        return await self.call(f"delete_my_{domain}", {"item_id": str(item_id)})


class CareerPilotMCPClient:
    """Request-scoped authenticated client; configuration remains centralized."""

    def __init__(self, access_token: str):
        self.client = build_mcp_client(access_token)

    @asynccontextmanager
    async def read_session(self):
        async with self.client.session("career-pilot-core") as session:
            yield CareerPilotMCPReadSession(session)
