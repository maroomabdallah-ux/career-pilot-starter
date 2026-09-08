"""Applications, approval events, durable requests and unique LLM call accounting.

Revision ID: 20260908_12
Revises: 20260906_11
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260908_12"
down_revision = "20260906_11"
branch_labels = None
depends_on = None


def identity():
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade():
    # Legacy entries represent separate calls; preserve all historical totals.
    op.add_column("ai_usage", sa.Column("llm_call_id", sa.String(128)))
    op.execute("UPDATE ai_usage SET llm_call_id = 'legacy-' || id::text")
    op.alter_column("ai_usage", "llm_call_id", nullable=False)
    op.create_unique_constraint("uq_ai_usage_user_call", "ai_usage", ["user_id", "llm_call_id"])
    op.alter_column("saved_jobs", "external_job_id", type_=sa.Text())
    op.create_table(
        "job_applications",
        *identity(),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("saved_job_id", sa.Uuid(), sa.ForeignKey("saved_jobs.id", ondelete="SET NULL")),
        sa.Column("source", sa.String(60), nullable=False),
        sa.Column("external_job_id", sa.Text(), nullable=False),
        sa.Column("job_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), sa.ForeignKey("resumes.id", ondelete="SET NULL")),
        sa.Column("resume_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("profile_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("cover_letter", sa.Text(), nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("application_url", sa.Text(), nullable=False),
        sa.Column("method", sa.String(40), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("applied_at", sa.DateTime(timezone=True)),
        sa.Column("submission_evidence", sa.Text()),
        sa.UniqueConstraint("user_id", "source", "external_job_id", name="uq_application_user_job"),
    )
    op.create_index("ix_job_applications_user_id", "job_applications", ["user_id"])
    op.create_table(
        "application_events",
        *identity(),
        sa.Column(
            "application_id",
            sa.Uuid(),
            sa.ForeignKey("job_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("actor", sa.String(30), nullable=False),
    )
    op.create_index(
        "ix_application_events_application_id", "application_events", ["application_id"]
    )
    op.create_table(
        "idempotent_requests",
        *identity(),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("operation", sa.String(250), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("state", sa.String(30), nullable=False),
        sa.Column("response", postgresql.JSONB()),
        sa.Column("status_code", sa.Integer()),
        sa.UniqueConstraint(
            "user_id", "operation", "key", name="uq_idempotency_user_operation_key"
        ),
    )
    op.create_index("ix_idempotent_requests_user_id", "idempotent_requests", ["user_id"])


def downgrade():
    op.drop_table("idempotent_requests")
    op.drop_table("application_events")
    op.drop_table("job_applications")
    op.drop_constraint("uq_ai_usage_user_call", "ai_usage", type_="unique")
    op.drop_column("ai_usage", "llm_call_id")
    # Keep widened job IDs: truncating existing data on downgrade would be destructive.
