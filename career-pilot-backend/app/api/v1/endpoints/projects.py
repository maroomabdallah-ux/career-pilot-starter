from uuid import UUID

from fastapi import APIRouter, Response

from app.api.dependencies import SessionDep
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project import ProjectService

router = APIRouter()


@router.post(
    "/career-profiles/{profile_id}/projects", response_model=ProjectResponse, status_code=201
)
async def create(profile_id: UUID, data: ProjectCreate, db: SessionDep):
    return await ProjectService(db).create_project(profile_id, data)


@router.get("/career-profiles/{profile_id}/projects", response_model=list[ProjectResponse])
async def list_items(profile_id: UUID, db: SessionDep):
    return await ProjectService(db).list_projects(profile_id)


@router.get("/projects/{item_id}", response_model=ProjectResponse)
async def get(item_id: UUID, db: SessionDep):
    return await ProjectService(db).get_project(item_id)


@router.patch("/projects/{item_id}", response_model=ProjectResponse)
async def update(item_id: UUID, data: ProjectUpdate, db: SessionDep):
    return await ProjectService(db).update_project(item_id, data)


@router.delete("/projects/{item_id}", status_code=204)
async def delete(item_id: UUID, db: SessionDep):
    await ProjectService(db).delete_project(item_id)
    return Response(status_code=204)
