import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.ai.callback import UsageTrackingCallback
from app.ai.context import ai_conversation, ai_user_id, request_id_var
from app.core.security import create_access_token
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.ai_usage import AIUsage
from app.models.user import User

pytestmark = pytest.mark.skipif(not os.getenv("RUN_DATABASE_TESTS"), reason="requires PostgreSQL")


def response(input_tokens=100, cached=20, output_tokens=25):
    message = SimpleNamespace(
        usage_metadata={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_token_details": {"cache_read": cached},
        },
        response_metadata={},
    )
    return SimpleNamespace(
        llm_output={"model_name": "gpt-4.1-mini"}, generations=[[SimpleNamespace(message=message)]]
    )


@pytest.mark.asyncio
async def test_four_llm_calls_share_request_and_aggregate_by_conversation():
    marker = uuid4().hex
    async with AsyncSessionLocal() as session:
        user = User(email=f"usage-{marker}@example.com", first_name="Usage", last_name="User")
        session.add(user)
        await session.commit()
        user_id = user.id
    request_token = request_id_var.set("request-four-shared")
    try:
        with ai_user_id(user_id), ai_conversation("conversation-resume-1"):
            callback = UsageTrackingCallback("resume_agent", "gpt-4.1-mini")
            for _ in range(4):
                await callback.on_llm_end(response())
    finally:
        request_id_var.reset(request_token)
    async with AsyncSessionLocal() as session:
        rows = list(await session.scalars(select(AIUsage).where(AIUsage.user_id == user_id)))
        assert len(rows) == 4
        assert {row.request_id for row in rows} == {"request-four-shared"}
        assert {row.conversation_id for row in rows} == {"conversation-resume-1"}
        assert {row.agent_name for row in rows} == {"resume_agent"}
        assert all(row.total_cost is not None and row.pricing_status == "known" for row in rows)
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()


@pytest.mark.asyncio
async def test_admin_api_authorization_and_real_aggregation():
    marker = uuid4().hex
    async with AsyncSessionLocal() as session:
        admin = User(
            email=f"admin-{marker}@example.com", first_name="Admin", last_name="User", is_admin=True
        )
        normal = User(email=f"normal-{marker}@example.com", first_name="Normal", last_name="User")
        session.add_all([admin, normal])
        await session.commit()
        session.add_all(
            [
                AIUsage(
                    user_id=normal.id,
                    request_id="aggregate-one",
                    conversation_id="c1",
                    agent_name="profile_agent",
                    model="gpt-4.1-mini",
                    provider="openai",
                    input_tokens=100,
                    cached_input_tokens=20,
                    output_tokens=50,
                    total_tokens=150,
                    input_cost="0.000032",
                    cached_input_cost="0.000002",
                    output_cost="0.00008",
                    total_cost="0.000114",
                    pricing_status="known",
                ),
                AIUsage(
                    user_id=normal.id,
                    request_id="aggregate-one",
                    conversation_id="c1",
                    agent_name="resume_agent",
                    model="unknown-model",
                    provider="openai",
                    input_tokens=10,
                    cached_input_tokens=None,
                    output_tokens=5,
                    total_tokens=15,
                    pricing_status="unknown_model_pricing",
                ),
            ]
        )
        await session.commit()
        admin_id, normal_id = admin.id, normal.id
    with TestClient(app) as client:
        denied = client.get(
            "/api/v1/admin/usage/summary",
            headers={"Authorization": f"Bearer {create_access_token(normal_id)}"},
        )
        assert denied.status_code == 403
        allowed = client.get(
            "/api/v1/admin/usage/summary",
            headers={"Authorization": f"Bearer {create_access_token(admin_id)}"},
        )
        assert allowed.status_code == 200, allowed.text
        data = allowed.json()
        assert data["llm_calls"] == 2
        assert data["total_tokens"] == 165
        assert data["unknown_pricing_calls"] == 1
        auth = {"Authorization": f"Bearer {create_access_token(admin_id)}"}
        agents = client.get("/api/v1/admin/usage/by-agent", headers=auth).json()["items"]
        assert {row["agent_name"] for row in agents} == {"profile_agent", "resume_agent"}
        models = client.get("/api/v1/admin/usage/by-model", headers=auth).json()["items"]
        assert {row["model"] for row in models} == {"gpt-4.1-mini", "unknown-model"}
        requests = client.get("/api/v1/admin/usage/by-request", headers=auth).json()["items"]
        assert requests[0]["llm_calls"] == 2
        assert set(requests[0]["agents"]) == {"profile_agent", "resume_agent"}
        conversations = client.get("/api/v1/admin/usage/by-conversation", headers=auth).json()[
            "items"
        ]
        assert conversations[0]["conversation_id"] == "c1"
        daily = client.get("/api/v1/admin/usage/daily", headers=auth)
        assert daily.status_code == 200
        assert daily.json()[0]["calls"] == 2
        future = client.get(
            "/api/v1/admin/usage/summary?date_from=2099-01-01T00:00:00Z", headers=auth
        ).json()
        assert future["llm_calls"] == 0
        mine = client.get(
            "/api/v1/usage/me",
            headers={"Authorization": f"Bearer {create_access_token(normal_id)}"},
        )
        assert mine.status_code == 200 and mine.json()["llm_calls"] == 2
    async with AsyncSessionLocal() as session:
        await session.execute(delete(User).where(User.id.in_([admin_id, normal_id])))
        await session.commit()
