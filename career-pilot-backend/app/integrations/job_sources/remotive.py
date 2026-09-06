from datetime import UTC, datetime

import httpx

from app.integrations.job_sources.base import JobSourceAdapter
from app.schemas.job import JobResult, JobSearchCriteria


class RemotiveJobSource(JobSourceAdapter):
    name = "Remotive"
    authority = 20
    url = "https://remotive.com/api/remote-jobs"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self.client = client

    async def search(self, criteria: JobSearchCriteria) -> list[JobResult]:
        async def fetch(client):
            response = await client.get(self.url, params={"search": criteria.query})
            response.raise_for_status()
            return response.json().get("jobs", [])

        if self.client:
            rows = await fetch(self.client)
        else:
            async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
                rows = await fetch(client)
        now = datetime.now(UTC)
        return [
            JobResult(
                external_id=str(row["id"]),
                source=self.name,
                source_url=row["url"],
                title=row["title"],
                company=row["company_name"],
                company_logo=row.get("company_logo"),
                location=row.get("candidate_required_location"),
                workplace_type="remote",
                employment_type=_employment(row.get("job_type")),
                description=row.get("description"),
                skills=[str(tag) for tag in row.get("tags", [])],
                salary_currency=None,
                posted_at=row.get("publication_date"),
                apply_url=row["url"],
                retrieved_at=now,
            )
            for row in rows
            if row.get("id") and row.get("url") and row.get("title") and row.get("company_name")
        ]


def _employment(value):
    return str(value).lower().replace("_", "-") if value else None
