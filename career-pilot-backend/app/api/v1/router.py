from fastapi import APIRouter

from app.api.v1.endpoints import (
    career_profiles,
    education,
    experiences,
    projects,
    skills,
    system,
    users,
)

api_router = APIRouter()
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    career_profiles.router, prefix="/career-profiles", tags=["career profiles"]
)
api_router.include_router(education.router, tags=["education"])
api_router.include_router(experiences.router, tags=["experiences"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(skills.router, tags=["skills"])
