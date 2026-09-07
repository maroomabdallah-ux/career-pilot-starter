import re
from datetime import UTC, datetime

import httpx

from app.integrations.job_sources.base import JobSourceAdapter
from app.schemas.job import JobResult, JobSearchCriteria

SALARY_NUMBER = re.compile(r"\d[\d,.]*")
CURRENCY = re.compile(r"\b(USD|EUR|GBP|CAD|AUD|JOD|AED|SAR)\b", re.I)


class JoobleJobSource(JobSourceAdapter):
    name = "Jooble"
    authority = 20
    base_url = "https://jooble.org/api"

    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None):
        self.api_key = api_key
        self.client = client

    async def search(self, criteria: JobSearchCriteria) -> list[JobResult]:
        payload = {
            "keywords": criteria.query,
            "location": criteria.location
            or ("Remote" if criteria.workplace_type == "remote" else ""),
            "page": 1,
            "ResultOnPage": min(criteria.limit, 50),
            "companysearch": False,
        }

        async def fetch(client: httpx.AsyncClient):
            response = await client.post(f"{self.base_url}/{self.api_key}", json=payload)
            response.raise_for_status()
            return response.json().get("jobs", [])

        if self.client:
            rows = await fetch(self.client)
        else:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                rows = await fetch(client)
        now = datetime.now(UTC)
        return [result for row in rows if (result := _normalize(row, now))]


def _normalize(row: dict, retrieved_at: datetime) -> JobResult | None:
    link = row.get("link")
    if not row.get("id") or not row.get("title") or not row.get("company") or not link:
        return None
    salary_min, salary_max, currency = _salary(row.get("salary"))
    text = " ".join(str(row.get(key) or "") for key in ("title", "location", "snippet"))
    return JobResult(
        external_id=str(row["id"]),
        source="Jooble",
        source_url=link,
        title=row["title"],
        company=row["company"],
        location=row.get("location"),
        country=None,
        workplace_type="remote" if "remote" in text.casefold() else "unknown",
        employment_type=str(row["type"]).casefold() if row.get("type") else None,
        description=row.get("snippet"),
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency=currency,
        posted_at=row.get("updated"),
        apply_url=link,
        retrieved_at=retrieved_at,
    )


def _salary(value) -> tuple[float | None, float | None, str | None]:
    text = str(value or "")
    values = []
    for match in SALARY_NUMBER.findall(text):
        try:
            values.append(float(match.replace(",", "")))
        except ValueError:
            pass
    currency = CURRENCY.search(text)
    return (
        values[0] if values else None,
        values[1] if len(values) > 1 else None,
        currency.group(1).upper() if currency else None,
    )
