from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, SessionDep
from app.api.idempotency import IdempotentRoute
from app.schemas.application import (
    ApplicationApprove,
    ApplicationCreate,
    ApplicationGenerate,
    ApplicationPrepare,
    ApplicationResponse,
    ApplicationTailor,
    ApplicationTrack,
    InterviewKit,
    PreparationDraft,
)
from app.services.applications import ApplicationService

router = APIRouter(route_class=IdempotentRoute)


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(session: SessionDep, user: CurrentUser):
    return await ApplicationService(session, user).list()


@router.post("", response_model=ApplicationResponse)
async def create_application(data: ApplicationCreate, session: SessionDep, user: CurrentUser):
    return await ApplicationService(session, user).create(data.job)


@router.post("/{application_id}/tailor", response_model=ApplicationResponse)
async def tailor_application(
    application_id: UUID, data: ApplicationTailor, session: SessionDep, user: CurrentUser
):
    return await ApplicationService(session, user).tailor(application_id, data)


@router.post("/{application_id}/generate", response_model=PreparationDraft)
async def generate_application(
    application_id: UUID, data: ApplicationGenerate, session: SessionDep, user: CurrentUser
):
    application, missing = await ApplicationService(session, user).generate_preparation(
        application_id, data
    )
    return PreparationDraft(application=application, missing_information=missing)


@router.get("/{application_id}/interview-kit", response_model=InterviewKit)
async def interview_kit(application_id: UUID, session: SessionDep, user: CurrentUser):
    return await ApplicationService(session, user).interview_kit(application_id)


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(application_id: UUID, session: SessionDep, user: CurrentUser):
    service = ApplicationService(session, user)
    return await service.response(await service.get(application_id))


@router.post("/{application_id}/prepare", response_model=ApplicationResponse)
async def prepare_application(
    application_id: UUID, data: ApplicationPrepare, session: SessionDep, user: CurrentUser
):
    return await ApplicationService(session, user).prepare(application_id, data)


@router.post("/{application_id}/approve", response_model=ApplicationResponse)
async def approve_application(
    application_id: UUID, data: ApplicationApprove, session: SessionDep, user: CurrentUser
):
    return await ApplicationService(session, user).approve(application_id, data)


@router.post("/{application_id}/track", response_model=ApplicationResponse)
async def track_application(
    application_id: UUID, data: ApplicationTrack, session: SessionDep, user: CurrentUser
):
    return await ApplicationService(session, user).track(application_id, data)
