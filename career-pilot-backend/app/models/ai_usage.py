from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDTimestampMixin


class AIUsage(UUIDTimestampMixin, Base):
    __tablename__ = "ai_usage"
    __table_args__ = (
        Index("ix_ai_usage_user_created", "user_id", "created_at"),
        Index("ix_ai_usage_request_id", "request_id"),
        Index("ix_ai_usage_conversation_id", "conversation_id"),
        Index("ix_ai_usage_agent_name", "agent_name"),
        Index("ix_ai_usage_model", "model"),
        Index("ix_ai_usage_created_at", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    conversation_id: Mapped[str | None] = mapped_column(String(128))
    request_id: Mapped[str] = mapped_column(String(64))
    agent_name: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(120))
    provider: Mapped[str] = mapped_column(String(50))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cached_input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    input_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    cached_input_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    output_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    pricing_status: Mapped[str] = mapped_column(String(40))
