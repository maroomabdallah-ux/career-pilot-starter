from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_usage,
    applications,
    auth,
    career_profiles,
    education,
    experiences,
    jobs,
    me,
    profile_agent,
    projects,
    reference,
    resumes,
    skills,
    system,
    usage,
    users,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(me.router, prefix="/me", tags=["current user"])
api_router.include_router(reference.router, prefix="/reference", tags=["reference data"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(profile_agent.router, prefix="/ai/profile", tags=["profile agent"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(usage.router, prefix="/usage", tags=["AI usage"])
api_router.include_router(admin_usage.router, prefix="/admin/usage", tags=["admin AI usage"])
if settings.ENABLE_LEGACY_CRUD_ROUTES:
    api_router.include_router(users.router, prefix="/users", tags=["legacy development"])
    api_router.include_router(
        career_profiles.router,
        prefix="/career-profiles",
        tags=["legacy development"],
    )
    api_router.include_router(education.router, tags=["legacy development"])
    api_router.include_router(experiences.router, tags=["legacy development"])
    api_router.include_router(projects.router, tags=["legacy development"])
    api_router.include_router(skills.router, tags=["legacy development"])
