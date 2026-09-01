from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.api.dependencies import CurrentUser, SessionDep
from app.graphs.resume_graph import resume_graph
from app.schemas.resume import ResumeGenerate, ResumeRegenerate, ResumeResponse, ResumeUpdate
from app.services.me import MeService
from app.services.resume import ResumeService

router = APIRouter()


def service(session, user):
    return ResumeService(session, user.id)


def serialize_date(value):
    return value.isoformat() if value else None


def build_content(user, profile, include_projects):
    """Deterministic draft: only canonical profile values, never fabricated facts."""
    return {
        "header": {
            "name": f"{user.first_name} {user.last_name}".strip(),
            "email": user.email,
            "title": profile.professional_title,
            "city": profile.city,
            "country": profile.country,
            "phone": profile.phone,
            "linkedin_url": str(profile.linkedin_url) if profile.linkedin_url else None,
            "github_url": str(profile.github_url) if profile.github_url else None,
            "portfolio_url": str(profile.portfolio_url) if profile.portfolio_url else None,
        },
        "summary": profile.professional_summary,
        "experience": [
            {
                "company": x.company,
                "job_title": x.job_title,
                "location": x.location,
                "start_date": serialize_date(x.start_date),
                "end_date": serialize_date(x.end_date),
                "is_current": x.is_current,
                "bullets": [x.description] if x.description else [],
                "technologies": x.technologies,
            }
            for x in profile.experiences
        ],
        "education": [
            {
                "institution": x.institution,
                "degree": x.degree,
                "field_of_study": x.field_of_study,
                "start_date": serialize_date(x.start_date),
                "end_date": serialize_date(x.end_date),
                "grade": x.grade,
                "grade_system": x.grade_system,
                "description": x.description,
            }
            for x in profile.education
        ],
        "projects": [
            {
                "name": x.name,
                "role": x.role,
                "description": x.description,
                "technologies": x.technologies,
                "project_url": str(x.project_url) if x.project_url else None,
                "repository_url": str(x.repository_url) if x.repository_url else None,
            }
            for x in profile.projects
        ]
        if include_projects
        else [],
        "skills": [x.name for x in profile.skills],
    }


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(session: SessionDep, user: CurrentUser):
    return await service(session, user).list()


@router.post("/generate", response_model=ResumeResponse, status_code=201)
async def generate(data: ResumeGenerate, session: SessionDep, user: CurrentUser):
    profile = await MeService(session, user).profile()
    verified = build_content(user, profile, data.include_projects)
    try:
        result = await resume_graph.ainvoke({"verified": verified, "section": "all", "rag": []})
    except Exception as exc:
        raise HTTPException(502, "CareerPilot could not generate the resume safely.") from exc
    if result.get("error"):
        raise HTTPException(422, result["error"])
    return await service(session, user).create(data.title, data.language, result["content"])


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: UUID, session: SessionDep, user: CurrentUser):
    try:
        return await service(session, user).get(resume_id)
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
    profile = await MeService(session, user).profile()
    verified = build_content(user, profile, True)
    try:
        result = await resume_graph.ainvoke(
            {
                "verified": verified,
                "existing": resume.content,
                "section": data.section.value,
                "rag": [],
            }
        )
    except Exception as exc:
        raise HTTPException(502, "CareerPilot could not regenerate this section safely.") from exc
    return await resume_service.update(resume_id, ResumeUpdate(content=result["content"]))


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
