from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UserDefinedType

from app.db.base import Base
from app.models.base import UUIDTimestampMixin


class Vector(UserDefinedType):
    """Minimal pgvector type; keeps pgvector infrastructure out of agent code."""

    cache_ok = True

    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions

    def get_col_spec(self, **kwargs: Any) -> str:
        return f"vector({self.dimensions})"

    def bind_processor(self, dialect):
        def process(value: list[float] | None) -> str | None:
            return None if value is None else "[" + ",".join(str(float(v)) for v in value) + "]"

        return process


class CareerKnowledgeDocument(UUIDTimestampMixin, Base):
    __tablename__ = "career_knowledge_documents"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    source_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)


class CareerKnowledgeChunk(UUIDTimestampMixin, Base):
    __tablename__ = "career_knowledge_chunks"

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("career_knowledge_documents.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    chunk_index: Mapped[int] = mapped_column(Integer)
