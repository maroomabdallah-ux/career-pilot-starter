from decimal import Decimal

from app.ai.pricing import pricing_for
from app.models.ai_usage import AIUsage
from app.repositories.ai_usage import AIUsageRepository
from app.schemas.ai_usage import UsageFilter, UsageSummary


class UsageAnalyticsService:
    def __init__(self, session):
        self.repository = AIUsageRepository(session)

    async def summary(self, filters: UsageFilter, user_id=None):
        row = await self.repository.summary(filters, user_id)
        calls, requests = row[0], row[8]
        cost = Decimal(row[5])
        return UsageSummary(
            llm_calls=calls,
            input_tokens=row[1],
            cached_input_tokens=row[2],
            output_tokens=row[3],
            total_tokens=row[4],
            total_cost=cost,
            today_cost=row[6],
            month_cost=row[7],
            average_cost_per_call=cost / calls if calls else Decimal(0),
            average_cost_per_request=cost / requests if requests else Decimal(0),
            active_ai_users=row[9],
            unknown_pricing_calls=row[10],
            missing_usage_calls=row[11],
            failed_llm_calls=row[12],
        )

    async def group(self, filters, columns, page, page_size, join_user=False):
        rows = await self.repository.grouped(filters, columns, page, page_size, join_user)
        return {"items": [dict(row) for row in rows], "page": page, "page_size": page_size}

    async def daily(self, filters):
        rows = [dict(row) for row in await self.repository.daily(filters)]
        costs = [Decimal(row["total_cost"]) for row in rows]
        average = sum(costs, Decimal(0)) / len(costs) if costs else Decimal(0)
        for row in rows:
            row["unusual_cost_spike"] = bool(average and Decimal(row["total_cost"]) > average * 2)
        return rows

    async def requests(self, filters, page, page_size):
        rows = await self.repository.by_request(filters, page, page_size)
        return {"items": [dict(row) for row in rows], "page": page, "page_size": page_size}

    async def models(self, filters, page, page_size):
        result = await self.group(filters, [AIUsage.model], page, page_size)
        for row in result["items"]:
            pricing = pricing_for(row["model"])
            row["estimated_cache_savings"] = (
                Decimal(row["cached_input_tokens"])
                / Decimal(1_000_000)
                * (pricing.input_per_million - pricing.cached_input_per_million)
                if pricing
                else None
            )
            calls = max(row["llm_calls"], 1)
            row["average_input_tokens"] = row["input_tokens"] / calls
            row["average_output_tokens"] = row["output_tokens"] / calls
        return result
