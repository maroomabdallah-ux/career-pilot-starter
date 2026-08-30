from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.dependencies import SessionDep
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter()


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(data: UserCreate, db: SessionDep):
    return await UserService(db).create_user(data)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, db: SessionDep):
    return await UserService(db).get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: UUID, data: UserUpdate, db: SessionDep):
    return await UserService(db).update_user(user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, db: SessionDep):
    await UserService(db).delete_user(user_id)
    return Response(status_code=204)
