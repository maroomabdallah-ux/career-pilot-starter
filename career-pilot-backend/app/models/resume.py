from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDTimestampMixin


class Resume(UUIDTimestampMixin, Base):
    __tablename__ = "resumes"
    __table_args__ = (UniqueConstraint("user_id", "version", name="uq_resumes_user_version"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    document_type: Mapped[str] = mapped_column(String(32), default="resume")
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    template_id: Mapped[str] = mapped_column(String(64), default="ats_classic")
    language: Mapped[str] = mapped_column(String(8), default="en")
    content: Mapped[dict] = mapped_column(JSONB, default=dict)
