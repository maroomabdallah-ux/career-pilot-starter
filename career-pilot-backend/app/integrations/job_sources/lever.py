from datetime import UTC, datetime

import httpx

from app.integrations.job_sources.base import JobSourceAdapter
from app.integrations.job_sources.catalog import CompanyJobSource
from app.integrations.job_sources.parsing import extract_skills, infer_experience_level, infer_workplace, plain_text
from app.schemas.job import JobResult, JobSearchCriteria


class LeverJobSource(JobSourceAdapter):
    name = "Lever"
    authority = 50
    base_url = "https://api.lever.co/v0/postings"

    def __init__(self, entry: CompanyJobSource, client: httpx.AsyncClient | None = None):
        self.entry, self.client = entry, client

    async def search(self, _criteria: JobSearchCriteria) -> list[JobResult]:
        async def fetch(client: httpx.AsyncClient):
            response = await client.get(
                f"{self.base_url}/{self.entry.board}", params={"mode": "json", "limit": 100},
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()

        if self.client:
            rows = await fetch(self.client)
        else:
            async with httpx.AsyncClient(timeout=18, follow_redirects=True) as client:
                rows = await fetch(client)
        now = datetime.now(UTC)
        return [result for row in rows if (result := self._normalize(row, now))]

    def _normalize(self, row: dict, retrieved_at: datetime) -> JobResult | None:
        link, apply_url = row.get("hostedUrl"), row.get("applyUrl") or row.get("hostedUrl")
        if not row.get("id") or not row.get("text") or not link or not apply_url:
            return None
        categories = row.get("categories") or {}
        description = plain_text(row.get("descriptionPlain") or row.get("description")) or None
        requirements = [
            plain_text(item.get("content")) for item in row.get("lists") or []
            if "require" in str(item.get("text") or "").casefold() and plain_text(item.get("content"))
        ]
        salary, workplace = row.get("salaryRange") or {}, row.get("workplaceType")
        return JobResult(
            external_id=f"{self.entry.board}:{row['id']}", source=self.name, source_url=link,
            title=row["text"], company=self.entry.company, location=categories.get("location"),
            country=row.get("country"), workplace_type=(workplace if workplace in {"remote", "hybrid", "on-site"} else infer_workplace(f"{categories.get('location', '')} {description or ''}")),
            employment_type=categories.get("commitment"),
            experience_level=infer_experience_level(row["text"], description), description=description,
            requirements=requirements, skills=extract_skills(f"{description or ''} {' '.join(requirements)}"),
            salary_min=salary.get("min"), salary_max=salary.get("max"), salary_currency=salary.get("currency"),
            posted_at=(datetime.fromtimestamp(row["createdAt"] / 1000, UTC) if isinstance(row.get("createdAt"), (int, float)) else None),
            apply_url=apply_url, retrieved_at=retrieved_at,
        )
