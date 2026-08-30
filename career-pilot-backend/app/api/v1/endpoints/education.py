from uuid import UUID

from fastapi import APIRouter, Response

from app.api.dependencies import SessionDep
from app.schemas.education import EducationCreate, EducationResponse, EducationUpdate
from app.services.education import EducationService

router = APIRouter()


@router.post(
    "/career-profiles/{profile_id}/education", response_model=EducationResponse, status_code=201
)
async def create(profile_id: UUID, data: EducationCreate, db: SessionDep):
    return await EducationService(db).create_education(profile_id, data)


@router.get("/career-profiles/{profile_id}/education", response_model=list[EducationResponse])
async def list_items(profile_id: UUID, db: SessionDep):
    return await EducationService(db).list_education(profile_id)


@router.get("/education/{item_id}", response_model=EducationResponse)
async def get(item_id: UUID, db: SessionDep):
    return await EducationService(db).get_education(item_id)


@router.patch("/education/{item_id}", response_model=EducationResponse)
async def update(item_id: UUID, data: EducationUpdate, db: SessionDep):
    return await EducationService(db).update_education(item_id, data)


@router.delete("/education/{item_id}", status_code=204)
async def delete(item_id: UUID, db: SessionDep):
    await EducationService(db).delete_education(item_id)
    return Response(status_code=204)
