"""add AI usage accounting and admin flag

Revision ID: 20260906_11
Revises: 20260906_10
"""

import sqlalchemy as sa

from alembic import op

revision = "20260906_11"
down_revision = "20260906_10"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users", sa.Column("is_admin", sa.Boolean(), server_default="false", nullable=False)
    )
    op.create_table(
        "ai_usage",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.String(128)),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("agent_name", sa.String(80), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("cached_input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("input_cost", sa.Numeric(20, 10)),
        sa.Column("cached_input_cost", sa.Numeric(20, 10)),
        sa.Column("output_cost", sa.Numeric(20, 10)),
        sa.Column("total_cost", sa.Numeric(20, 10)),
        sa.Column("pricing_status", sa.String(40), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_usage_user_created", "ai_usage", ["user_id", "created_at"])
    for name, column in (
        ("ix_ai_usage_request_id", "request_id"),
        ("ix_ai_usage_conversation_id", "conversation_id"),
        ("ix_ai_usage_agent_name", "agent_name"),
        ("ix_ai_usage_model", "model"),
        ("ix_ai_usage_created_at", "created_at"),
    ):
        op.create_index(name, "ai_usage", [column])


def downgrade():
    for name in (
        "ix_ai_usage_created_at",
        "ix_ai_usage_model",
        "ix_ai_usage_agent_name",
        "ix_ai_usage_conversation_id",
        "ix_ai_usage_request_id",
        "ix_ai_usage_user_created",
    ):
        op.drop_index(name, table_name="ai_usage")
    op.drop_table("ai_usage")
    op.drop_column("users", "is_admin")
