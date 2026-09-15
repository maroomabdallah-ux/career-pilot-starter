from datetime import UTC, datetime

import httpx
import pytest

from app.schemas.job import JobResult
from app.services.job_links import validate_job_link


def listing():
    return JobResult(
        external_id="1", source="Provider", source_url="https://example.com/job",
        title="Nurse", company="Hospital", apply_url="https://example.com/apply",
        retrieved_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_403_is_restricted_not_invalid(monkeypatch):
    async def get(*args, **kwargs):
        return httpx.Response(403, request=httpx.Request("GET", "https://example.com"))
    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    checked = await validate_job_link(listing())
    assert checked.link_status == "restricted"
    assert checked.link_checked_at is not None


@pytest.mark.asyncio
async def test_removed_link_is_invalid(monkeypatch):
    async def get(*args, **kwargs):
        return httpx.Response(410, request=httpx.Request("GET", "https://example.com"))
    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    assert (await validate_job_link(listing())).link_status == "invalid"
