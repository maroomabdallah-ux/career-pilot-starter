from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    career_profiles,
    education,
    experiences,
    me,
    projects,
    reference,
    skills,
    system,
    users,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(me.router, prefix="/me", tags=["current user"])
api_router.include_router(reference.router, prefix="/reference", tags=["reference data"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
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
