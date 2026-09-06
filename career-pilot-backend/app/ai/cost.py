from dataclasses import dataclass
from decimal import Decimal

from app.ai.pricing import ModelPricing

MILLION = Decimal(1_000_000)


@dataclass(frozen=True)
class UsageCost:
    input_cost: Decimal
    cached_input_cost: Decimal
    output_cost: Decimal
    total_cost: Decimal


def calculate_cost(
    input_tokens: int,
    cached_input_tokens: int | None,
    output_tokens: int,
    pricing: ModelPricing,
) -> UsageCost:
    cached = min(max(cached_input_tokens or 0, 0), max(input_tokens, 0))
    uncached = max(input_tokens, 0) - cached
    input_cost = Decimal(uncached) / MILLION * pricing.input_per_million
    cached_cost = Decimal(cached) / MILLION * pricing.cached_input_per_million
    output_cost = Decimal(max(output_tokens, 0)) / MILLION * pricing.output_per_million
    return UsageCost(input_cost, cached_cost, output_cost, input_cost + cached_cost + output_cost)
