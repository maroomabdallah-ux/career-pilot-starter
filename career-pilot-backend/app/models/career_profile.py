from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.education import Education
    from app.models.experience import Experience
    from app.models.project import Project
    from app.models.skill import Skill
    from app.models.user import User


class CareerProfile(UUIDTimestampMixin, Base):
    __tablename__ = "career_profiles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    professional_title: Mapped[str | None] = mapped_column(String(200))
    professional_summary: Mapped[str | None] = mapped_column(Text)
    profile_picture: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(50))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    linkedin_url: Mapped[str | None] = mapped_column(String(2048))
    github_url: Mapped[str | None] = mapped_column(String(2048))
    portfolio_url: Mapped[str | None] = mapped_column(String(2048))
    target_roles: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSONB), default=list, server_default="[]"
    )
    preferred_locations: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSONB), default=list, server_default="[]"
    )
    preferred_work_modes: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSONB), default=list, server_default="[]"
    )
    years_of_experience: Mapped[float] = mapped_column(Float, default=0, server_default="0")

    user: Mapped[User] = relationship(back_populates="career_profile")
    education: Mapped[list[Education]] = relationship(
        back_populates="career_profile", cascade="all, delete-orphan"
    )
    experiences: Mapped[list[Experience]] = relationship(
        back_populates="career_profile", cascade="all, delete-orphan"
    )
    projects: Mapped[list[Project]] = relationship(
        back_populates="career_profile", cascade="all, delete-orphan"
    )
    skills: Mapped[list[Skill]] = relationship(
        back_populates="career_profile", cascade="all, delete-orphan"
    )
