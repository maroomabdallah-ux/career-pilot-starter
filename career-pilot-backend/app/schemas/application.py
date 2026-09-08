from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.job import JobResult


class ApplicationCreate(BaseModel):
    job: JobResult


class ApplicationPrepare(BaseModel):
    version: int = Field(ge=1)
    resume_id: UUID | None = None
    cover_letter: str = Field(default="", max_length=20000)
    answers: list[dict[str, str]] = Field(default_factory=list, max_length=50)
    application_url: HttpUrl | None = None


class ApplicationApprove(BaseModel):
    version: int = Field(ge=1)
    approved: Literal[True]


class ApplicationTrack(BaseModel):
    version: int = Field(ge=1)
    status: Literal["submitted_externally", "interview", "offer", "rejected", "withdrawn"]
    notes: str = Field(default="", max_length=10000)
    confirmed: Literal[True]


class ApplicationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    kind: str
    message: str
    actor: str
    created_at: datetime


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    saved_job_id: UUID | None
    job_snapshot: dict
    source: str
    external_job_id: str
    status: str
    version: int
    resume_id: UUID | None
    resume_snapshot: dict
    profile_snapshot: dict
    cover_letter: str
    answers: list
    notes: str
    application_url: str
    method: str
    approved_at: datetime | None
    applied_at: datetime | None
    submission_evidence: str | None
    created_at: datetime
    updated_at: datetime
    events: list[ApplicationEventResponse] = Field(default_factory=list)
