from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.jobs.service import understand_job_search
from app.schemas.job import JobSearchCriteria


class JobSearchState(TypedDict, total=False):
    prompt: str
    supplied_criteria: dict[str, Any]
    extracted: dict[str, Any]
    profile: dict[str, Any]
    skills: list[dict[str, Any]]
    criteria: dict[str, Any]
    clarification: str
    result: dict[str, Any]


async def understand(state):
    if state.get("supplied_criteria"):
        return {"extracted": state["supplied_criteria"]}
    return {"extracted": understand_job_search(state.get("prompt", ""))}


async def load_profile(state, config):
    extracted = state["extracted"]
    # An explicit occupation is a Discover search.  It must remain independent
    # of the member's profile, skills, location, and previous career field.
    if extracted.get("query"):
        return {}
    client = config["configurable"]["mcp_client"]
    async with client.read_session() as mcp:
        profile = await mcp.get_profile()
        skills = await mcp.get_skills()
    return {"profile": profile, "skills": skills}


async def resolve(state):
    values = dict(state["extracted"])
    profile = state.get("profile", {})
    skills = state.get("skills", [])
    if not values.get("query"):
        values["query"] = (
            (profile.get("target_roles") or [None])[0]
            or profile.get("professional_title")
        )
        modes = [str(x).casefold() for x in profile.get("preferred_work_modes", [])]
        if not values.get("workplace_type"):
            values["workplace_type"] = next(
                (x for x in ("remote", "hybrid", "on-site") if x in modes), None
            )
        values["location"] = values.get("location") or (
            profile.get("preferred_locations") or [None]
        )[0]
        values["skills"] = [item["name"] for item in skills[:10]]
    if not values.get("query"):
        return {"clarification": "What job title or career field would you like me to search for?"}
    return {"criteria": JobSearchCriteria(**values).model_dump(mode="json")}


def route(state):
    return "clarify" if state.get("clarification") else "search"


async def search(state, config):
    client = config["configurable"]["mcp_client"]
    async with client.read_session() as mcp:
        result = await mcp.search_jobs(state["criteria"])
    return {"result": result}


builder = StateGraph(JobSearchState)
builder.add_node("understand_search_request", understand)
builder.add_node("load_profile_context", load_profile)
builder.add_node("resolve_search_criteria", resolve)
builder.add_node("search_jobs_mcp", search)
builder.add_edge(START, "understand_search_request")
builder.add_edge("understand_search_request", "load_profile_context")
builder.add_edge("load_profile_context", "resolve_search_criteria")
builder.add_conditional_edges(
    "resolve_search_criteria", route, {"clarify": END, "search": "search_jobs_mcp"}
)
builder.add_edge("search_jobs_mcp", END)
job_search_graph = builder.compile()


# The browser's discovery flow uses the same providers and deterministic ranking,
# orchestrated with LangGraph. The existing MCP conversational flow remains available.
class RecommendationState(TypedDict, total=False):
    query: str
    location: str | None
    workplace_type: str | None
    employment_type: str | None
    context: Any
    criteria: Any
    result: Any


async def recommendation_context(state, config):
    from app.services.job_recommendations import load_career_context

    deps = config["configurable"]
    return {"context": await load_career_context(deps["session"], deps["user_id"])}


async def recommendation_criteria(state):
    context = state["context"]
    from app.services.job_recommendations import expand_search_roles

    expansions = expand_search_roles(context)
    # Providers receive one focused occupation, not a concatenation of every
    # role and skill in the profile (which is too restrictive to match).
    query = state.get("query", "").strip() or (context.roles or expansions or [""])[0]
    if not query:
        query = "career opportunities"
    location = state.get("location")
    modes = [str(mode).casefold() for mode in context.modes]
    mode = state.get("workplace_type") or (
        "remote" if "remote" in modes else None
    )
    # A remote preference is worldwide unless the member explicitly enters a
    # location in this request. Do not silently constrain it to their home city.
    if location is None and mode != "remote":
        location = context.location
    remote_location = (location or "").strip().casefold() == "remote"
    mode = mode or ("remote" if remote_location else None)
    # Remote is a work mode, not a geographic location supported by SerpApi.
    return {
        "criteria": JobSearchCriteria(
            query=query,
            location=None if remote_location else location or None,
            workplace_type=mode,
            employment_type=state.get("employment_type") or None,
            limit=50,
        )
    }


async def recommendation_fetch(state, config):
    service = config["configurable"]["job_service"]
    result = await service.search(state["criteria"])
    # Some providers do not consistently classify remote listings. Keep the
    # member's remote preference for the first pass, then broaden only when it
    # would otherwise leave the recommendations empty.
    if not result.jobs and state["criteria"].workplace_type:
        broadened = state["criteria"].model_copy(update={"workplace_type": None})
        result = await service.search(broadened)
        if result.jobs:
            result.message = "No exact work-arrangement matches were found; showing relevant open roles."
    return {"result": result}


async def recommendation_rank(state):
    from app.services.job_recommendations import rank_jobs

    result = state["result"].model_copy(deep=True)
    result.jobs = rank_jobs(result.jobs, state["context"])
    result.result_count = len(result.jobs)
    return {"result": result}


recommendations = StateGraph(RecommendationState)
recommendations.add_node("load_career_context", recommendation_context)
recommendations.add_node("resolve_preferences", recommendation_criteria)
recommendations.add_node("fetch_real_jobs", recommendation_fetch)
recommendations.add_node("rank_with_evidence", recommendation_rank)
recommendations.add_edge(START, "load_career_context")
recommendations.add_edge("load_career_context", "resolve_preferences")
recommendations.add_edge("resolve_preferences", "fetch_real_jobs")
recommendations.add_edge("fetch_real_jobs", "rank_with_evidence")
recommendations.add_edge("rank_with_evidence", END)
recommendation_graph = recommendations.compile()
