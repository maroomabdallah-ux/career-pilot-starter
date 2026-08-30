from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.career_profile import CareerProfile


class Experience(UUIDTimestampMixin, Base):
    __tablename__ = "experiences"
    career_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    company: Mapped[str] = mapped_column(String(200))
    job_title: Mapped[str] = mapped_column(String(200))
    employment_type: Mapped[str | None] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(200))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    description: Mapped[str | None] = mapped_column(Text)
    achievements: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSONB), default=list, server_default="[]"
    )
    technologies: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSONB), default=list, server_default="[]"
    )
    career_profile: Mapped[CareerProfile] = relationship(back_populates="experiences")
