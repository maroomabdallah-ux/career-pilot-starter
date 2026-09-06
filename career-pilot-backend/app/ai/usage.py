from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderUsage:
    input_tokens: int
    cached_input_tokens: int | None
    output_tokens: int
    total_tokens: int


def extract_usage(response: Any) -> ProviderUsage | None:
    llm = getattr(response, "llm_output", None) or {}
    raw = llm.get("token_usage") or llm.get("usage")
    if not raw:
        generations = getattr(response, "generations", None) or []
        message = (
            getattr(generations[0][0], "message", None) if generations and generations[0] else None
        )
        metadata = getattr(message, "usage_metadata", None) or {}
        response_meta = getattr(message, "response_metadata", None) or {}
        raw = metadata or response_meta.get("token_usage")
    if not raw:
        return None
    try:
        input_tokens = int(raw.get("input_tokens", raw.get("prompt_tokens", 0)))
        output_tokens = int(raw.get("output_tokens", raw.get("completion_tokens", 0)))
        total_tokens = int(raw.get("total_tokens", input_tokens + output_tokens))
        details = raw.get("input_token_details") or raw.get("prompt_tokens_details") or {}
        cached = details.get("cache_read", details.get("cached_tokens"))
        return ProviderUsage(
            input_tokens, int(cached) if cached is not None else None, output_tokens, total_tokens
        )
    except (TypeError, ValueError, AttributeError):
        return None
