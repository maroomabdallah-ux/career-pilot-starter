from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt


class ProfileAgentState(TypedDict, total=False):
    user_id: str
    proposal: dict[str, Any]
    result: dict[str, Any]


async def request_approval(state: ProfileAgentState):
    decision = interrupt(state["proposal"])
    if decision != "approve":
        return {"result": {"message": "The proposed change was discarded."}}
    return {}


async def execute_write(state: ProfileAgentState, config: RunnableConfig):
    client = config["configurable"]["mcp_client"]
    proposal = state["proposal"]
    domain, operation, fields = proposal["domain"], proposal["operation"], proposal["fields"]
    async with client.read_session() as mcp:
        if domain == "profile":
            result = await mcp.update_profile(fields)
        elif domain == "skill" and operation == "create":
            results = [await mcp.add_skill({"name": name}) for name in fields["names"]]
            labels = ", ".join(item["label"] for item in results)
            return {"result": {"message": f"Added {labels} to your Skills."}}
        elif domain == "skill" and operation == "update":
            result = await mcp.update_skill(fields["id"], fields["changes"])
        elif domain == "skill" and operation == "delete":
            result = await mcp.delete_skill(fields["id"])
        elif operation == "create":
            result = await mcp.add_profile_child(domain, fields)
        elif operation == "update":
            result = await mcp.update_profile_child(domain, fields["id"], fields["changes"])
        else:
            result = await mcp.delete_profile_child(domain, fields["id"])
    action = {"create": "Added", "update": "Updated", "delete": "Removed"}[operation]
    return {"result": {"message": f"{action} {result['label']} in your profile."}}


def after_approval(state: ProfileAgentState):
    return END if state.get("result") else "execute_write"


def build_profile_graph():
    graph = StateGraph(ProfileAgentState)
    graph.add_node("request_approval", request_approval)
    graph.add_node("execute_write", execute_write)
    graph.add_edge(START, "request_approval")
    graph.add_conditional_edges("request_approval", after_approval)
    graph.add_edge("execute_write", END)
    return graph.compile(checkpointer=MemorySaver())


profile_graph = build_profile_graph()
