from typing import Any, TypedDict
from uuid import UUID

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from app.schemas.career_profile import CareerProfileUpdate
from app.schemas.education import EducationCreate, EducationUpdate
from app.schemas.experience import ExperienceCreate, ExperienceUpdate
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.skill import SkillCreate
from app.services.education import EducationService
from app.services.experience import ExperienceService
from app.services.project import ProjectService
from app.services.skill import SkillService

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
    services = config["configurable"]["services"]
    me, session, proposal = services["me"], services["session"], state["proposal"]
    domain, operation, fields = proposal["domain"], proposal["operation"], proposal["fields"]
    if domain == "profile":
        await me.update_profile(CareerProfileUpdate(**fields))
        return {"result": {"message": "Your profile basics were updated."}}
    if domain == "skill":
        if proposal["operation"] == "delete":
            await me.delete_child(
                SkillService(session), "get_skill", "delete_skill", UUID(proposal["fields"]["id"])
            )
            return {"result": {"message": f"Removed {proposal['fields']['name']} from your skills."}}
        for name in proposal["fields"]["names"]:
            await me.create_child(SkillService(session), "create_skill", SkillCreate(name=name))
        return {"result": {"message": f"Added {len(proposal['fields']['names'])} skill(s) to your profile."}}
    definitions = {
        "education": (EducationService, "get_education", "create_education", "update_education", "delete_education", EducationCreate, EducationUpdate, "institution"),
        "experience": (ExperienceService, "get_experience", "create_experience", "update_experience", "delete_experience", ExperienceCreate, ExperienceUpdate, "company"),
        "project": (ProjectService, "get_project", "create_project", "update_project", "delete_project", ProjectCreate, ProjectUpdate, "name"),
    }
    service_type, get_method, create_method, update_method, delete_method, create_schema, update_schema, label = definitions[domain]
    service = service_type(session)
    if operation == "delete":
        await me.delete_child(service, get_method, delete_method, UUID(fields["id"]))
        return {"result": {"message": f"Removed {fields.get(label, domain)} from your profile."}}
    if operation == "update":
        item = await me.update_child(
            service, get_method, update_method, UUID(fields["id"]), update_schema(**fields["changes"])
        )
        return {"result": {"message": f"Updated {getattr(item, label)}."}}
    item = await me.create_child(service, create_method, create_schema(**fields))
    return {"result": {"message": f"Added {getattr(item, label)} to your profile."}}

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
