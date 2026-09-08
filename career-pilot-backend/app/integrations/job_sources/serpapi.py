from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta

import httpx

from app.integrations.job_sources.base import JobProvider, JobProviderResult
from app.integrations.job_sources.parsing import (
    extract_skills,
    infer_experience_level,
    infer_workplace,
    plain_text,
)
from app.schemas.job import JobResult, JobSearchCriteria

logger = logging.getLogger(__name__)


class SerpApiJobProvider(JobProvider):
    name = "Google Jobs"
    authority = 40
    url = "https://serpapi.com/search.json"

    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None):
        self.api_key, self.client = api_key, client

    async def search(self, criteria: JobSearchCriteria) -> JobProviderResult:
        params = {"engine": "google_jobs", "q": criteria.query, "api_key": self.api_key}
        if criteria.location:
            params["location"] = criteria.location
        if criteria.page_token:
            params["next_page_token"] = criteria.page_token
        logger.info("Searching jobs: %s / %s", criteria.query, criteria.location or "any location")

        async def fetch(client: httpx.AsyncClient) -> dict:
            response = await client.get(self.url, params=params)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("SerpApi returned an invalid response")
            if payload.get("error"):
                raise ValueError("SerpApi rejected the job search request")
            return payload

        if self.client:
            payload = await fetch(self.client)
        else:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                payload = await fetch(client)
        rows = payload.get("jobs_results") or []
        if not isinstance(rows, list):
            raise ValueError("SerpApi returned invalid job results")
        now = datetime.now(UTC)
        jobs = [job for row in rows if isinstance(row, dict) and (job := _normalize(row, now))]
        logger.info("SerpApi returned: %d results; normalized jobs: %d", len(rows), len(jobs))
        token = (payload.get("serpapi_pagination") or {}).get("next_page_token")
        return JobProviderResult(jobs, token)


def _normalize(row: dict, retrieved_at: datetime) -> JobResult | None:
    title, company = plain_text(row.get("title")), plain_text(row.get("company_name"))
    location = plain_text(row.get("location")) or None
    description = plain_text(row.get("description")) or None
    options = row.get("apply_options") or []
    apply_url = next(
        (x.get("link") for x in options if isinstance(x, dict) and x.get("link")),
        row.get("share_link"),
    )
    if not title or not company or not apply_url:
        return None
    detected = row.get("detected_extensions") or {}
    extensions = [str(value) for value in row.get("extensions") or []]
    employment = detected.get("schedule_type") or next(
        (x for x in extensions if "time" in x.casefold() or "contract" in x.casefold()), None
    )
    posted = detected.get("posted_at") or next(
        (x for x in extensions if "ago" in x.casefold()), None
    )
    text = " ".join(filter(None, (title, location, description, " ".join(extensions))))
    external_id = str(row.get("job_id") or _stable_id(title, company, location))
    normalized_options = [
        {"title": str(option.get("title") or "Apply"), "link": str(option["link"])}
        for option in options
        if isinstance(option, dict) and option.get("link")
    ]
    return JobResult(
        external_id=external_id,
        source="Google Jobs",
        source_url=row.get("share_link") or apply_url,
        title=title,
        company=company,
        company_logo=row.get("thumbnail"),
        via=row.get("via"),
        apply_options=normalized_options,
        location=location,
        workplace_type=infer_workplace(text),
        employment_type=employment,
        experience_level=infer_experience_level(title, description),
        description=description,
        skills=extract_skills(text),
        posted_at=_relative_posted_at(posted, retrieved_at),
        apply_url=apply_url,
        retrieved_at=retrieved_at,
    )


def _stable_id(title: str, company: str, location: str | None) -> str:
    value = "|".join((title.casefold(), company.casefold(), (location or "").casefold()))
    return hashlib.sha256(value.encode()).hexdigest()[:24]


def _relative_posted_at(value: str | None, now: datetime) -> datetime | None:
    if not value:
        return None
    words = value.casefold().split()
    amount = (
        int(words[0])
        if words and words[0].isdigit()
        else 0
        if words and words[0] == "today"
        else None
    )
    if amount is None:
        return None
    unit = next(
        (word for word in words if word.startswith(("hour", "day", "week", "month"))),
        "day" if words[0] == "today" else "",
    )
    if unit.startswith("hour"):
        return now - timedelta(hours=amount)
    if unit.startswith("day"):
        return now - timedelta(days=amount)
    if unit.startswith("week"):
        return now - timedelta(weeks=amount)
    if unit.startswith("month"):
        return now - timedelta(days=30 * amount)
    return None
