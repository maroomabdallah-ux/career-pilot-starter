from datetime import UTC, datetime

import httpx

from app.integrations.job_sources.base import JobSourceAdapter
from app.schemas.job import JobResult, JobSearchCriteria


class ArbeitnowJobSource(JobSourceAdapter):
    name = "Arbeitnow"
    authority = 30
    url = "https://www.arbeitnow.com/api/job-board-api"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self.client = client

    async def search(self, criteria: JobSearchCriteria) -> list[JobResult]:
        async def fetch(client):
            response = await client.get(self.url)
            response.raise_for_status()
            return response.json().get("data", [])

        if self.client:
            rows = await fetch(self.client)
        else:
            async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
                rows = await fetch(client)
        now = datetime.now(UTC)
        return [
            JobResult(
                external_id=str(row["slug"]),
                source=self.name,
                source_url=row["url"],
                title=row["title"],
                company=row["company_name"],
                location=row.get("location"),
                workplace_type="remote" if row.get("remote") else "on-site",
                employment_type=(row.get("job_types") or [None])[0],
                description=row.get("description"),
                skills=[str(tag) for tag in row.get("tags", [])],
                posted_at=(
                    datetime.fromtimestamp(row["created_at"], UTC)
                    if isinstance(row.get("created_at"), (int, float))
                    else row.get("created_at")
                ),
                apply_url=row["url"],
                retrieved_at=now,
            )
            for row in rows
            if row.get("slug") and row.get("url") and row.get("title") and row.get("company_name")
        ]
