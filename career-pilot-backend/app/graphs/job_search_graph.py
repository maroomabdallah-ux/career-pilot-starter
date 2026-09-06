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


async def understand(state, _config):
    if state.get("supplied_criteria"):
        return {"extracted": state["supplied_criteria"]}
    return {"extracted": understand_job_search(state.get("prompt", ""))}


async def load_profile(state, config):
    extracted = state["extracted"]
    if extracted.get("query") and (extracted.get("location") or extracted.get("workplace_type")):
        return {}
    client = config["configurable"]["mcp_client"]
    async with client.read_session() as mcp:
        profile = await mcp.get_profile()
        skills = await mcp.get_skills()
    return {"profile": profile, "skills": skills}


async def resolve(state, _config):
    values = dict(state["extracted"])
    profile = state.get("profile", {})
    skills = state.get("skills", [])
    values["query"] = (
        values.get("query")
        or (profile.get("target_roles") or [None])[0]
        or profile.get("professional_title")
    )
    modes = [str(x).casefold() for x in profile.get("preferred_work_modes", [])]
    if not values.get("workplace_type"):
        values["workplace_type"] = next(
            (x for x in ("remote", "hybrid", "on-site") if x in modes), None
        )
    values["location"] = values.get("location") or (profile.get("preferred_locations") or [None])[0]
    values["skills"] = [item["name"] for item in skills[:10]]
    if not values.get("query"):
        return {"clarification": "What job title or career field would you like me to search for?"}
    if not values.get("location") and not values.get("workplace_type"):
        return {"clarification": "Do you want jobs in a specific location, remote jobs, or both?"}
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
