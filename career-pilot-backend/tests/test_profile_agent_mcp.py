from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langgraph.types import Command

from app.agents.profile.schemas import IntentResult, ProfileIntent
from app.api.v1.endpoints import profile_agent
from app.graphs.profile_graph import profile_graph


class FakeReads:
    def __init__(self):
        self.calls = []
        self.skills = [{"id": str(uuid4()), "name": "Python"}]

    async def get_profile(self):
        self.calls.append("get_my_profile")
        return {"professional_title": "Engineer"}

    async def get_skills(self):
        self.calls.append("get_my_skills")
        return self.skills

    async def get_education(self):
        self.calls.append("get_my_education")
        return [{"id": str(uuid4()), "institution": "WISE University"}]

    async def get_experience(self):
        self.calls.append("get_my_experience")
        return [{"id": str(uuid4()), "company": "Ebtikar AI", "job_title": "Developer"}]

    async def get_projects(self):
        self.calls.append("get_my_projects")
        return [{"id": str(uuid4()), "name": "CareerPilot"}]

    async def search_career_knowledge(self, **_arguments):
        self.calls.append("search_my_career_knowledge")
        return [{"content": "Supporting context"}]

    async def add_skill(self, data):
        self.calls.append("add_my_skill")
        return {"label": data["name"]}

    async def delete_skill(self, _item_id):
        self.calls.append("delete_my_skill")
        return {"label": "Python"}

    async def update_skill(self, _item_id, changes):
        self.calls.append(("update_my_skill", changes))
        return {"label": changes.get("name", "Python")}

    async def add_profile_child(self, domain, data):
        self.calls.append((f"add_my_{domain}", data))
        return {"label": data.get("name") or data.get("company") or data.get("institution")}

    async def update_profile_child(self, domain, _item_id, changes):
        self.calls.append((f"update_my_{domain}", changes))
        return {"label": "Ebtikar AI"}

    async def delete_profile_child(self, domain, _item_id):
        self.calls.append(f"delete_my_{domain}")
        return {"label": "Target"}


class FakeClient:
    def __init__(self, reads):
        self.reads = reads

    @asynccontextmanager
    async def read_session(self):
        yield self.reads


class FakeUnderstanding:
    result = None

    async def understand(self, _message):
        return self.result


USER = SimpleNamespace(id=uuid4())


@pytest.mark.asyncio
async def test_greeting_makes_no_mcp_call(monkeypatch):
    FakeUnderstanding.result = IntentResult(intent="greeting", confidence=1)
    monkeypatch.setattr(profile_agent, "ProfileUnderstandingService", FakeUnderstanding)
    monkeypatch.setattr(
        profile_agent,
        "CareerPilotMCPClient",
        lambda _token: (_ for _ in ()).throw(AssertionError("MCP must not be created")),
    )
    result = await profile_agent.chat(profile_agent.ChatRequest(message="hi"), USER, "access-token")
    assert result.type == "message"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("message", "intent", "expected"),
    [
        ("What are my skills?", ProfileIntent.READ_SKILLS, ["get_my_skills"]),
        ("شو مهاراتي؟", ProfileIntent.READ_SKILLS, ["get_my_skills"]),
        ("Show my education", ProfileIntent.READ_EDUCATION, ["get_my_education"]),
        ("Show my experience", ProfileIntent.READ_EXPERIENCE, ["get_my_experience"]),
        (
            "Show خبراتي saved in CareerPilot",
            ProfileIntent.READ_EXPERIENCE,
            ["get_my_experience"],
        ),
        ("Show my projects", ProfileIntent.READ_PROJECTS, ["get_my_projects"]),
    ],
)
async def test_profile_reads_are_intent_specific(monkeypatch, message, intent, expected):
    reads = FakeReads()
    FakeUnderstanding.result = IntentResult(intent=intent, confidence=1)
    monkeypatch.setattr(profile_agent, "ProfileUnderstandingService", FakeUnderstanding)
    monkeypatch.setattr(profile_agent, "CareerPilotMCPClient", lambda _token: FakeClient(reads))

    result = await profile_agent.chat(profile_agent.ChatRequest(message=message), USER, "token")

    assert result.type == "message"
    assert reads.calls == expected


@pytest.mark.asyncio
async def test_unstructured_profile_question_can_use_projects_and_rag(monkeypatch):
    reads = FakeReads()
    FakeUnderstanding.result = IntentResult(intent="general_profile_question", confidence=1)
    monkeypatch.setattr(profile_agent, "ProfileUnderstandingService", FakeUnderstanding)
    monkeypatch.setattr(profile_agent, "CareerPilotMCPClient", lambda _token: FakeClient(reads))

    await profile_agent.chat(
        profile_agent.ChatRequest(message="What do you know about my CareerPilot project?"),
        USER,
        "token",
    )
    assert reads.calls == ["get_my_projects", "search_my_career_knowledge"]


@pytest.mark.asyncio
async def test_add_skill_waits_for_approval_and_reject_does_not_write():
    reads = FakeReads()
    client = FakeClient(reads)
    thread = uuid4().hex
    graph_config = profile_agent.config(thread, USER, client)
    proposal = {"domain": "skill", "operation": "create", "fields": {"names": ["FastAPI"]}}

    result = await profile_graph.ainvoke(
        {"user_id": str(USER.id), "proposal": proposal}, config=graph_config
    )
    assert result.get("__interrupt__")
    assert "add_my_skill" not in reads.calls

    rejected = await profile_graph.ainvoke(Command(resume="reject"), config=graph_config)
    assert rejected["result"]["message"] == "The proposed change was discarded."
    assert "add_my_skill" not in reads.calls


@pytest.mark.asyncio
async def test_approved_skill_write_uses_mcp_after_interrupt():
    reads = FakeReads()
    client = FakeClient(reads)
    graph_config = profile_agent.config(uuid4().hex, USER, client)
    proposal = {"domain": "skill", "operation": "create", "fields": {"names": ["FastAPI"]}}
    await profile_graph.ainvoke(
        {"user_id": str(USER.id), "proposal": proposal}, config=graph_config
    )

    approved = await profile_graph.ainvoke(Command(resume="approve"), config=graph_config)

    assert reads.calls == ["add_my_skill"]
    assert approved["result"]["message"] == "Added FastAPI to your Skills."


@pytest.mark.asyncio
async def test_duplicate_skill_and_ambiguous_experience_do_not_create_proposals():
    reads = FakeReads()
    duplicate = IntentResult(intent="add_skill", confidence=1, fields={"names": ["Python"]})
    proposal, problem = await profile_agent.make_proposal(duplicate, reads)
    assert proposal is None
    assert "already exist" in problem

    async def duplicates():
        return [
            {"id": str(uuid4()), "company": "Ebtikar AI", "job_title": "Backend Developer"},
            {"id": str(uuid4()), "company": "Ebtikar AI", "job_title": "AI Engineer"},
        ]

    reads.get_experience = duplicates
    update = IntentResult(
        intent="update_experience",
        confidence=1,
        fields={
            "target": {"company": "Ebtikar AI"},
            "changes": {"job_title": "AI Backend Developer"},
        },
    )
    proposal, problem = await profile_agent.make_proposal(update, reads)
    assert proposal is None
    assert "multiple" in problem


@pytest.mark.asyncio
async def test_missing_required_experience_never_calls_write():
    reads = FakeReads()
    intent = IntentResult(
        intent="add_experience",
        confidence=1,
        fields={"company": "Microsoft"},
        missing_required_fields=["job_title"],
    )
    proposal, problem = await profile_agent.make_proposal(intent, reads)
    assert proposal is None
    assert "job_title" in problem
    assert not any(call.startswith(("add_", "update_", "delete_")) for call in reads.calls)


@pytest.mark.asyncio
async def test_update_experience_changes_only_approved_field_after_approval():
    reads = FakeReads()
    intent = IntentResult(
        intent="update_experience",
        confidence=1,
        fields={
            "target": {"company": "Ebtikar AI"},
            "changes": {"job_title": "AI Backend Developer"},
        },
    )
    proposal, problem = await profile_agent.make_proposal(intent, reads)
    assert problem is None
    client = FakeClient(reads)
    graph_config = profile_agent.config(uuid4().hex, USER, client)
    await profile_graph.ainvoke(
        {"user_id": str(USER.id), "proposal": proposal}, config=graph_config
    )
    assert not any(
        isinstance(call, tuple) and call[0] == "update_my_experience" for call in reads.calls
    )

    await profile_graph.ainvoke(Command(resume="approve"), config=graph_config)

    assert ("update_my_experience", {"job_title": "AI Backend Developer"}) in reads.calls


@pytest.mark.asyncio
async def test_delete_skill_reject_then_repeat_and_approve():
    reads = FakeReads()
    intent = IntentResult(
        intent="delete_skill", confidence=1, fields={"target": {"name": "Python"}}
    )
    proposal, problem = await profile_agent.make_proposal(intent, reads)
    assert problem is None
    client = FakeClient(reads)

    rejected_config = profile_agent.config(uuid4().hex, USER, client)
    await profile_graph.ainvoke(
        {"user_id": str(USER.id), "proposal": proposal}, config=rejected_config
    )
    await profile_graph.ainvoke(Command(resume="reject"), config=rejected_config)
    assert "delete_my_skill" not in reads.calls

    approved_config = profile_agent.config(uuid4().hex, USER, client)
    await profile_graph.ainvoke(
        {"user_id": str(USER.id), "proposal": proposal}, config=approved_config
    )
    await profile_graph.ainvoke(Command(resume="approve"), config=approved_config)
    assert reads.calls.count("delete_my_skill") == 1


@pytest.mark.asyncio
async def test_edit_replaces_pending_values_and_requires_fresh_approval(monkeypatch):
    reads = FakeReads()
    client = FakeClient(reads)
    monkeypatch.setattr(profile_agent, "CareerPilotMCPClient", lambda _token: client)
    thread = uuid4().hex
    proposal = {"domain": "skill", "operation": "create", "fields": {"names": ["FastAPI"]}}
    await profile_graph.ainvoke(
        {"user_id": str(USER.id), "proposal": proposal},
        config=profile_agent.config(thread, USER, client),
    )

    edited = await profile_agent.approve(
        profile_agent.ApprovalRequest(
            thread_id=thread,
            decision="edit",
            edited_fields={"name": "Django"},
        ),
        USER,
        "token",
    )
    assert edited.requires_approval is True
    assert edited.proposal.fields == {"names": ["Django"]}
    assert "add_my_skill" not in reads.calls

    await profile_agent.approve(
        profile_agent.ApprovalRequest(thread_id=thread, decision="approve"),
        USER,
        "token",
    )
    assert "add_my_skill" in reads.calls


@pytest.mark.asyncio
async def test_approval_checkpoint_is_namespaced_by_authenticated_user(monkeypatch):
    reads = FakeReads()
    client = FakeClient(reads)
    monkeypatch.setattr(profile_agent, "CareerPilotMCPClient", lambda _token: client)
    thread = uuid4().hex
    proposal = {
        "domain": "skill",
        "operation": "delete",
        "fields": {"id": str(uuid4()), "name": "Python"},
    }
    await profile_graph.ainvoke(
        {"user_id": str(USER.id), "proposal": proposal},
        config=profile_agent.config(thread, USER, client),
    )
    user_b = SimpleNamespace(id=uuid4())

    with pytest.raises(profile_agent.HTTPException) as denied:
        await profile_agent.approve(
            profile_agent.ApprovalRequest(thread_id=thread, decision="approve"),
            user_b,
            "token-b",
        )
    assert denied.value.status_code == 404
    assert "delete_my_skill" not in reads.calls
