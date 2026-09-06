"""add saved jobs and job search history

Revision ID: 20260906_10
Revises: 20260906_09
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260906_10"
down_revision = "20260906_09"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "saved_jobs",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(60), nullable=False),
        sa.Column("external_job_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("company", sa.String(250), nullable=False),
        sa.Column("location", sa.String(250)),
        sa.Column("workplace_type", sa.String(30), nullable=False),
        sa.Column("employment_type", sa.String(80)),
        sa.Column("apply_url", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "source", "external_job_id"),
    )
    op.create_index("ix_saved_jobs_user_id", "saved_jobs", ["user_id"])
    op.create_table(
        "job_search_history",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("criteria", postgresql.JSONB(), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("sources", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("source_failures", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_search_history_user_id", "job_search_history", ["user_id"])


def downgrade():
    op.drop_index("ix_job_search_history_user_id", table_name="job_search_history")
    op.drop_table("job_search_history")
    op.drop_index("ix_saved_jobs_user_id", table_name="saved_jobs")
    op.drop_table("saved_jobs")
