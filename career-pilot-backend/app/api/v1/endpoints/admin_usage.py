from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies import AdminUser, SessionDep
from app.models.ai_usage import AIUsage
from app.models.user import User
from app.schemas.ai_usage import UsageFilter, UsageSummary
from app.services.ai_usage import UsageAnalyticsService

router = APIRouter()


def filters(date_from=None, date_to=None, user_id=None, agent=None, model=None):
    return UsageFilter(
        date_from=date_from, date_to=date_to, user_id=user_id, agent=agent, model=model
    )


@router.get("/summary", response_model=UsageSummary)
async def summary(
    session: SessionDep,
    admin: AdminUser,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user_id: UUID | None = None,
    agent: str | None = None,
    model: str | None = None,
):
    del admin
    return await UsageAnalyticsService(session).summary(
        filters(date_from, date_to, user_id, agent, model)
    )


def paging(page: int, page_size: int):
    return max(page, 1), min(max(page_size, 1), 100)


@router.get("/by-user")
async def by_user(
    session: SessionDep,
    admin: AdminUser,
    page: int = 1,
    page_size: int = Query(25, le=100),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user_id: UUID | None = None,
    agent: str | None = None,
    model: str | None = None,
):
    del admin
    page, page_size = paging(page, page_size)
    return await UsageAnalyticsService(session).group(
        filters(date_from, date_to, user_id, agent, model),
        [AIUsage.user_id, User.email],
        page,
        page_size,
        join_user=True,
    )


async def grouped(session, values, page, page_size, date_from, date_to, user_id, agent, model):
    page, page_size = paging(page, page_size)
    return await UsageAnalyticsService(session).group(
        filters(date_from, date_to, user_id, agent, model), values, page, page_size
    )


@router.get("/by-agent")
async def by_agent(
    session: SessionDep,
    admin: AdminUser,
    page: int = 1,
    page_size: int = 25,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user_id: UUID | None = None,
    agent: str | None = None,
    model: str | None = None,
):
    del admin
    return await grouped(
        session, [AIUsage.agent_name], page, page_size, date_from, date_to, user_id, agent, model
    )


@router.get("/by-model")
async def by_model(
    session: SessionDep,
    admin: AdminUser,
    page: int = 1,
    page_size: int = 25,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user_id: UUID | None = None,
    agent: str | None = None,
    model: str | None = None,
):
    del admin
    page, page_size = paging(page, page_size)
    return await UsageAnalyticsService(session).models(
        filters(date_from, date_to, user_id, agent, model), page, page_size
    )


@router.get("/by-request")
async def by_request(
    session: SessionDep,
    admin: AdminUser,
    page: int = 1,
    page_size: int = 25,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user_id: UUID | None = None,
    agent: str | None = None,
    model: str | None = None,
):
    del admin
    page, page_size = paging(page, page_size)
    return await UsageAnalyticsService(session).requests(
        filters(date_from, date_to, user_id, agent, model), page, page_size
    )


@router.get("/by-conversation")
async def by_conversation(
    session: SessionDep,
    admin: AdminUser,
    page: int = 1,
    page_size: int = 25,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user_id: UUID | None = None,
    agent: str | None = None,
    model: str | None = None,
):
    del admin
    return await grouped(
        session,
        [AIUsage.conversation_id, AIUsage.user_id],
        page,
        page_size,
        date_from,
        date_to,
        user_id,
        agent,
        model,
    )


@router.get("/daily")
async def daily(
    session: SessionDep,
    admin: AdminUser,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user_id: UUID | None = None,
    agent: str | None = None,
    model: str | None = None,
):
    del admin
    return await UsageAnalyticsService(session).daily(
        filters(date_from, date_to, user_id, agent, model)
    )
