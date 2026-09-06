import os
from uuid import uuid4

import pytest
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken
from mcp.server.fastmcp.exceptions import ToolError
from sqlalchemy import delete, select

from app.db.session import AsyncSessionLocal
from app.mcp.server import create_mcp_server
from app.models.career_profile import CareerProfile
from app.models.experience import Experience
from app.models.skill import Skill
from app.models.user import User

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_DATABASE_TESTS"),
    reason="requires a migrated PostgreSQL test database",
)


def authenticated_user(user_id):
    return AuthenticatedUser(
        AccessToken(
            token="test-token-not-logged",
            client_id="careerpilot-test",
            scopes=["careerpilot:read"],
            subject=str(user_id),
        )
    )


@pytest.mark.asyncio
async def test_mcp_profile_writes_are_serialized_and_cannot_cross_user_ownership():
    marker = uuid4().hex
    async with AsyncSessionLocal() as session:
        user_a = User(
            email=f"mcp-a-{marker}@example.com",
            first_name="A",
            last_name="User",
            password_hash="unused",
        )
        user_b = User(
            email=f"mcp-b-{marker}@example.com",
            first_name="B",
            last_name="User",
            password_hash="unused",
        )
        session.add_all([user_a, user_b])
        await session.flush()
        profile_a = CareerProfile(user_id=user_a.id)
        profile_b = CareerProfile(user_id=user_b.id)
        session.add_all([profile_a, profile_b])
        await session.flush()
        skill_b = Skill(career_profile_id=profile_b.id, name="Private B Skill")
        experience_b = Experience(
            career_profile_id=profile_b.id,
            company="Private B Company",
            job_title="Private B Role",
        )
        session.add_all([skill_b, experience_b])
        await session.commit()
        user_a_id, user_b_id = user_a.id, user_b.id
        skill_b_id, experience_b_id = skill_b.id, experience_b.id

    token = auth_context_var.set(authenticated_user(user_a_id))
    server = create_mcp_server()
    try:
        _, created = await server.call_tool(
            "add_my_skill",
            {"data": {"name": "User A Python", "proficiency_level": "Advanced"}},
        )
        assert created["success"] is True
        assert created["operation"] == "create"
        assert created["item"]["name"] == "User A Python"

        _, skills = await server.call_tool("get_my_skills", {})
        assert [item["name"] for item in skills["result"]] == ["User A Python"]

        with pytest.raises(ToolError):
            await server.call_tool(
                "update_my_experience",
                {
                    "item_id": str(experience_b_id),
                    "changes": {"job_title": "Stolen Role"},
                },
            )
        with pytest.raises(ToolError):
            await server.call_tool("delete_my_skill", {"skill_id": str(skill_b_id)})
    finally:
        auth_context_var.reset(token)

    async with AsyncSessionLocal() as session:
        untouched_skill = await session.get(Skill, skill_b_id)
        untouched_experience = await session.get(Experience, experience_b_id)
        assert untouched_skill.name == "Private B Skill"
        assert untouched_experience.job_title == "Private B Role"
        await session.execute(delete(User).where(User.id.in_([user_a_id, user_b_id])))
        await session.commit()

        remaining = await session.scalars(
            select(Skill).where(Skill.name.in_(["User A Python", "Private B Skill"]))
        )
        assert list(remaining) == []
