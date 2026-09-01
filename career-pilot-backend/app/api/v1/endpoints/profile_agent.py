import logging
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from langgraph.types import Command
from langchain_openai.chat_models.base import (
    OpenAIAuthenticationError,
    OpenAIConnectionError,
    OpenAIModelNotFoundError,
    OpenAIRateLimitError,
    OpenAITimeoutError,
)
from pydantic import ValidationError
from app.agents.profile.schemas import AgentResponse, ApprovalRequest, ChatRequest, ProfileIntent, Proposal
from app.agents.profile.service import ProfileAgentConfigurationError, ProfileUnderstandingService, language_message
from app.api.dependencies import CurrentUser, SessionDep
from app.core.config import settings
from app.graphs.profile_graph import profile_graph
from app.schemas.career_profile import CareerProfileUpdate
from app.schemas.education import EducationCreate, EducationUpdate
from app.schemas.experience import ExperienceCreate, ExperienceUpdate
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.skill import SkillCreate
from app.services.me import MeService

router = APIRouter()
logger = logging.getLogger(__name__)
WRITE = {ProfileIntent.ADD_PROFILE_INFORMATION:("profile","update"),ProfileIntent.UPDATE_PROFILE_INFORMATION:("profile","update"),ProfileIntent.ADD_EDUCATION:("education","create"),ProfileIntent.UPDATE_EDUCATION:("education","update"),ProfileIntent.DELETE_EDUCATION:("education","delete"),ProfileIntent.ADD_EXPERIENCE:("experience","create"),ProfileIntent.UPDATE_EXPERIENCE:("experience","update"),ProfileIntent.DELETE_EXPERIENCE:("experience","delete"),ProfileIntent.ADD_PROJECT:("project","create"),ProfileIntent.UPDATE_PROJECT:("project","update"),ProfileIntent.DELETE_PROJECT:("project","delete"),ProfileIntent.ADD_SKILL:("skill","create"),ProfileIntent.DELETE_SKILL:("skill","delete")}
READ = {ProfileIntent.READ_PROFILE:("experiences","education","projects","skills"),ProfileIntent.READ_SKILLS:("skills",),ProfileIntent.READ_EDUCATION:("education",),ProfileIntent.READ_EXPERIENCE:("experiences",),ProfileIntent.READ_PROJECTS:("projects",)}

def config(thread_id, user, session):
    return {"configurable":{"thread_id":thread_id,"services":{"session":session,"me":MeService(session,user)}}}
def label(domain): return {"skill":"name","education":"institution","experience":"company","project":"name"}[domain]
def records(profile, domain): return {"skill":profile.skills,"education":profile.education,"experience":profile.experiences,"project":profile.projects}[domain]

def validate(domain, operation, fields):
    schemas={"profile":(CareerProfileUpdate,CareerProfileUpdate),"education":(EducationCreate,EducationUpdate),"experience":(ExperienceCreate,ExperienceUpdate),"project":(ProjectCreate,ProjectUpdate)}
    if domain == "skill":
        names=fields.get("names") or ([fields["name"]] if fields.get("name") else [])
        if operation == "create" and names:
            for name in names: SkillCreate(name=name)
            return {"names":names}
        raise ValueError("a skill name is required")
    create, update=schemas[domain]
    if operation == "create": return create(**fields).model_dump(mode="json")
    changes=fields.get("changes",fields)
    return {"changes":update(**changes).model_dump(exclude_unset=True,mode="json")}

async def make_proposal(intent, me):
    domain, operation=WRITE[intent.intent]
    if intent.missing_required_fields: return None, "Please provide: "+", ".join(intent.missing_required_fields)+"."
    fields=dict(intent.fields)
    if domain != "profile" and operation in {"update","delete"}:
        target=fields.get("target",fields); name=str(target.get(label(domain),target.get("name",""))).strip()
        if not name: return None, f"Which {domain} should I {operation}?"
        matches=[item for item in records(await me.profile(),domain) if str(getattr(item,label(domain))).strip().casefold()==name.casefold()]
        if not matches: return None, f"I couldn't find {name} in your {domain} records."
        if len(matches)>1: return None, f"I found multiple {domain} records named {name}. Please tell me which one you mean."
        fields={"id":str(matches[0].id),label(domain):getattr(matches[0],label(domain)),**({"changes":fields.get("changes",{})} if operation=="update" else {})}
    if domain == "skill" and operation == "create":
        names=fields.get("names") or ([fields["name"]] if fields.get("name") else [])
        duplicate=[name for name in names if any(s.name.casefold()==str(name).strip().casefold() for s in (await me.profile()).skills)]
        if duplicate: return None, f"{', '.join(duplicate)} already exist in your Skills section."
    try:
        if operation != "delete":
            checked=validate(domain,operation,fields)
            fields={**fields,**checked} if operation=="update" else checked
    except (ValidationError,ValueError) as exc: return None, f"Please provide valid {domain} details: {exc}."
    return {"operation":operation,"domain":domain,"fields":fields},None

@router.post("/chat",response_model=AgentResponse)
async def chat(data:ChatRequest,session:SessionDep,user:CurrentUser):
    thread_id=data.thread_id or str(uuid4())
    try:
        intent=await ProfileUnderstandingService().understand(data.message)
        logger.info("profile-agent request thread=%s intent=%s",thread_id,intent.intent)
    except ProfileAgentConfigurationError as exc: raise HTTPException(503,str(exc)) from exc
    except OpenAIAuthenticationError as exc:
        raise HTTPException(503, "CareerPilot AI could not authenticate with OpenAI. Check OPENAI_API_KEY.") from exc
    except OpenAIModelNotFoundError as exc:
        raise HTTPException(503, "CareerPilot AI model is unavailable. Check PROFILE_AGENT_MODEL.") from exc
    except OpenAIRateLimitError as exc:
        raise HTTPException(429, "CareerPilot AI is temporarily rate-limited. Please try again shortly.") from exc
    except (OpenAIConnectionError, OpenAITimeoutError) as exc:
        raise HTTPException(503, "CareerPilot AI cannot reach OpenAI. Check this server's internet/DNS connection.") from exc
    except Exception as exc:
        logger.exception("profile-agent understanding failed thread=%s",thread_id)
        detail = "CareerPilot AI could not process that request. Your profile was not modified."
        if settings.ENVIRONMENT == "development":
            detail = f"{detail} Diagnostic: {type(exc).__name__}."
        raise HTTPException(502, detail) from exc
    if intent.intent == ProfileIntent.GREETING:
        return AgentResponse(
            type="message",
            thread_id=thread_id,
            message=language_message(
                data.message,
                "Hi! I can help you review, improve, or update your career profile. What would you like to work on?",
                "أهلًا! بقدر أساعدك تراجع بروفايلك، تضيف خبرة أو مهارات، أو نشوف شو ناقص فيه. شو حاب نشتغل عليه؟",
            ),
        )
    if intent.intent == ProfileIntent.GENERAL_CONVERSATION:
        return AgentResponse(
            type="message",
            thread_id=thread_id,
            message=language_message(
                data.message,
                "I can review your profile, list saved details, suggest what to complete, or prepare approved changes to your skills, education, experience, and projects.",
                "بقدر أراجع بروفايلك، أعرض معلوماتك المحفوظة، أقترح شو ناقص، أو أجهّز تغييرات للمهارات والتعليم والخبرة والمشاريع بعد موافقتك.",
            ),
        )
    me=MeService(session,user)
    if intent.intent in READ:
        profile=await me.profile(); parts=[]
        for field in READ[intent.intent]:
            values=getattr(profile,field)
            names=", ".join(str(getattr(x,"name",getattr(x,"company",getattr(x,"institution","item")))) for x in values)
            parts.append((field.replace("experiences", "experience").replace("education", "education")+": "+names) if names else "no entries")
        if intent.intent == ProfileIntent.READ_SKILLS:
            english="Your current skills are " + (", ".join(s.name for s in profile.skills) or "not added yet") + "."
            arabic="مهاراتك الحالية هي: " + ("، ".join(s.name for s in profile.skills) or "لم تضف مهارات بعد") + "."
        else:
            english="Here’s what I found in your saved profile: " + "; ".join(parts) + "."
            arabic="هذا ما وجدته في بروفايلك المحفوظ: " + "؛ ".join(parts) + "."
        return AgentResponse(type="message",thread_id=thread_id,message=language_message(data.message,english,arabic))
    if intent.intent in {ProfileIntent.PROFILE_COMPLETENESS,ProfileIntent.PROFILE_GAPS,ProfileIntent.NEXT_BEST_ACTION}:
        p=await me.profile(); missing=[name for name,present in (("professional title",p.professional_title),("education",p.education),("experience",p.experiences),("skills",p.skills)) if not present]
        english="Your profile has the core sections filled in." if not missing else "The next profile sections to add are: "+", ".join(missing)+"."
        arabic="الأقسام الأساسية في بروفايلك مكتملة." if not missing else "الأقسام الناقصة التالية في بروفايلك: "+", ".join(missing)+"."
        return AgentResponse(type="message",thread_id=thread_id,message=language_message(data.message,english,arabic))
    if intent.intent in WRITE:
        proposal,problem=await make_proposal(intent,me)
        if problem: return AgentResponse(type="clarification" if intent.missing_required_fields else "message",thread_id=thread_id,message=problem)
        result=await profile_graph.ainvoke({"user_id":str(user.id),"proposal":proposal},config=config(thread_id,user,session))
        return AgentResponse(type="proposal",message=language_message(data.message,"Please review the proposed change before saving.","راجع التغيير المقترح قبل الحفظ."),thread_id=thread_id,proposal=Proposal(**result["__interrupt__"][0].value),requires_approval=True)
    return AgentResponse(type="clarification",thread_id=thread_id,message=language_message(data.message,"I need a little more detail about what you want to read or change in your profile.","بدي تفاصيل أكثر شوي عن المعلومات اللي بدك تقرأها أو تعدلها في بروفايلك."))

@router.post("/approve",response_model=AgentResponse)
async def approve(data:ApprovalRequest,session:SessionDep,user:CurrentUser):
    graph_config=config(data.thread_id,user,session); snapshot=await profile_graph.aget_state(graph_config)
    if not snapshot.values: raise HTTPException(404,"Pending proposal not found or expired")
    if snapshot.values.get("user_id")!=str(user.id): raise HTTPException(403,"You cannot approve another user's proposal")
    if snapshot.values.get("result"): raise HTTPException(409,"This proposal has already been decided")
    try:
        result=await profile_graph.ainvoke(Command(resume=data.decision),config=graph_config)
        return AgentResponse(type="result",thread_id=data.thread_id,message=result["result"]["message"])
    except Exception as exc:
        logger.exception("profile-agent write failed thread=%s",data.thread_id)
        raise HTTPException(500,"I couldn't complete that profile change. Your profile was not modified.") from exc
