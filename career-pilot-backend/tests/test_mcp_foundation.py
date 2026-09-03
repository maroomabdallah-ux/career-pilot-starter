import inspect
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from app.core.security import create_access_token, create_refresh_token
from app.mcp.schemas import ResumeOutput, SkillOutput, json_output
from app.mcp.server import CareerPilotTokenVerifier, create_mcp_server

EXPECTED_TOOLS = {
    "get_my_profile",
    "get_my_skills",
    "get_my_experience",
    "get_my_education",
    "get_my_projects",
    "search_my_career_knowledge",
    "list_my_resumes",
    "get_my_resume",
}


@pytest.mark.asyncio
async def test_mcp_server_instantiates_and_discovers_only_read_tools():
    server = create_mcp_server()
    tools = await server.list_tools()
    assert {tool.name for tool in tools} == EXPECTED_TOOLS
    for tool in tools:
        assert "user_id" not in tool.inputSchema.get("properties", {})


@pytest.mark.asyncio
async def test_mcp_token_verifier_accepts_only_careerpilot_access_tokens():
    user_id = uuid4()
    verifier = CareerPilotTokenVerifier()
    access = await verifier.verify_token(create_access_token(user_id))
    assert access is not None
    assert access.subject == str(user_id)
    assert access.scopes == ["careerpilot:read"]
    assert await verifier.verify_token("invalid") is None
    assert await verifier.verify_token(create_refresh_token(user_id, "refresh-test")) is None


def test_tool_signatures_do_not_expose_identity_arguments():
    server = create_mcp_server()
    for tool in server._tool_manager.list_tools():
        assert "user_id" not in inspect.signature(tool.fn).parameters


def test_mcp_outputs_serialize_uuid_datetime_and_nested_content():
    now = datetime.now(UTC)
    skill = SkillOutput(id=uuid4(), name="Python", years_of_experience=2.5)
    resume = ResumeOutput(
        id=uuid4(),
        title="Backend Resume",
        document_type="resume",
        version=2,
        status="draft",
        template_id="careerpilot_classic",
        language="en",
        updated_at=now,
        content={"summary": "API engineer"},
    )
    encoded = json_output([skill])
    assert isinstance(encoded[0]["id"], str)
    encoded_resume = json_output(resume)
    assert encoded_resume["updated_at"] == now.isoformat().replace("+00:00", "Z")
    assert encoded_resume["content"] == {"summary": "API engineer"}


@pytest.mark.asyncio
async def test_unknown_resume_error_is_clean(monkeypatch):
    from app.mcp.tools import resume as resume_tools

    async def fake_run_tool(_name, operation):
        class Service:
            async def get(self, _resume_id):
                raise ValueError("Resume not found")

        monkeypatch.setattr(resume_tools, "ResumeService", lambda *_: Service())
        try:
            return await operation(object(), type("User", (), {"id": uuid4()})())
        except ValueError as exc:
            raise ToolError(str(exc)) from exc

    monkeypatch.setattr(resume_tools, "run_tool", fake_run_tool)
    server = create_mcp_server()
    with pytest.raises(ToolError, match="Resume not found"):
        await server.call_tool("get_my_resume", {"resume_id": str(uuid4())})
