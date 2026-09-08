from datetime import UTC

import httpx
import pytest

from app.integrations.job_sources import SerpApiJobProvider
from app.schemas.job import JobSearchCriteria


@pytest.mark.asyncio
async def test_serpapi_request_normalization_and_pagination():
    async def handler(request: httpx.Request):
        assert request.url.params["engine"] == "google_jobs"
        assert request.url.params["q"] == "Software Engineer"
        assert request.url.params["location"] == "Amman, Jordan"
        assert request.url.params["api_key"] == "secret"
        return httpx.Response(
            200,
            json={
                "jobs_results": [
                    {
                        "job_id": "google-1",
                        "title": "Software Engineer",
                        "company_name": "Example",
                        "location": "Amman, Jordan",
                        "description": "Build Python APIs with FastAPI services",
                        "detected_extensions": {
                            "posted_at": "2 days ago",
                            "schedule_type": "Full-time",
                        },
                        "apply_options": [
                            {"title": "Company", "link": "https://example.com/apply"}
                        ],
                        "share_link": "https://www.google.com/search?q=software+engineer",
                    },
                    {"title": "Incomplete listing"},
                ],
                "serpapi_pagination": {"next_page_token": "next-token"},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await SerpApiJobProvider("secret", client).search(
            JobSearchCriteria(query="Software Engineer", location="Amman, Jordan")
        )

    assert result.next_page_token == "next-token"
    assert len(result.jobs) == 1
    job = result.jobs[0]
    assert job.external_id == "google-1"
    assert job.source == "Google Jobs"
    assert job.employment_type == "Full-time"
    assert job.posted_at and job.posted_at.tzinfo == UTC
    assert job.skills == ["Python", "FastAPI"]


@pytest.mark.asyncio
async def test_serpapi_missing_optional_fields_gets_stable_id():
    row = {
        "title": "Python Developer",
        "company_name": "Example",
        "apply_options": [{"link": "https://example.com/jobs/python"}],
    }

    async def handler(_request: httpx.Request):
        return httpx.Response(200, json={"jobs_results": [row]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = SerpApiJobProvider("secret", client)
        first = await provider.search(JobSearchCriteria(query="Python Developer"))
        second = await provider.search(JobSearchCriteria(query="Python Developer"))

    assert first.jobs[0].external_id == second.jobs[0].external_id
    assert first.jobs[0].location is None
    assert first.jobs[0].posted_at is None


@pytest.mark.asyncio
async def test_serpapi_invalid_key_error_does_not_expose_key():
    async def handler(_request: httpx.Request):
        return httpx.Response(200, json={"error": "Invalid API key supplied"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="rejected") as error:
            await SerpApiJobProvider("do-not-leak", client).search(
                JobSearchCriteria(query="Python Developer")
            )

    assert "do-not-leak" not in str(error.value)
