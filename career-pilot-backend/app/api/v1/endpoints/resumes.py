import logging
import asyncio
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import JSONResponse

from app.api.dependencies import CurrentUser, SessionDep
from app.graphs.resume_graph import ResumeGenerationStageError, resume_copilot_graph, resume_graph
from app.schemas.resume import (ResumeAnalysisResponse, ResumeCoachRequest, ResumeCoachResponse,
    ResumeEvidence, ResumeGenerate, ResumeRegenerate, ResumeResponse, ResumeSuggestion,
    ResumeSuggestionApply, ResumeUpdate)
from app.agents.resume.service import ResumeWritingService
from app.services.resume import ResumeService
from app.services.resume_context import ResumeContextBuilder
from app.services.resume_intelligence import analyze_resume, apply_suggestion, validate_suggestion
from app.services.resume_pdf import PDFRendererUnavailable, render_resume_pdf
from app.services.resume_templates import TEMPLATES, TemplateAccessService

router = APIRouter()
logger = logging.getLogger(__name__)


def generation_error(stage: str):
    return {
        "error": {
            "code": "resume_generation_failed",
            "stage": stage,
            "message": "CareerPilot could not generate the resume safely.",
        }
    }


def service(session, user):
    return ResumeService(session, user.id)


@router.get("/templates")
async def list_templates():
    return list(TEMPLATES.values())


@router.get("/readiness")
async def resume_readiness(session: SessionDep, user: CurrentUser):
    return (await ResumeContextBuilder(session, user).build(with_rag=False)).readiness


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(session: SessionDep, user: CurrentUser):
    return await service(session, user).list()


@router.post("/generate", response_model=ResumeResponse, status_code=201)
async def generate(data: ResumeGenerate, session: SessionDep, user: CurrentUser):
    try:
        context = await ResumeContextBuilder(session, user).build(data.include_projects)
    except Exception:
        logger.exception(
            "Resume generation failed",
            extra={"user_id": str(user.id), "stage": "load_context"},
        )
        return JSONResponse(status_code=502, content=generation_error("load_context"))
    if not context.readiness["ready"]:
        raise HTTPException(
            422, {"message": "Your profile needs more information.", **context.readiness}
        )
    try:
        result = await resume_graph.ainvoke(
            {"verified": context.verified, "section": "all", "rag": context.supporting_rag}
        )
    except ResumeGenerationStageError as exc:
        logger.exception(
            "Resume generation failed",
            extra={"user_id": str(user.id), "stage": exc.stage},
        )
        return JSONResponse(status_code=502, content=generation_error(exc.stage))
    except Exception:
        logger.exception(
            "Resume generation failed",
            extra={"user_id": str(user.id), "stage": "workflow"},
        )
        return JSONResponse(status_code=502, content=generation_error("workflow"))
    if result.get("error"):
        raise HTTPException(422, result["error"])
    try:
        return await service(session, user).create(
            data.title, data.language, result["content"], data.template_id
        )
    except Exception:
        logger.exception(
            "Resume generation failed",
            extra={"user_id": str(user.id), "stage": "save_draft"},
        )
        return JSONResponse(status_code=502, content=generation_error("save_draft"))


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: UUID, session: SessionDep, user: CurrentUser):
    try:
        return await service(session, user).get(resume_id)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/{resume_id}/duplicate", response_model=ResumeResponse, status_code=201)
async def duplicate_resume(resume_id: UUID, session: SessionDep, user: CurrentUser):
    resume_service = service(session, user)
    try:
        source = await resume_service.get(resume_id)
        return await resume_service.create(
            f"{source.title} Copy", source.language, source.content, source.template_id
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.patch("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: UUID, data: ResumeUpdate, session: SessionDep, user: CurrentUser
):
    try:
        return await service(session, user).update(resume_id, data)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/{resume_id}/approve", response_model=ResumeResponse)
async def approve_resume(resume_id: UUID, session: SessionDep, user: CurrentUser):
    try:
        return await service(session, user).transition(resume_id, "approved")
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/{resume_id}/regenerate-section", response_model=ResumeResponse)
async def regenerate_section(
    resume_id: UUID, data: ResumeRegenerate, session: SessionDep, user: CurrentUser
):
    resume_service = service(session, user)
    try:
        resume = await resume_service.get(resume_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    if resume.status == "approved":
        raise HTTPException(409, "Approved resumes cannot be regenerated. Create a new version.")
    context = await ResumeContextBuilder(session, user).build()
    try:
        result = await resume_graph.ainvoke(
            {
                "verified": context.verified,
                "existing": resume.content,
                "section": data.section.value,
                "rag": context.supporting_rag,
            }
        )
    except Exception as exc:
        raise HTTPException(502, "CareerPilot could not regenerate this section safely.") from exc
    if result.get("error"):
        raise HTTPException(422, result["error"])
    return await resume_service.update(resume_id, ResumeUpdate(content=result["content"]))


@router.get("/{resume_id}/analysis", response_model=ResumeAnalysisResponse)
async def analyze(resume_id: UUID, session: SessionDep, user: CurrentUser):
    resume = await service(session, user).get(resume_id)
    context = await ResumeContextBuilder(session, user).build()
    return analyze_resume(resume.content, context.verified, context.supporting_rag)


@router.post("/{resume_id}/copilot", response_model=ResumeCoachResponse)
async def coach(resume_id: UUID, data: ResumeCoachRequest, session: SessionDep, user: CurrentUser):
    resume = await service(session, user).get(resume_id)
    context = await ResumeContextBuilder(session, user).build()
    result = await resume_copilot_graph.ainvoke({"content": resume.content,
        "verified": context.verified, "rag": context.supporting_rag,
        "selection": data.selection.model_dump(), "message": data.message,
        "user_answer": data.user_answer or ""})
    analysis = result["analysis"]
    message = data.message.casefold()
    write_requested = bool(data.user_answer) or any(token in message for token in (
        "generate", "write", "improve", "rewrite", "short", "concise", "technical",
        "professional", "bullet", "حسن", "اكتب", "اختصر", "تقني", "نقاط",
    ))
    if write_requested and (not analysis.missing_information or data.user_answer):
        verified = dict(context.verified)
        if data.user_answer:
            verified["resume_user_answer"] = data.user_answer.strip()
        section = data.selection.section
        prompts = [section]
        if section == "summary":
            prompts = [
                "summary; professional version",
                "summary; technical version",
                "summary; concise version",
            ]
        try:
            writings = await asyncio.gather(*(
                ResumeWritingService().generate(verified, prompt, context.supporting_rag)
                for prompt in prompts
            ))
        except Exception as exc:
            logger.exception("Resume suggestion generation failed", extra={"resume_id": str(resume_id)})
            raise HTTPException(502, "CareerPilot could not create grounded suggestions right now.") from exc
        evidence = [ResumeEvidence(source_type="profile", domain=section, excerpt="Verified Career Profile")]
        if data.user_answer:
            evidence.append(ResumeEvidence(source_type="user_answer", domain=section, excerpt=data.user_answer.strip()))
        generated = []
        if section == "summary":
            for label, writing in zip(("Professional", "Technical", "Concise"), writings, strict=True):
                if writing.summary:
                    generated.append((label, writing.summary, "rewrite"))
        elif section == "experience":
            index = data.selection.item_index or 0
            for item in writings[0].experience:
                if item.index == index:
                    generated.extend(("Suggested bullet", bullet, "strengthen") for bullet in item.bullets)
        elif section == "projects":
            index = data.selection.item_index or 0
            for item in writings[0].projects:
                if item.index == index and item.description:
                    generated.append(("Improved description", item.description, "rewrite"))
        elif section == "skills":
            current = {skill.casefold() for group in resume.content.get("skill_groups", []) for skill in group.get("items", [])}
            for group in writings[0].skill_groups.values():
                generated.extend(("Verified missing skill", skill, "add_existing_fact") for skill in group if skill.casefold() not in current)
        for label, text, suggestion_type in reversed(generated[:3]):
            analysis.supported_suggestions.insert(0, ResumeSuggestion(
                id=str(uuid4()), section=section, item_index=data.selection.item_index,
                bullet_index=data.selection.bullet_index, type=suggestion_type, label=label,
                reason="Written from verified Career Profile information and relevant saved context.",
                suggestion=text, evidence=evidence, requires_confirmation=False,
            ))
    return ResumeCoachResponse(selection=data.selection, analysis=analysis,
        detected_intent=result["intent"], response_language=result["language"],
        relevant_context=result.get("relevant_context", []), profile_update_requires_approval=bool(data.user_answer))


@router.post("/{resume_id}/suggestions/apply", response_model=ResumeResponse)
async def accept_suggestion(resume_id: UUID, data: ResumeSuggestionApply, session: SessionDep, user: CurrentUser):
    resume_service = service(session, user)
    resume = await resume_service.get(resume_id)
    if resume.status == "approved":
        raise HTTPException(409, "Approved resumes are immutable. Create a new version.")
    context = await ResumeContextBuilder(session, user).build()
    candidate = data.suggestion.model_copy(update={"suggestion": data.edited_text or data.suggestion.suggestion})
    errors = validate_suggestion(candidate, context.verified, context.supporting_rag,
        "confirmed" if data.confirmed else (data.edited_text if any(e.source_type == "user_answer" for e in candidate.evidence) else None))
    if errors:
        raise HTTPException(422, {"message": "Suggestion validation failed.", "issues": errors})
    updated = apply_suggestion(resume.content, candidate, data.edited_text)
    return await resume_service.update(resume_id, ResumeUpdate(content=updated))


@router.post("/{resume_id}/export")
async def export_resume(resume_id: UUID, session: SessionDep, user: CurrentUser):
    try:
        resume = await service(session, user).get(resume_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    if not TemplateAccessService().can_export(resume.template_id, user):
        raise HTTPException(403, "This premium template requires an eligible plan for PDF export.")
    try:
        pdf = await render_resume_pdf(resume.content, resume.template_id)
    except PDFRendererUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    filename = (
        "".join(c if c.isalnum() or c in "-_" else "-" for c in resume.title).strip("-") or "resume"
    )
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )


@router.post("/{resume_id}/review", response_model=ResumeResponse)
async def review_resume(resume_id: UUID, session: SessionDep, user: CurrentUser):
    try:
        return await service(session, user).transition(resume_id, "review")
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/{resume_id}/archive", response_model=ResumeResponse)
async def archive_resume(resume_id: UUID, session: SessionDep, user: CurrentUser):
    try:
        return await service(session, user).transition(resume_id, "archived")
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(resume_id: UUID, session: SessionDep, user: CurrentUser):
    try:
        await service(session, user).delete(resume_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
