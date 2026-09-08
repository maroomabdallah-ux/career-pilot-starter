from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDTimestampMixin


class JobApplication(UUIDTimestampMixin, Base):
    __tablename__ = "job_applications"
    __table_args__ = (
        UniqueConstraint("user_id", "source", "external_job_id", name="uq_application_user_job"),
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    saved_job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("saved_jobs.id", ondelete="SET NULL")
    )
    source: Mapped[str] = mapped_column(String(60))
    external_job_id: Mapped[str] = mapped_column(Text)
    job_snapshot: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)
    resume_id: Mapped[UUID | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"))
    resume_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    profile_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    cover_letter: Mapped[str] = mapped_column(Text, default="")
    answers: Mapped[list] = mapped_column(JSONB, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")
    application_url: Mapped[str] = mapped_column(Text)
    method: Mapped[str] = mapped_column(String(40), default="external")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submission_evidence: Mapped[str | None] = mapped_column(Text)


class ApplicationEvent(UUIDTimestampMixin, Base):
    __tablename__ = "application_events"
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(String(30), default="user")


class IdempotentRequest(UUIDTimestampMixin, Base):
    __tablename__ = "idempotent_requests"
    __table_args__ = (
        UniqueConstraint("user_id", "operation", "key", name="uq_idempotency_user_operation_key"),
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    operation: Mapped[str] = mapped_column(String(250))
    key: Mapped[str] = mapped_column(String(128))
    fingerprint: Mapped[str] = mapped_column(String(64))
    request_id: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(30), default="processing")
    response: Mapped[dict | None] = mapped_column(JSONB)
    status_code: Mapped[int | None] = mapped_column(Integer)
