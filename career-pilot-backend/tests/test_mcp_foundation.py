import inspect
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from mcp.server.fastmcp.exceptions import ToolError
from mcp.shared.memory import create_connected_server_and_client_session

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
    "update_my_profile",
    "add_my_skill",
    "update_my_skill",
    "delete_my_skill",
    "add_my_experience",
    "update_my_experience",
    "delete_my_experience",
    "add_my_education",
    "update_my_education",
    "delete_my_education",
    "add_my_project",
    "update_my_project",
    "delete_my_project",
    "search_jobs",
    "get_job_details",
}


@pytest.mark.asyncio
async def test_mcp_server_instantiates_and_discovers_profile_read_write_tools():
    server = create_mcp_server()
    tools = await server.list_tools()
    assert {tool.name for tool in tools} == EXPECTED_TOOLS
    for tool in tools:
        assert "user_id" not in tool.inputSchema.get("properties", {})


@pytest.mark.asyncio
async def test_mcp_protocol_initializes_and_discovers_expected_tools():
    async with create_connected_server_and_client_session(create_mcp_server()) as client:
        discovered = await client.list_tools()
    assert {tool.name for tool in discovered.tools} == EXPECTED_TOOLS


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


@pytest.mark.asyncio
async def test_profile_child_tools_use_only_current_users_profile(monkeypatch):
    from app.mcp.tools import profile as profile_tools

    user_a = type("User", (), {"id": uuid4()})()
    profile_a = type("Profile", (), {"id": uuid4()})()

    async def fake_run_tool(_name, operation):
        return await operation(object(), user_a)

    class FakeMeService:
        def __init__(self, _session, user):
            assert user.id == user_a.id

        async def profile(self):
            return profile_a

        async def list_children(self, service, method):
            return await getattr(service, method)(profile_a.id)

    class FakeSkillService:
        def __init__(self, _session):
            pass

        async def list_skills(self, profile_id):
            assert profile_id == profile_a.id
            return [
                type(
                    "Skill",
                    (),
                    {
                        "id": uuid4(),
                        "name": "User A Python",
                        "category": "Engineering",
                        "proficiency_level": "Advanced",
                        "years_of_experience": 4,
                    },
                )()
            ]

    class FakeExperienceService:
        def __init__(self, _session):
            pass

        async def list_experiences(self, profile_id):
            assert profile_id == profile_a.id
            return [
                type(
                    "Experience",
                    (),
                    {
                        "id": uuid4(),
                        "company": "User A Company",
                        "job_title": "Engineer",
                        "employment_type": None,
                        "location": None,
                        "start_date": None,
                        "end_date": None,
                        "is_current": True,
                        "description": None,
                        "achievements": [],
                        "technologies": [],
                    },
                )()
            ]

    monkeypatch.setattr(profile_tools, "run_tool", fake_run_tool)
    monkeypatch.setattr(profile_tools, "MeService", FakeMeService)
    monkeypatch.setattr(profile_tools, "SkillService", FakeSkillService)
    monkeypatch.setattr(profile_tools, "ExperienceService", FakeExperienceService)
    server = create_mcp_server()

    _, skills = await server.call_tool("get_my_skills", {})
    _, experiences = await server.call_tool("get_my_experience", {})
    assert [item["name"] for item in skills["result"]] == ["User A Python"]
    assert [item["company"] for item in experiences["result"]] == ["User A Company"]


@pytest.mark.asyncio
async def test_rag_search_is_constructed_with_current_user_id(monkeypatch):
    from app.mcp.tools import rag as rag_tools

    user_a = type("User", (), {"id": uuid4()})()

    async def fake_run_tool(_name, operation):
        return await operation(object(), user_a)

    class FakeKnowledgeService:
        def __init__(self, _session, user_id):
            assert user_id == user_a.id

        async def retrieve(self, query, **filters):
            assert query == "backend systems"
            return [
                type(
                    "Chunk",
                    (),
                    {
                        "content": "User A private knowledge",
                        "metadata_json": {"domain": "career"},
                    },
                )()
            ]

    monkeypatch.setattr(rag_tools, "run_tool", fake_run_tool)
    monkeypatch.setattr(rag_tools, "CareerKnowledgeService", FakeKnowledgeService)
    _, result = await create_mcp_server().call_tool(
        "search_my_career_knowledge", {"query": "backend systems"}
    )
    assert [item["content"] for item in result["result"]] == ["User A private knowledge"]


@pytest.mark.asyncio
async def test_resume_tools_scope_list_and_get_to_current_user(monkeypatch):
    from app.mcp.tools import resume as resume_tools

    user_a_id, user_b_id = uuid4(), uuid4()
    resume_a_id, resume_b_id = uuid4(), uuid4()
    now = datetime.now(UTC)
    records = {
        user_a_id: [
            type(
                "Resume",
                (),
                {
                    "id": resume_a_id,
                    "title": "User A Resume",
                    "document_type": "resume",
                    "version": 1,
                    "status": "draft",
                    "template_id": "clear_ats",
                    "language": "en",
                    "updated_at": now,
                    "content": {"summary": "A"},
                    "design": {},
                },
            )()
        ],
        user_b_id: [
            type(
                "Resume",
                (),
                {
                    "id": resume_b_id,
                    "title": "User B Resume",
                    "document_type": "resume",
                    "version": 1,
                    "status": "draft",
                    "template_id": "clear_ats",
                    "language": "en",
                    "updated_at": now,
                    "content": {"summary": "B"},
                    "design": {},
                },
            )()
        ],
    }

    async def fake_run_tool(_name, operation):
        return await operation(object(), type("User", (), {"id": user_a_id})())

    class FakeResumeService:
        def __init__(self, _session, user_id):
            self.user_id = user_id

        async def list(self):
            return records[self.user_id]

        async def get(self, resume_id):
            match = next((item for item in records[self.user_id] if item.id == resume_id), None)
            if not match:
                raise ValueError("Resume not found")
            return match

    monkeypatch.setattr(resume_tools, "run_tool", fake_run_tool)
    monkeypatch.setattr(resume_tools, "ResumeService", FakeResumeService)
    server = create_mcp_server()
    _, listed = await server.call_tool("list_my_resumes", {})
    assert [item["id"] for item in listed["result"]] == [str(resume_a_id)]
    _, owned = await server.call_tool("get_my_resume", {"resume_id": str(resume_a_id)})
    assert owned["content"] == {"summary": "A"}
    with pytest.raises(ToolError, match="Resume not found"):
        await server.call_tool("get_my_resume", {"resume_id": str(resume_b_id)})
