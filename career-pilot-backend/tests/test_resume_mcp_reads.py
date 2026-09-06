from contextlib import asynccontextmanager
from uuid import uuid4

import pytest

from app.graphs.resume_graph import resume_graph
from app.mcp.clients.core_client import build_mcp_client
from app.schemas.resume import ExperienceWriting, ResumeFactValidation, ResumeWriting
from app.services.resume_context import ResumeContextBuilder


class User:
    id = uuid4()
    first_name = "Current"
    last_name = "User"
    email = "current@example.com"


class FakeMCPReads:
    def __init__(self, *, rag_error=False, profile_error=False):
        self.calls = []
        self.rag_error = rag_error
        self.profile_error = profile_error

    async def get_profile(self):
        self.calls.append(("get_my_profile", {}))
        if self.profile_error:
            raise RuntimeError("profile MCP unavailable")
        return {
            "professional_title": "Backend Engineer",
            "professional_summary": "Builds reliable APIs.",
            "city": "Amman",
            "country": "Jordan",
        }

    async def get_skills(self):
        self.calls.append(("get_my_skills", {}))
        return [{"name": "Python", "category": "Backend"}]

    async def get_experience(self):
        self.calls.append(("get_my_experience", {}))
        return [
            {
                "company": "Current User Co",
                "job_title": "Engineer",
                "description": "Built APIs",
                "achievements": ["Improved reliability"],
                "technologies": ["Python"],
                "is_current": True,
            }
        ]

    async def get_education(self):
        self.calls.append(("get_my_education", {}))
        return [{"institution": "Current User University", "degree": "BSc"}]

    async def get_projects(self):
        self.calls.append(("get_my_projects", {}))
        return [{"name": "Current User Portal", "description": "A private portal"}]

    async def search_career_knowledge(self, **arguments):
        self.calls.append(("search_my_career_knowledge", arguments))
        if self.rag_error:
            raise RuntimeError("RAG unavailable")
        return [{"content": f"Relevant: {arguments['query']}"}]


class FakeMCPClient:
    def __init__(self, reads):
        self.reads = reads
        self.sessions = 0

    @asynccontextmanager
    async def read_session(self):
        self.sessions += 1
        yield self.reads


def test_resume_mcp_client_uses_configured_streamable_http_and_bearer_token():
    client = build_mcp_client("request-access-token")
    connection = client.connections["career-pilot-core"]

    assert connection["transport"] == "streamable_http"
    assert connection["headers"] == {"Authorization": "Bearer request-access-token"}


@pytest.mark.asyncio
async def test_resume_context_loads_all_verified_profile_reads_through_one_mcp_session():
    reads = FakeMCPReads()
    client = FakeMCPClient(reads)
    context = await ResumeContextBuilder(User(), "secret-token", client=client).build()

    assert client.sessions == 1
    assert [name for name, _ in reads.calls[:5]] == [
        "get_my_profile",
        "get_my_skills",
        "get_my_experience",
        "get_my_education",
        "get_my_projects",
    ]
    assert context.verified["header"]["professional_title"] == "Backend Engineer"
    assert context.verified["skills"] == [{"name": "Python", "category": "Backend"}]
    assert context.verified["experience"][0]["company"] == "Current User Co"
    assert context.verified["education"][0]["institution"] == "Current User University"
    assert context.verified["projects"][0]["name"] == "Current User Portal"
    assert context.readiness["ready"] is True


@pytest.mark.asyncio
async def test_resume_context_uses_focused_mcp_rag_queries():
    reads = FakeMCPReads()
    context = await ResumeContextBuilder(
        User(), "secret-token", client=FakeMCPClient(reads)
    ).build()
    rag_calls = [
        arguments for name, arguments in reads.calls if name == "search_my_career_knowledge"
    ]

    assert rag_calls[0] == {
        "query": "professional career summary responsibilities achievements",
        "domain": "career",
        "limit": 2,
    }
    assert rag_calls[1]["company"] == "Current User Co"
    assert rag_calls[1]["query"] == "Current User Co Engineer"
    assert rag_calls[2]["project"] == "Current User Portal"
    assert len(context.supporting_rag) == 3


@pytest.mark.asyncio
async def test_optional_mcp_rag_failure_keeps_verified_profile_context():
    reads = FakeMCPReads(rag_error=True)
    context = await ResumeContextBuilder(
        User(), "secret-token", client=FakeMCPClient(reads)
    ).build()

    assert context.readiness["ready"] is True
    assert context.verified["experience"][0]["company"] == "Current User Co"
    assert context.supporting_rag == []


@pytest.mark.asyncio
async def test_required_mcp_profile_failure_fails_context_safely():
    reads = FakeMCPReads(profile_error=True)
    with pytest.raises(RuntimeError, match="profile MCP unavailable"):
        await ResumeContextBuilder(User(), "secret-token", client=FakeMCPClient(reads)).build()


@pytest.mark.asyncio
async def test_include_projects_false_avoids_project_mcp_read():
    reads = FakeMCPReads()
    context = await ResumeContextBuilder(User(), "secret-token", client=FakeMCPClient(reads)).build(
        include_projects=False, with_rag=False
    )

    assert "get_my_projects" not in [name for name, _ in reads.calls]
    assert "search_my_career_knowledge" not in [name for name, _ in reads.calls]
    assert context.verified["projects"] == []


@pytest.mark.asyncio
async def test_resume_generation_summary_and_experience_still_succeed_with_mcp_context(
    monkeypatch,
):
    import app.graphs.resume_graph as graph_module

    context = await ResumeContextBuilder(
        User(), "secret-token", client=FakeMCPClient(FakeMCPReads())
    ).build(with_rag=False)

    class FakeWriter:
        async def generate(self, verified, section, rag):
            assert verified is context.verified
            return ResumeWriting(
                summary="Backend Engineer building reliable APIs.",
                experience=[ExperienceWriting(index=0, bullets=["Built APIs"])],
            )

    class FakeValidator:
        async def validate(self, verified, content, rag):
            return ResumeFactValidation(valid=True)

    monkeypatch.setattr(graph_module, "ResumeWritingService", FakeWriter)
    monkeypatch.setattr(graph_module, "SemanticFactValidationService", FakeValidator)
    result = await resume_graph.ainvoke({"verified": context.verified, "section": "all", "rag": []})

    assert result.get("error") is None
    assert result["content"]["summary"] == "Backend Engineer building reliable APIs."
    assert result["content"]["experience"][0]["bullets"] == ["Built APIs"]
