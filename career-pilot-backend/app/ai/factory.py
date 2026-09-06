from langchain_openai import ChatOpenAI

from app.ai.callback import UsageTrackingCallback
from app.core.config import settings


def create_chat_model(*, agent_name: str, model: str, **kwargs) -> ChatOpenAI:
    """The only supported construction path for CareerPilot chat models."""
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required for AI features.")
    callbacks = [*kwargs.pop("callbacks", []), UsageTrackingCallback(agent_name, model)]
    return ChatOpenAI(model=model, api_key=settings.OPENAI_API_KEY, callbacks=callbacks, **kwargs)
