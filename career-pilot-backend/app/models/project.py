from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.career_profile import CareerProfile


class Project(UUIDTimestampMixin, Base):
    __tablename__ = "projects"
    career_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(String(200))
    technologies: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSONB), default=list, server_default="[]"
    )
    project_url: Mapped[str | None] = mapped_column(String(2048))
    repository_url: Mapped[str | None] = mapped_column(String(2048))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    career_profile: Mapped[CareerProfile] = relationship(back_populates="projects")
