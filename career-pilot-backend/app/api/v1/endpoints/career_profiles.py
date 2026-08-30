from uuid import UUID

from fastapi import APIRouter, Response

from app.api.dependencies import SessionDep
from app.schemas.career_profile import (
    CareerProfileCreate,
    CareerProfileResponse,
    CareerProfileUpdate,
)
from app.services.career_profile import CareerProfileService

router = APIRouter()


@router.post("", response_model=CareerProfileResponse, status_code=201)
async def create_profile(data: CareerProfileCreate, db: SessionDep):
    return await CareerProfileService(db).create_profile(data)


@router.get("/{profile_id}", response_model=CareerProfileResponse)
async def get_profile(profile_id: UUID, db: SessionDep):
    return await CareerProfileService(db).get_profile(profile_id)


@router.get("/user/{user_id}", response_model=CareerProfileResponse)
async def get_profile_by_user(user_id: UUID, db: SessionDep):
    return await CareerProfileService(db).get_profile_by_user(user_id)


@router.patch("/{profile_id}", response_model=CareerProfileResponse)
async def update_profile(profile_id: UUID, data: CareerProfileUpdate, db: SessionDep):
    return await CareerProfileService(db).update_profile(profile_id, data)


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(profile_id: UUID, db: SessionDep):
    await CareerProfileService(db).delete_profile(profile_id)
    return Response(status_code=204)
