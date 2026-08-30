from langgraph.graph import END, START, StateGraph

from app.agents.state import CareerState


def starter_node(state: CareerState) -> CareerState:
    return {
        **state,
        "current_step": "starter",
        "result": {"message": "CareerPilot LangGraph starter is ready."},
    }


def build_career_graph():
    graph = StateGraph(CareerState)
    graph.add_node("starter", starter_node)
    graph.add_edge(START, "starter")
    graph.add_edge("starter", END)
    return graph.compile()


career_graph = build_career_graph()
