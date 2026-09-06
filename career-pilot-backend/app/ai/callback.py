import logging

from langchain_core.callbacks import AsyncCallbackHandler

from app.ai.context import current_ai_context
from app.ai.service import AIUsageService
from app.ai.usage import extract_usage

logger = logging.getLogger(__name__)


class UsageTrackingCallback(AsyncCallbackHandler):
    def __init__(self, agent_name: str, configured_model: str, provider: str = "openai"):
        self.agent_name = agent_name
        self.configured_model = configured_model
        self.provider = provider

    async def on_llm_end(self, response, **kwargs):
        model = (getattr(response, "llm_output", None) or {}).get(
            "model_name"
        ) or self.configured_model
        try:
            await AIUsageService().record(
                current_ai_context(), self.agent_name, model, self.provider, extract_usage(response)
            )
        except Exception:
            # Accounting is fail-open for the user response, but never silent operationally.
            logger.critical(
                "AI usage persistence failed", extra={"agent": self.agent_name}, exc_info=True
            )

    async def on_llm_error(self, error, **kwargs):
        del error
        try:
            await AIUsageService().record(
                current_ai_context(),
                self.agent_name,
                self.configured_model,
                self.provider,
                None,
                status_override="failed_llm_request",
            )
        except Exception:
            logger.critical(
                "Failed AI call could not be recorded",
                extra={"agent": self.agent_name},
                exc_info=True,
            )
