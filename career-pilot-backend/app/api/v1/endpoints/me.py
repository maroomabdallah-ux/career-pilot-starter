from uuid import UUID

from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, SessionDep
from app.schemas.career_profile import CareerProfileResponse, CareerProfileUpdate
from app.schemas.education import EducationCreate, EducationResponse, EducationUpdate
from app.schemas.experience import ExperienceCreate, ExperienceResponse, ExperienceUpdate
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.skill import SkillCreate, SkillResponse, SkillUpdate
from app.schemas.user import UserResponse
from app.services.education import EducationService
from app.services.experience import ExperienceService
from app.services.me import MeService
from app.services.project import ProjectService
from app.services.skill import SkillService

router = APIRouter()


@router.get("/profile", response_model=CareerProfileResponse)
async def get_profile(session: SessionDep, user: CurrentUser):
    return await MeService(session, user).profile()


@router.post("/profile", response_model=CareerProfileResponse, status_code=201)
async def create_profile(data: CareerProfileUpdate, session: SessionDep, user: CurrentUser):
    return await MeService(session, user).create_profile(data)


@router.patch("/profile", response_model=CareerProfileResponse)
async def update_profile(data: CareerProfileUpdate, session: SessionDep, user: CurrentUser):
    return await MeService(session, user).update_profile(data)


@router.post("/onboarding/complete", response_model=UserResponse)
async def complete_onboarding(session: SessionDep, user: CurrentUser):
    return await MeService(session, user).complete_onboarding()


@router.get("/education", response_model=list[EducationResponse])
async def list_education(session: SessionDep, user: CurrentUser):
    return await MeService(session, user).list_children(EducationService(session), "list_education")


@router.post("/education", response_model=EducationResponse, status_code=201)
async def create_education(data: EducationCreate, session: SessionDep, user: CurrentUser):
    return await MeService(session, user).create_child(
        EducationService(session), "create_education", data
    )


@router.patch("/education/{item_id}", response_model=EducationResponse)
async def update_education(
    item_id: UUID, data: EducationUpdate, session: SessionDep, user: CurrentUser
):
    return await MeService(session, user).update_child(
        EducationService(session), "get_education", "update_education", item_id, data
    )


@router.delete("/education/{item_id}", status_code=204)
async def delete_education(item_id: UUID, session: SessionDep, user: CurrentUser):
    await MeService(session, user).delete_child(
        EducationService(session), "get_education", "delete_education", item_id
    )


@router.get("/experiences", response_model=list[ExperienceResponse])
async def list_experience(session: SessionDep, user: CurrentUser):
    return await MeService(session, user).list_children(
        ExperienceService(session), "list_experiences"
    )


@router.post("/experiences", response_model=ExperienceResponse, status_code=201)
async def create_experience(data: ExperienceCreate, session: SessionDep, user: CurrentUser):
    return await MeService(session, user).create_child(
        ExperienceService(session), "create_experience", data
    )


@router.patch("/experiences/{item_id}", response_model=ExperienceResponse)
async def update_experience(
    item_id: UUID, data: ExperienceUpdate, session: SessionDep, user: CurrentUser
):
    return await MeService(session, user).update_child(
        ExperienceService(session), "get_experience", "update_experience", item_id, data
    )


@router.delete("/experiences/{item_id}", status_code=204)
async def delete_experience(item_id: UUID, session: SessionDep, user: CurrentUser):
    await MeService(session, user).delete_child(
        ExperienceService(session), "get_experience", "delete_experience", item_id
    )


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(session: SessionDep, user: CurrentUser):
    return await MeService(session, user).list_children(ProjectService(session), "list_projects")


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, session: SessionDep, user: CurrentUser):
    return await MeService(session, user).create_child(
        ProjectService(session), "create_project", data
    )


@router.patch("/projects/{item_id}", response_model=ProjectResponse)
async def update_project(
    item_id: UUID, data: ProjectUpdate, session: SessionDep, user: CurrentUser
):
    return await MeService(session, user).update_child(
        ProjectService(session), "get_project", "update_project", item_id, data
    )


@router.delete("/projects/{item_id}", status_code=204)
async def delete_project(item_id: UUID, session: SessionDep, user: CurrentUser):
    await MeService(session, user).delete_child(
        ProjectService(session), "get_project", "delete_project", item_id
    )


@router.get("/skills", response_model=list[SkillResponse])
async def list_skills(session: SessionDep, user: CurrentUser):
    return await MeService(session, user).list_children(SkillService(session), "list_skills")


@router.post("/skills", response_model=SkillResponse, status_code=201)
async def create_skill(data: SkillCreate, session: SessionDep, user: CurrentUser):
    return await MeService(session, user).create_child(SkillService(session), "create_skill", data)


@router.patch("/skills/{item_id}", response_model=SkillResponse)
async def update_skill(item_id: UUID, data: SkillUpdate, session: SessionDep, user: CurrentUser):
    return await MeService(session, user).update_child(
        SkillService(session), "get_skill", "update_skill", item_id, data
    )


@router.delete("/skills/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(item_id: UUID, session: SessionDep, user: CurrentUser):
    await MeService(session, user).delete_child(
        SkillService(session), "get_skill", "delete_skill", item_id
    )
