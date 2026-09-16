from contextlib import asynccontextmanager
import asyncio
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


def test_arabic_accounting_search_is_domain_correct():
    result = understand_job_search("دورلي على شغل محاسبة بعمان")

    assert result["query"] == "Accountant"
    assert result["location"] == "Amman"


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
        )
    )
    assert result.result_count == 1
    assert result.source_failures == ["Unavailable"]
    found = result.jobs[0]
    assert found.source == "DirectATS"
    assert found.salary_min is None and found.salary_max is None
    assert found.matched_skills == []
    assert found.skill_gaps == []
    assert found.fit_reasons == []


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
async def test_location_does_not_treat_worldwide_as_a_local_match():
    rows = [
        job(external_id="amman", location="Amman, Jordan"),
        job(external_id="glasgow", location="Glasgow, Scotland"),
        job(external_id="global", location="Worldwide"),
    ]
    result = await JobSearchService([Source("DirectATS", rows)]).search(
        JobSearchCriteria(query="Python", location="Amman")
    )

    assert {item.external_id for item in result.jobs} == {"amman"}


def test_default_discovery_uses_only_google_jobs(monkeypatch):
    monkeypatch.setattr("app.services.job_search.settings.SERPAPI_API_KEY", "configured-key")
    names = [source.name for source in JobSearchService._configured_sources()]
    assert names == ["Google Jobs"]


def test_default_discovery_requires_serpapi_key(monkeypatch):
    monkeypatch.setattr("app.services.job_search.settings.SERPAPI_API_KEY", None)
    assert JobSearchService._configured_sources() == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "title"),
    [
        ("Nurse", "Registered Nurse"),
        ("Accountant", "Management Accountant"),
        ("Backend Developer", "Backend Developer"),
    ],
)
async def test_discovery_search_is_occupation_agnostic(query, title):
    rows = [
        job(external_id="nurse", title="Registered Nurse", description="Clinical patient care"),
        job(external_id="accountant", title="Management Accountant", description="Financial reporting"),
        job(external_id="backend", title="Backend Developer", description="API development"),
    ]

    result = await JobSearchService([Source("GeneralBoard", rows)]).search(
        JobSearchCriteria(query=query)
    )

    assert [item.title for item in result.jobs] == [title]


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
async def test_concurrent_identical_searches_share_one_provider_request():
    source = Source("DirectATS", [job()])
    calls = 0

    async def counted(_criteria):
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        return source.rows

    source.search = counted
    service = JobSearchService([source])
    results = await asyncio.gather(*(service.search(JobSearchCriteria(query="Python")) for _ in range(3)))
    assert calls == 1
    assert all(result.result_count == 1 for result in results)


@pytest.mark.asyncio
async def test_client_cancellation_does_not_cancel_catalog_refresh():
    source = Source("DirectATS", [job()])
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def delayed(_criteria):
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return source.rows

    source.search = delayed
    service = JobSearchService([source])
    criteria = JobSearchCriteria(query="Python")
    client_request = asyncio.create_task(service.search(criteria))
    await started.wait()
    client_request.cancel()
    with pytest.raises(asyncio.CancelledError):
        await client_request
    release.set()
    result = await service.search(criteria)
    assert result.result_count == 1
    assert calls == 1


@pytest.mark.asyncio
async def test_first_results_are_diversified_across_available_sources():
    many = [job("LargeBoard", str(index)) for index in range(5)]
    one = job("CompanyATS", "ats-1", company="Different Co")

    result = await JobSearchService(
        [Source("LargeBoard", many), Source("CompanyATS", [one])]
    ).search(JobSearchCriteria(query="Python", limit=6))

    assert {item.source for item in result.jobs[:2]} == {"LargeBoard", "CompanyATS"}


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
async def test_explicit_discover_query_never_loads_profile_context():
    class ProfileTrackingMCP(FakeMCP):
        profile_reads = 0
        skill_reads = 0

        async def get_profile(self):
            self.profile_reads += 1
            return {"professional_title": "Backend Developer"}

        async def get_skills(self):
            self.skill_reads += 1
            return [{"name": "Python"}]

    mcp = ProfileTrackingMCP()
    state = await job_search_graph.ainvoke(
        {"prompt": "Find Nurse jobs"}, config={"configurable": {"mcp_client": mcp}}
    )

    assert state["result"]["criteria"]["query"] == "Nurse"
    assert state["result"]["criteria"]["skills"] == []
    assert (mcp.profile_reads, mcp.skill_reads) == (0, 0)


@pytest.mark.asyncio
async def test_no_configured_sources_returns_actionable_message():
    result = await JobSearchService(sources=[]).search(JobSearchCriteria(query="Python"))

    assert result.jobs == []
    assert "No job providers are configured" in result.message


@pytest.mark.asyncio
async def test_all_provider_failures_raise_clean_service_error():
    service = JobSearchService([Source("Unavailable", error=RuntimeError("secret detail"))])

    with pytest.raises(RuntimeError, match="All configured job providers are unavailable"):
        await service.search(JobSearchCriteria(query="Python"))


@pytest.mark.asyncio
async def test_default_freshness_excludes_old_and_expired_jobs():
    rows = [
        job(external_id="recent"),
        job(external_id="old", posted_at=datetime.now(UTC) - timedelta(days=61)),
        job(external_id="expired", expires_at=datetime.now(UTC) - timedelta(days=1)),
    ]
    result = await JobSearchService([Source("DirectATS", rows)]).search(
        JobSearchCriteria(query="Python")
    )
    assert [item.external_id for item in result.jobs] == ["recent"]


@pytest.mark.asyncio
async def test_source_confirmed_active_can_survive_imperfect_old_date():
    active = job(
        external_id="active",
        posted_at=datetime.now(UTC) - timedelta(days=90),
        normalized_status="active",
    )
    result = await JobSearchService([Source("DirectATS", [active])]).search(
        JobSearchCriteria(query="Python")
    )
    assert [item.external_id for item in result.jobs] == ["active"]
