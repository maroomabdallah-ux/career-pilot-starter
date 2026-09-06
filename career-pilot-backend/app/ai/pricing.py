from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ModelPricing:
    input_per_million: Decimal
    cached_input_per_million: Decimal
    output_per_million: Decimal


# USD prices per one million tokens. Update only this registry when provider pricing changes.
MODEL_PRICING = {
    "gpt-4.1": ModelPricing(Decimal("2.00"), Decimal("0.50"), Decimal("8.00")),
    "gpt-4.1-mini": ModelPricing(Decimal("0.40"), Decimal("0.10"), Decimal("1.60")),
    "gpt-4.1-nano": ModelPricing(Decimal("0.10"), Decimal("0.025"), Decimal("0.40")),
}


def pricing_for(model: str) -> ModelPricing | None:
    normalized = model.casefold()
    for known, pricing in MODEL_PRICING.items():
        if normalized == known or normalized.startswith(f"{known}-"):
            return pricing
    return None
