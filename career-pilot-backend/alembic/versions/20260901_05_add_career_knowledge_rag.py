"""add user-scoped career knowledge vector store

Revision ID: 20260901_05
Revises: 20260901_04
"""

import sqlalchemy as sa
from alembic import op

revision = "20260901_05"
down_revision = "20260901_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "career_knowledge_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_reference", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_career_knowledge_documents_user_id", "career_knowledge_documents", ["user_id"])
    op.execute("""
        CREATE TABLE career_knowledge_chunks (
          id uuid PRIMARY KEY, document_id uuid NOT NULL REFERENCES career_knowledge_documents(id) ON DELETE CASCADE,
          user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE, content text NOT NULL,
          embedding vector(1536) NOT NULL, metadata_json json NOT NULL DEFAULT '{}'::json,
          chunk_index integer NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.create_index("ix_career_knowledge_chunks_user_id", "career_knowledge_chunks", ["user_id"])
    op.execute("CREATE INDEX ix_career_knowledge_chunks_embedding ON career_knowledge_chunks USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.drop_table("career_knowledge_chunks")
    op.drop_table("career_knowledge_documents")
