import logging

from app.ai.context import AIContext
from app.ai.cost import calculate_cost
from app.ai.pricing import pricing_for
from app.ai.usage import ProviderUsage
from app.db.session import AsyncSessionLocal
from app.models.ai_usage import AIUsage

logger = logging.getLogger(__name__)


class AIUsageService:
    async def record(
        self,
        context: AIContext,
        agent_name: str,
        model: str,
        provider: str,
        usage: ProviderUsage | None,
        status_override: str | None = None,
    ):
        if not context.user_id:
            logger.critical(
                "AI usage missing authenticated user context", extra={"agent": agent_name}
            )
            return None
        pricing = pricing_for(model)
        status = status_override or "known"
        costs = None
        if status_override:
            pass
        elif usage is None:
            status = "missing_provider_usage"
        elif pricing is None:
            status = "unknown_model_pricing"
        else:
            costs = calculate_cost(
                usage.input_tokens, usage.cached_input_tokens, usage.output_tokens, pricing
            )
        item = AIUsage(
            user_id=context.user_id,
            conversation_id=context.conversation_id,
            request_id=context.request_id,
            agent_name=agent_name,
            model=model,
            provider=provider,
            input_tokens=usage.input_tokens if usage else 0,
            cached_input_tokens=usage.cached_input_tokens if usage else None,
            output_tokens=usage.output_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            input_cost=costs.input_cost if costs else None,
            cached_input_cost=costs.cached_input_cost if costs else None,
            output_cost=costs.output_cost if costs else None,
            total_cost=costs.total_cost if costs else None,
            pricing_status=status,
        )
        async with AsyncSessionLocal() as session:
            session.add(item)
            await session.commit()
            await session.refresh(item)
        return item
