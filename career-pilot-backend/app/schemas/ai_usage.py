from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class UsageFilter(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    user_id: UUID | None = None
    agent: str | None = None
    model: str | None = None


class UsageSummary(BaseModel):
    llm_calls: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    total_tokens: int
    total_cost: Decimal
    today_cost: Decimal
    month_cost: Decimal
    average_cost_per_call: Decimal
    average_cost_per_request: Decimal
    active_ai_users: int
    unknown_pricing_calls: int
    missing_usage_calls: int
    failed_llm_calls: int


class UsagePage(BaseModel):
    items: list[dict]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)


class DailyUsage(BaseModel):
    date: date
    calls: int
    total_tokens: int
    total_cost: Decimal
    unusual_cost_spike: bool = False
