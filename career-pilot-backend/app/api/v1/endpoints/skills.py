from uuid import UUID

from fastapi import APIRouter, Response

from app.api.dependencies import SessionDep
from app.schemas.skill import SkillCreate, SkillResponse, SkillUpdate
from app.services.skill import SkillService

router = APIRouter()


@router.post("/career-profiles/{profile_id}/skills", response_model=SkillResponse, status_code=201)
async def create(profile_id: UUID, data: SkillCreate, db: SessionDep):
    return await SkillService(db).create_skill(profile_id, data)


@router.get("/career-profiles/{profile_id}/skills", response_model=list[SkillResponse])
async def list_items(profile_id: UUID, db: SessionDep):
    return await SkillService(db).list_skills(profile_id)


@router.get("/skills/{item_id}", response_model=SkillResponse)
async def get(item_id: UUID, db: SessionDep):
    return await SkillService(db).get_skill(item_id)


@router.patch("/skills/{item_id}", response_model=SkillResponse)
async def update(item_id: UUID, data: SkillUpdate, db: SessionDep):
    return await SkillService(db).update_skill(item_id, data)


@router.delete("/skills/{item_id}", status_code=204)
async def delete(item_id: UUID, db: SessionDep):
    await SkillService(db).delete_skill(item_id)
    return Response(status_code=204)
