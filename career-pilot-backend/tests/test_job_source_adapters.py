import httpx
import pytest

from app.integrations.job_sources import AdzunaJobSource, JoobleJobSource
from app.schemas.job import JobSearchCriteria


@pytest.mark.asyncio
async def test_adzuna_request_and_normalization():
    async def handler(request: httpx.Request):
        assert request.url.params["app_id"] == "app-id"
        assert request.url.params["app_key"] == "app-key"
        assert request.url.params["what"] == "Python Developer"
        assert request.url.params["where"] == "London"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "adz-1",
                        "title": "Remote Python Developer",
                        "company": {"display_name": "Acme"},
                        "location": {"display_name": "London", "area": ["UK", "London"]},
                        "description": "Build APIs remotely",
                        "created": "2026-09-01T12:00:00Z",
                        "redirect_url": "https://www.adzuna.co.uk/jobs/details/adz-1",
                        "contract_time": "full_time",
                        "salary_min": 50000,
                        "salary_max": 60000,
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        jobs = await AdzunaJobSource("app-id", "app-key", "gb", client).search(
            JobSearchCriteria(query="Python Developer", location="London")
        )

    assert len(jobs) == 1
    assert jobs[0].source == "Adzuna"
    assert jobs[0].country == "UK"
    assert jobs[0].salary_min == 50000
    assert jobs[0].workplace_type == "remote"


@pytest.mark.asyncio
async def test_jooble_request_and_normalization():
    async def handler(request: httpx.Request):
        assert request.url.path == "/api/secret-key"
        payload = __import__("json").loads(request.content)
        assert payload["keywords"] == "Backend Developer"
        assert payload["location"] == "Amman"
        return httpx.Response(
            200,
            json={
                "jobs": [
                    {
                        "id": 42,
                        "title": "Backend Developer",
                        "company": "Example Co",
                        "location": "Amman, Jordan",
                        "snippet": "Python services",
                        "salary": "1,500 - 2,000 JOD",
                        "type": "Full-time",
                        "link": "https://jooble.org/jdp/42",
                        "updated": "2026-09-02T10:30:00",
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        jobs = await JoobleJobSource("secret-key", client).search(
            JobSearchCriteria(query="Backend Developer", location="Amman")
        )

    assert len(jobs) == 1
    assert jobs[0].source == "Jooble"
    assert jobs[0].salary_min == 1500
    assert jobs[0].salary_max == 2000
    assert jobs[0].salary_currency == "JOD"


@pytest.mark.asyncio
async def test_provider_http_error_isolated_by_search_service():
    async def handler(_request: httpx.Request):
        return httpx.Response(403, json={"error": "invalid key"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source = JoobleJobSource("bad-key", client)
        with pytest.raises(httpx.HTTPStatusError):
            await source.search(JobSearchCriteria(query="Python", location="Remote"))
