from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class SavedJob(UUIDTimestampMixin, Base):
    __tablename__ = "saved_jobs"
    __table_args__ = (UniqueConstraint("user_id", "source", "external_job_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(60))
    external_job_id: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(300))
    company: Mapped[str] = mapped_column(String(250))
    location: Mapped[str | None] = mapped_column(String(250))
    workplace_type: Mapped[str] = mapped_column(String(30), default="unknown")
    employment_type: Mapped[str | None] = mapped_column(String(80))
    apply_url: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text)
    snapshot: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    saved_at: Mapped[datetime] = mapped_column(server_default=func.now())
    user: Mapped[User] = relationship(back_populates="saved_jobs")


class JobSearchHistory(UUIDTimestampMixin, Base):
    __tablename__ = "job_search_history"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    criteria: Mapped[dict] = mapped_column(JSONB)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    sources: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]")
    source_failures: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]")
    user: Mapped[User] = relationship(back_populates="job_search_history")
