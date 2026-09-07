from datetime import UTC, datetime

import httpx

from app.integrations.job_sources.base import JobSourceAdapter
from app.integrations.job_sources.catalog import CompanyJobSource
from app.integrations.job_sources.parsing import extract_skills, infer_experience_level, infer_workplace, plain_text
from app.schemas.job import JobResult, JobSearchCriteria


class GreenhouseJobSource(JobSourceAdapter):
    name = "Greenhouse"
    authority = 50
    base_url = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, entry: CompanyJobSource, client: httpx.AsyncClient | None = None):
        self.entry, self.client = entry, client

    async def search(self, _criteria: JobSearchCriteria) -> list[JobResult]:
        async def fetch(client: httpx.AsyncClient):
            response = await client.get(f"{self.base_url}/{self.entry.board}/jobs", params={"content": "true"})
            response.raise_for_status()
            return response.json().get("jobs", [])

        if self.client:
            rows = await fetch(self.client)
        else:
            async with httpx.AsyncClient(timeout=18, follow_redirects=True) as client:
                rows = await fetch(client)
        now = datetime.now(UTC)
        return [result for row in rows if (result := self._normalize(row, now))]

    def _normalize(self, row: dict, retrieved_at: datetime) -> JobResult | None:
        title, link = row.get("title") or row.get("name"), row.get("absolute_url")
        if not row.get("id") or not title or not link:
            return None
        description = plain_text(row.get("content")) or None
        location = (row.get("location") or {}).get("name")
        text = f"{title} {location or ''} {description or ''}"
        return JobResult(
            external_id=f"{self.entry.board}:{row['id']}", source=self.name, source_url=link,
            title=title, company=row.get("company_name") or self.entry.company, location=location,
            country=None, workplace_type=infer_workplace(text), employment_type=None,
            experience_level=infer_experience_level(title, description), description=description,
            requirements=[], skills=extract_skills(text),
            posted_at=row.get("first_published") or row.get("updated_at"),
            expires_at=row.get("application_deadline"), apply_url=link, retrieved_at=retrieved_at,
        )
