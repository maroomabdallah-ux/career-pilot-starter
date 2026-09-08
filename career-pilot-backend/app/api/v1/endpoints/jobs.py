from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AccessTokenDep, CurrentUser, SessionDep
from app.graphs.job_search_graph import job_search_graph, recommendation_graph
from app.mcp.clients.core_client import CareerPilotMCPClient
from app.schemas.job import (
    JobResult,
    JobSearchRequest,
    JobSearchResponse,
    PaginatedJobSearchResponse,
    SavedJobCreate,
    SavedJobResponse,
    SearchHistoryResponse,
)
from app.services.job_search import JobSearchService
from app.services.jobs import SavedJobService

router = APIRouter()
direct_job_search = JobSearchService()
DEFAULT_DISCOVERY_QUERY = (
    "Software Engineer Backend Developer Full Stack Developer AI Engineer Data Analyst"
)


@router.get("/search", response_model=PaginatedJobSearchResponse)
async def paginated_search_jobs(
    session: SessionDep,
    user: CurrentUser,
    q: str = "",
    location: str | None = None,
    page: int = 1,
    page_size: int = 10,
    workplace_type: str | None = None,
    employment_type: str | None = None,
):
    if page < 1 or page_size != 10:
        raise HTTPException(422, "page must be at least 1 and page_size must be 10")
    try:
        state = await recommendation_graph.ainvoke(
            {
                "query": q,
                "location": location,
                "workplace_type": workplace_type,
                "employment_type": employment_type,
            },
            config={
                "configurable": {
                    "session": session,
                    "user_id": user.id,
                    "job_service": direct_job_search,
                }
            },
        )
        result, criteria = state["result"], state["criteria"]
    except Exception as exc:
        raise HTTPException(502, "Unable to load jobs at the moment.") from exc
    start = (page - 1) * page_size
    jobs = result.jobs[start : start + page_size]
    await SavedJobService(session, user.id).record_search(
        criteria, len(jobs), sorted({job.source for job in jobs}), result.source_failures
    )
    return PaginatedJobSearchResponse(
        jobs=jobs,
        page=page,
        page_size=page_size,
        has_next=len(result.jobs) > start + page_size,
        has_previous=page > 1,
        source_failures=result.source_failures,
        message=result.message,
        total_pages=max(1, (len(result.jobs) + 9) // 10),
        context_sources=state["context"].sources,
        search_query=criteria.query,
        search_location=criteria.location or "",
    )


@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(
    data: JobSearchRequest, session: SessionDep, user: CurrentUser, token: AccessTokenDep
):
    if not data.prompt and not data.criteria:
        raise HTTPException(422, "Provide a natural-language request or structured criteria")
    client = CareerPilotMCPClient(token)
    try:
        state = await job_search_graph.ainvoke(
            {
                "prompt": data.prompt or "",
                "supplied_criteria": data.criteria.model_dump(mode="json") if data.criteria else {},
            },
            config={"configurable": {"mcp_client": client}},
        )
    except Exception as exc:
        raise HTTPException(502, "CareerPilot could not search job sources right now") from exc
    if state.get("clarification"):
        return JobSearchResponse(
            criteria=data.criteria or {"query": "clarification required"},
            jobs=[],
            result_count=0,
            message=state["clarification"],
        )
    result = JobSearchResponse.model_validate(state["result"])
    sources = sorted({job.source for job in result.jobs})
    await SavedJobService(session, user.id).record_search(
        result.criteria, result.result_count, sources, result.source_failures
    )
    return result


@router.get("/details/{source}/{external_id}", response_model=JobResult)
async def job_details(source: str, external_id: str, user: CurrentUser, token: AccessTokenDep):
    del user
    try:
        async with CareerPilotMCPClient(token).read_session() as mcp:
            return await mcp.get_job_details(source, external_id)
    except Exception as exc:
        raise HTTPException(404, "Job details expired; run the search again") from exc


@router.get("/saved", response_model=list[SavedJobResponse])
async def saved_jobs(session: SessionDep, user: CurrentUser):
    return await SavedJobService(session, user.id).list()


@router.post("/saved", response_model=SavedJobResponse, status_code=201)
async def save_job(data: SavedJobCreate, session: SessionDep, user: CurrentUser):
    return await SavedJobService(session, user.id).save(data.job)


@router.delete("/saved/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_job(item_id: UUID, session: SessionDep, user: CurrentUser):
    await SavedJobService(session, user.id).unsave(item_id)


@router.get("/search-history", response_model=list[SearchHistoryResponse])
async def search_history(session: SessionDep, user: CurrentUser):
    return await SavedJobService(session, user.id).history()
