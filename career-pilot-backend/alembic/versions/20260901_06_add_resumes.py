"""add resumes

Revision ID: 20260901_06
Revises: 20260901_05
"""
import sqlalchemy as sa
from alembic import op
revision="20260901_06"
down_revision="20260901_05"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("resumes",sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("user_id",sa.Uuid(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("title",sa.String(200),nullable=False),sa.Column("resume_type",sa.String(32),nullable=False,server_default="general"),sa.Column("status",sa.String(32),nullable=False,server_default="draft"),sa.Column("language",sa.String(8),nullable=False,server_default="en"),sa.Column("content",sa.JSON(),nullable=False,server_default="{}"),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False))
    op.create_index("ix_resumes_user_id","resumes",["user_id"])
def downgrade(): op.drop_table("resumes")
