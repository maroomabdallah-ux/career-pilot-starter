from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import pytest

from app.agents.jobs.service import understand_job_search
from app.graphs.job_search_graph import job_search_graph
from app.schemas.job import JobResult, JobSearchCriteria
from app.services.job_search import JobSearchService


def job(source="DirectATS", external_id="1", **changes):
    values = dict(
        external_id=external_id,
        source=source,
        source_url=f"https://example.com/{external_id}",
        title="Junior Python Backend Developer",
        company="Acme",
        location="Amman, Jordan",
        workplace_type="remote",
        employment_type="full-time",
        description="Build FastAPI services. Kubernetes is useful.",
        skills=["Python", "FastAPI", "Kubernetes"],
        posted_at=datetime.now(UTC) - timedelta(days=2),
        apply_url=f"https://example.com/{external_id}",
        retrieved_at=datetime.now(UTC),
    )
    values.update(changes)
    return JobResult(**values)


class Source:
    authority = 30

    def __init__(self, name, rows=None, error=None):
        self.name, self.rows, self.error = name, rows or [], error

    async def search(self, _criteria):
        if self.error:
            raise self.error
        return self.rows


class FakeMCP:
    @asynccontextmanager
    async def read_session(self):
        yield self

    async def search_jobs(self, criteria):
        parsed = JobSearchCriteria.model_validate(criteria)
        return {
            "criteria": parsed.model_dump(mode="json"),
            "jobs": [],
            "result_count": 0,
            "source_failures": [],
            "message": None,
        }


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Find remote junior Python backend jobs posted this week", ("remote", "junior", "7d")),
        ("دورلي على شغل backend ريموت", ("remote", None, None)),
        ("بدي شغل FastAPI remote في Amman", ("remote", None, None)),
    ],
)
def test_bilingual_structured_search_intent(message, expected):
    result = understand_job_search(message)
    assert (result["workplace_type"], result["experience_level"], result["date_posted"]) == expected
    assert result["query"]


@pytest.mark.asyncio
async def test_normalize_filter_deduplicate_relevance_and_source_fallback():
    duplicate = job(
        "Secondary",
        "2",
        source_url="https://secondary.test/2",
        apply_url="https://secondary.test/2",
    )
    service = JobSearchService(
        [
            Source("DirectATS", [job()]),
            Source("Secondary", [duplicate]),
            Source("Unavailable", error=RuntimeError("private provider detail")),
        ]
    )
    service.sources[1].authority = 10
    result = await service.search(
        JobSearchCriteria(
            query="Python Backend",
            workplace_type="remote",
            experience_level="junior",
            date_posted="7d",
        ),
        ["Python", "FastAPI"],
    )
    assert result.result_count == 1
    assert result.source_failures == ["Unavailable"]
    found = result.jobs[0]
    assert found.source == "DirectATS"
    assert found.matched_skills == ["Python", "FastAPI"]
    assert "Kubernetes" in found.skill_gaps
    assert found.salary_min is None and found.salary_max is None
    assert not any("Kubernetes" in reason for reason in found.fit_reasons)


@pytest.mark.asyncio
async def test_location_remote_and_experience_filters():
    rows = [
        job(),
        job(
            external_id="local",
            workplace_type="on-site",
            location="Berlin",
            title="Senior Python Backend Developer",
        ),
    ]
    service = JobSearchService([Source("DirectATS", rows)])
    result = await service.search(
        JobSearchCriteria(
            query="Python", location="Amman", workplace_type="remote", experience_level="junior"
        )
    )
    assert [item.external_id for item in result.jobs] == ["1"]


@pytest.mark.asyncio
async def test_short_cache_avoids_repeating_identical_source_call():
    source = Source("DirectATS", [job()])
    calls = 0
    original = source.search

    async def counted(criteria):
        nonlocal calls
        calls += 1
        return await original(criteria)

    source.search = counted
    service = JobSearchService([source])
    criteria = JobSearchCriteria(query="Python", workplace_type="remote")
    await service.search(criteria)
    await service.search(criteria)
    assert calls == 1


@pytest.mark.asyncio
async def test_job_search_graph_accepts_structured_criteria():
    state = await job_search_graph.ainvoke(
        {
            "prompt": "",
            "supplied_criteria": {
                "query": "Python",
                "workplace_type": "remote",
                "limit": 5,
            },
        },
        config={"configurable": {"mcp_client": FakeMCP()}},
    )

    assert state["result"]["criteria"]["query"] == "Python"


@pytest.mark.asyncio
async def test_no_configured_sources_returns_actionable_message():
    result = await JobSearchService(sources=[]).search(JobSearchCriteria(query="Python"))

    assert result.jobs == []
    assert "No job providers are configured" in result.message
