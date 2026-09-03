import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.resume.service import (
    ResumeWritingService,
    SemanticFactValidationService,
    merge_writing,
    quality_issues,
    validate_fixed_facts,
)
from app.services.resume_intelligence import analyze_section

logger = logging.getLogger(__name__)


class ResumeGenerationStageError(RuntimeError):
    def __init__(self, stage: str):
        super().__init__(f"Resume generation failed during {stage}")
        self.stage = stage


async def _stage(name: str, operation: Callable[[], Awaitable[dict]]) -> dict:
    logger.info("Resume generation stage started", extra={"stage": name})
    try:
        result = await operation()
    except Exception as exc:
        logger.exception("Resume generation stage failed", extra={"stage": name})
        raise ResumeGenerationStageError(name) from exc
    logger.info("Resume generation stage completed", extra={"stage": name})
    return result


class ResumeState(TypedDict, total=False):
    verified: dict[str, Any]
    existing: dict[str, Any]
    section: str
    rag: list[str]
    content: dict[str, Any]
    error: str
    plan: dict[str, Any]
    quality_warnings: list[str]


async def evaluate_readiness(state: ResumeState):
    source = state["verified"]
    if not (source.get("experience") or source.get("projects") or source.get("skills")):
        return {"error": "Add experience, projects, or skills before creating a resume."}
    return {}


async def plan_resume(state: ResumeState):
    source = state["verified"]
    return {
        "plan": {
            "section_order": source.get("section_order", []),
            "experience_count": len(source.get("experience", [])),
            "education_count": len(source.get("education", [])),
            "project_count": len(source.get("projects", [])),
            "include_summary": True,
        }
    }


def route_readiness(state: ResumeState):
    return END if state.get("error") else "plan_resume"


async def generate_writing(state: ResumeState):
    async def operation():
        writing = await ResumeWritingService().generate(
            state["verified"], state.get("section", "all"), state.get("rag")
        )
        base = state.get("existing") or state["verified"]
        return {"content": merge_writing(base, writing, state.get("section", "all"))}

    return await _stage("generate_writing", operation)


async def fact_validation(state: ResumeState):
    async def operation():
        errors = validate_fixed_facts(state["verified"], state["content"])
        if not errors:
            semantic = await SemanticFactValidationService().validate(
                state["verified"], state["content"], state.get("rag")
            )
            errors.extend(semantic.unsupported_claims if not semantic.valid else [])
        if errors:
            return {"error": "Resume fact validation failed: " + "; ".join(errors[:4])}
        return {}

    return await _stage("fact_validation", operation)


async def quality_validation(state: ResumeState):
    content = {**state["content"]}
    from app.services.resume_intelligence import analyze_resume

    report = analyze_resume(content, state["verified"], state.get("rag", []))
    smart_flags = []
    for item in report.analyses:
        if item.quality in {"insufficient_information", "weak", "needs_improvement"}:
            label = item.section.title() + (f" {item.item_index + 1}" if item.item_index is not None else "")
            detail = item.issues[0].message if item.issues else item.missing_information[0]
            smart_flags.append(f"{label}: {detail}")
    content["review_flags"] = (quality_issues(content) + smart_flags)[:3]
    return {"content": content, "quality_warnings": content["review_flags"]}


def build_resume_graph():
    graph = StateGraph(ResumeState)
    graph.add_node("evaluate_readiness", evaluate_readiness)
    graph.add_node("plan_resume", plan_resume)
    graph.add_node("generate_writing", generate_writing)
    graph.add_node("fact_validation", fact_validation)
    graph.add_node("quality_validation", quality_validation)
    graph.add_edge(START, "evaluate_readiness")
    graph.add_conditional_edges("evaluate_readiness", route_readiness)
    graph.add_edge("plan_resume", "generate_writing")
    graph.add_edge("generate_writing", "fact_validation")
    graph.add_conditional_edges(
        "fact_validation", lambda state: END if state.get("error") else "quality_validation"
    )
    graph.add_edge("quality_validation", END)
    return graph.compile()


resume_graph = build_resume_graph()


class ResumeCopilotState(TypedDict, total=False):
    content: dict[str, Any]
    verified: dict[str, Any]
    rag: list[str]
    selection: dict[str, Any]
    message: str
    user_answer: str
    language: str
    intent: str
    analysis: Any
    relevant_context: list[str]


async def understand_resume_request(state: ResumeCopilotState):
    message = state.get("message", "").casefold()
    intent = "analyze"
    if any(x in message for x in ("strong", "improve", "حسن", "احسن", "technical", "تقني")):
        intent = "strengthen"
    elif any(x in message for x in ("short", "concise", "اختصر")):
        intent = "shorten"
    elif any(x in message for x in ("missing", "ناقص", "اضيف", "add")):
        intent = "missing_detail"
    return {"intent": intent, "language": "ar" if re.search(r"[\u0600-\u06ff]", message) else "en"}


async def evaluate_information_quality(state: ResumeCopilotState):
    selected = state["selection"]
    analysis = analyze_section(state["content"], state["verified"], selected["section"], selected.get("item_index"), state.get("rag", []), state.get("language", "en"))
    return {"analysis": analysis, "relevant_context": [s.suggestion for s in analysis.supported_suggestions if s.type == "add_existing_fact" and s.suggestion]}


def build_resume_copilot_graph():
    graph = StateGraph(ResumeCopilotState)
    graph.add_node("understand_resume_request", understand_resume_request)
    graph.add_node("evaluate_information_quality", evaluate_information_quality)
    graph.add_edge(START, "understand_resume_request")
    graph.add_edge("understand_resume_request", "evaluate_information_quality")
    graph.add_edge("evaluate_information_quality", END)
    return graph.compile()


resume_copilot_graph = build_resume_copilot_graph()
