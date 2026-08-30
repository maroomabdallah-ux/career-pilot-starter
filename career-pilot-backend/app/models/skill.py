from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDTimestampMixin

if TYPE_CHECKING:
    from app.models.career_profile import CareerProfile


class Skill(UUIDTimestampMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("career_profile_id", "name", name="uq_skill_profile_name"),)
    career_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(100))
    proficiency_level: Mapped[str | None] = mapped_column(String(100))
    years_of_experience: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    career_profile: Mapped[CareerProfile] = relationship(back_populates="skills")
