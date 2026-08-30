from uuid import UUID

from fastapi import APIRouter, Response

from app.api.dependencies import SessionDep
from app.schemas.experience import ExperienceCreate, ExperienceResponse, ExperienceUpdate
from app.services.experience import ExperienceService

router = APIRouter()


@router.post(
    "/career-profiles/{profile_id}/experiences", response_model=ExperienceResponse, status_code=201
)
async def create(profile_id: UUID, data: ExperienceCreate, db: SessionDep):
    return await ExperienceService(db).create_experience(profile_id, data)


@router.get("/career-profiles/{profile_id}/experiences", response_model=list[ExperienceResponse])
async def list_items(profile_id: UUID, db: SessionDep):
    return await ExperienceService(db).list_experiences(profile_id)


@router.get("/experiences/{item_id}", response_model=ExperienceResponse)
async def get(item_id: UUID, db: SessionDep):
    return await ExperienceService(db).get_experience(item_id)


@router.patch("/experiences/{item_id}", response_model=ExperienceResponse)
async def update(item_id: UUID, data: ExperienceUpdate, db: SessionDep):
    return await ExperienceService(db).update_experience(item_id, data)


@router.delete("/experiences/{item_id}", status_code=204)
async def delete(item_id: UUID, db: SessionDep):
    await ExperienceService(db).delete_experience(item_id)
    return Response(status_code=204)
