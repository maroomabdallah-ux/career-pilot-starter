from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.resume.service import ResumeWritingService, merge_writing


class ResumeState(TypedDict, total=False):
    verified: dict[str, Any]
    existing: dict[str, Any]
    section: str
    rag: list[str]
    content: dict[str, Any]
    error: str


async def evaluate_readiness(state: ResumeState):
    source = state["verified"]
    if not (source.get("experience") or source.get("projects") or source.get("skills")):
        return {"error": "Add experience, projects, or skills before creating a resume."}
    return {}


def route_readiness(state: ResumeState):
    return END if state.get("error") else "generate_writing"


async def generate_writing(state: ResumeState):
    writing = await ResumeWritingService().generate(
        state["verified"], state.get("section", "all"), state.get("rag")
    )
    base = state.get("existing") or state["verified"]
    return {"content": merge_writing(base, writing, state.get("section", "all"))}


def build_resume_graph():
    graph = StateGraph(ResumeState)
    graph.add_node("evaluate_readiness", evaluate_readiness)
    graph.add_node("generate_writing", generate_writing)
    graph.add_edge(START, "evaluate_readiness")
    graph.add_conditional_edges("evaluate_readiness", route_readiness)
    graph.add_edge("generate_writing", END)
    return graph.compile()


resume_graph = build_resume_graph()
