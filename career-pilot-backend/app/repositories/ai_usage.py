from datetime import UTC, datetime

from sqlalchemy import String, cast, func, select

from app.models.ai_usage import AIUsage
from app.models.user import User


class AIUsageRepository:
    def __init__(self, session):
        self.session = session

    def filtered(self, filters, user_id=None):
        conditions = []
        if user_id or filters.user_id:
            conditions.append(AIUsage.user_id == (user_id or filters.user_id))
        if filters.date_from:
            conditions.append(AIUsage.created_at >= filters.date_from)
        if filters.date_to:
            conditions.append(AIUsage.created_at < filters.date_to)
        if filters.agent:
            conditions.append(AIUsage.agent_name == filters.agent)
        if filters.model:
            conditions.append(AIUsage.model == filters.model)
        return conditions

    async def summary(self, filters, user_id=None):
        conditions = self.filtered(filters, user_id)
        now = datetime.now(UTC)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month = today.replace(day=1)
        total_cost = func.coalesce(func.sum(AIUsage.total_cost), 0)
        row = (
            await self.session.execute(
                select(
                    func.count(AIUsage.id),
                    func.coalesce(func.sum(AIUsage.input_tokens), 0),
                    func.coalesce(func.sum(AIUsage.cached_input_tokens), 0),
                    func.coalesce(func.sum(AIUsage.output_tokens), 0),
                    func.coalesce(func.sum(AIUsage.total_tokens), 0),
                    total_cost,
                    func.coalesce(
                        func.sum(AIUsage.total_cost).filter(AIUsage.created_at >= today), 0
                    ),
                    func.coalesce(
                        func.sum(AIUsage.total_cost).filter(AIUsage.created_at >= month), 0
                    ),
                    func.count(func.distinct(AIUsage.request_id)),
                    func.count(func.distinct(AIUsage.user_id)),
                    func.count(AIUsage.id).filter(
                        AIUsage.pricing_status == "unknown_model_pricing"
                    ),
                    func.count(AIUsage.id).filter(
                        AIUsage.pricing_status == "missing_provider_usage"
                    ),
                    func.count(AIUsage.id).filter(AIUsage.pricing_status == "failed_llm_request"),
                ).where(*conditions)
            )
        ).one()
        return row

    async def grouped(self, filters, group_columns, page, page_size, join_user=False):
        conditions = self.filtered(filters)
        now = datetime.now(UTC)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month = today.replace(day=1)
        query = select(
            *group_columns,
            func.count(AIUsage.id).label("llm_calls"),
            func.coalesce(func.sum(AIUsage.input_tokens), 0).label("input_tokens"),
            func.coalesce(func.sum(AIUsage.cached_input_tokens), 0).label("cached_input_tokens"),
            func.coalesce(func.sum(AIUsage.output_tokens), 0).label("output_tokens"),
            func.coalesce(func.sum(AIUsage.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(AIUsage.total_cost), 0).label("total_cost"),
            func.count(AIUsage.id)
            .filter(AIUsage.pricing_status != "known")
            .label("accounting_issues"),
            func.coalesce(
                func.sum(AIUsage.total_cost).filter(AIUsage.created_at >= today), 0
            ).label("today_cost"),
            func.coalesce(
                func.sum(AIUsage.total_cost).filter(AIUsage.created_at >= month), 0
            ).label("month_cost"),
            func.min(AIUsage.created_at).label("timestamp"),
        )
        if join_user:
            query = query.join(User, User.id == AIUsage.user_id)
        query = (
            query.where(*conditions)
            .group_by(*group_columns)
            .order_by(func.coalesce(func.sum(AIUsage.total_cost), 0).desc())
        )
        return (
            (await self.session.execute(query.offset((page - 1) * page_size).limit(page_size)))
            .mappings()
            .all()
        )

    async def by_request(self, filters, page, page_size):
        columns = [AIUsage.request_id, AIUsage.user_id, User.email]
        query = (
            select(
                *columns,
                func.array_agg(func.distinct(AIUsage.agent_name)).label("agents"),
                func.count(AIUsage.id).label("llm_calls"),
                func.coalesce(func.sum(AIUsage.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.sum(AIUsage.total_cost), 0).label("total_cost"),
                func.min(AIUsage.created_at).label("timestamp"),
            )
            .join(User, User.id == AIUsage.user_id)
            .where(*self.filtered(filters))
            .group_by(*columns)
        )
        query = query.order_by(func.coalesce(func.sum(AIUsage.total_cost), 0).desc())
        return (
            (await self.session.execute(query.offset((page - 1) * page_size).limit(page_size)))
            .mappings()
            .all()
        )

    async def daily(self, filters):
        day = cast(AIUsage.created_at, String).substr(1, 10)
        return (
            (
                await self.session.execute(
                    select(
                        day.label("date"),
                        func.count(AIUsage.id).label("calls"),
                        func.coalesce(func.sum(AIUsage.total_tokens), 0).label("total_tokens"),
                        func.coalesce(func.sum(AIUsage.total_cost), 0).label("total_cost"),
                    )
                    .where(*self.filtered(filters))
                    .group_by(day)
                    .order_by(day)
                )
            )
            .mappings()
            .all()
        )
