from datetime import UTC, datetime

import httpx

from app.integrations.job_sources.base import JobSourceAdapter
from app.schemas.job import JobResult, JobSearchCriteria


class AdzunaJobProvider(JobSourceAdapter):
    name = "Adzuna"
    authority = 30
    base_url = "https://api.adzuna.com/v1/api/jobs"

    def __init__(
        self,
        app_id: str,
        app_key: str,
        country: str = "gb",
        client: httpx.AsyncClient | None = None,
    ):
        self.app_id = app_id
        self.app_key = app_key
        self.country = country.casefold()
        self.client = client

    async def search(self, criteria: JobSearchCriteria) -> list[JobResult]:
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": min(criteria.limit, 50),
            "what": criteria.query,
            "content-type": "application/json",
        }
        if criteria.location:
            params["where"] = criteria.location
        if criteria.employment_type == "full-time":
            params["full_time"] = 1
        elif criteria.employment_type == "part-time":
            params["part_time"] = 1
        url = f"{self.base_url}/{self.country}/search/1"

        async def fetch(client: httpx.AsyncClient):
            response = await client.get(url, params=params, headers={"Accept": "application/json"})
            response.raise_for_status()
            return response.json().get("results", [])

        if self.client:
            rows = await fetch(self.client)
        else:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                rows = await fetch(client)
        now = datetime.now(UTC)
        return [result for row in rows if (result := _normalize(row, now))]


def _normalize(row: dict, retrieved_at: datetime) -> JobResult | None:
    link = row.get("redirect_url")
    company = (row.get("company") or {}).get("display_name")
    if not row.get("id") or not row.get("title") or not company or not link:
        return None
    area = (row.get("location") or {}).get("area") or []
    location = (row.get("location") or {}).get("display_name")
    return JobResult(
        external_id=str(row["id"]),
        source="Adzuna",
        source_url=link,
        title=row["title"],
        company=company,
        company_logo=(row.get("company") or {}).get("logo"),
        via="Adzuna",
        apply_options=[{"title": "Adzuna", "link": link}],
        location=location,
        country=str(area[0]) if area else None,
        workplace_type=_workplace(row, location),
        employment_type=_employment(row),
        description=row.get("description"),
        salary_min=row.get("salary_min"),
        salary_max=row.get("salary_max"),
        salary_currency=None,
        posted_at=row.get("created"),
        apply_url=link,
        retrieved_at=retrieved_at,
    )


def _workplace(row: dict, location: str | None) -> str:
    text = " ".join((str(row.get("title", "")), str(row.get("description", "")), location or ""))
    return "remote" if "remote" in text.casefold() else "unknown"


def _employment(row: dict) -> str | None:
    time = str(row.get("contract_time") or "").replace("_", "-")
    kind = str(row.get("contract_type") or "").replace("_", "-")
    return time or kind or None


AdzunaJobSource = AdzunaJobProvider
