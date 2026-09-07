from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class CompanyJobSource:
    company: str
    provider: Literal["greenhouse", "lever"]
    board: str
    enabled: bool = True


COMPANY_JOB_SOURCES = (
    CompanyJobSource("Stripe", "greenhouse", "stripe"),
    CompanyJobSource("Datadog", "greenhouse", "datadog"),
    CompanyJobSource("Figma", "greenhouse", "figma"),
    CompanyJobSource("Palantir", "lever", "palantir"),
    CompanyJobSource("Binance", "lever", "binance"),
    CompanyJobSource("Aircall", "lever", "aircall"),
)
