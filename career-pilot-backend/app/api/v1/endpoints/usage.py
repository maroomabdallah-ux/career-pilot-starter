from datetime import UTC, datetime

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, SessionDep
from app.schemas.ai_usage import UsageFilter, UsageSummary
from app.services.ai_usage import UsageAnalyticsService

router = APIRouter()


@router.get("/me", response_model=UsageSummary)
async def my_usage(session: SessionDep, user: CurrentUser):
    month = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return await UsageAnalyticsService(session).summary(UsageFilter(date_from=month), user.id)
