from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.career_profile import CareerProfile


class Education(UUIDTimestampMixin, Base):
    __tablename__ = "education"

    career_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    institution: Mapped[str] = mapped_column(String(200))
    degree: Mapped[str | None] = mapped_column(String(200))
    field_of_study: Mapped[str | None] = mapped_column(String(200))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    grade: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    career_profile: Mapped[CareerProfile] = relationship(back_populates="education")
