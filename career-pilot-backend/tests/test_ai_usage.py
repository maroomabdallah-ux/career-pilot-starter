from decimal import Decimal
from types import SimpleNamespace

from app.ai.cost import calculate_cost
from app.ai.pricing import ModelPricing, pricing_for
from app.ai.usage import extract_usage


def test_decimal_cost_with_cached_tokens():
    pricing = ModelPricing(Decimal("2"), Decimal("0.5"), Decimal("8"))
    cost = calculate_cost(1_000_000, 250_000, 100_000, pricing)
    assert cost.input_cost == Decimal("1.50")
    assert cost.cached_input_cost == Decimal("0.125")
    assert cost.output_cost == Decimal("0.8")
    assert cost.total_cost == Decimal("2.425")


def test_missing_cached_tokens_are_not_invented():
    pricing = ModelPricing(Decimal("0.4"), Decimal("0.1"), Decimal("1.6"))
    cost = calculate_cost(1000, None, 100, pricing)
    assert cost.cached_input_cost == 0
    assert cost.input_cost == Decimal("0.0004")


def test_unknown_model_has_no_pricing():
    assert pricing_for("provider-model-without-rate") is None


def test_extracts_actual_openai_usage_and_cache_details():
    message = SimpleNamespace(
        usage_metadata={
            "input_tokens": 120,
            "output_tokens": 30,
            "total_tokens": 150,
            "input_token_details": {"cache_read": 40},
        },
        response_metadata={},
    )
    response = SimpleNamespace(llm_output={}, generations=[[SimpleNamespace(message=message)]])
    usage = extract_usage(response)
    assert usage.input_tokens == 120
    assert usage.cached_input_tokens == 40
    assert usage.output_tokens == 30


def test_malformed_or_missing_provider_usage_is_explicitly_missing():
    assert extract_usage(SimpleNamespace(llm_output={}, generations=[])) is None
    assert (
        extract_usage(SimpleNamespace(llm_output={"token_usage": {"prompt_tokens": "bad"}})) is None
    )


def test_profile_and_resume_models_use_central_tracking_factory(monkeypatch):
    from app.agents.profile import service as profile
    from app.agents.resume import service as resume
    from app.ai import factory
    from app.core.config import settings

    class FakeChatModel:
        def __init__(self, **kwargs):
            self.callbacks = kwargs["callbacks"]

        def with_structured_output(self, *_args, **_kwargs):
            return self

    monkeypatch.setattr(factory, "ChatOpenAI", FakeChatModel)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-not-a-real-key")
    profile.get_profile_llm.cache_clear()
    resume.get_resume_llm.cache_clear()
    try:
        assert profile.get_profile_llm().callbacks[0].agent_name == "profile_agent"
        assert resume.get_resume_llm().callbacks[0].agent_name == "resume_agent"
    finally:
        profile.get_profile_llm.cache_clear()
        resume.get_resume_llm.cache_clear()
