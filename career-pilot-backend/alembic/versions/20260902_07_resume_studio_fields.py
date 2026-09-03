"""add resume studio version and template fields

Revision ID: 20260902_07
Revises: 20260901_06
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260902_07"
down_revision = "20260901_06"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "resumes",
        "content",
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using="content::jsonb",
    )
    op.add_column(
        "resumes",
        sa.Column("document_type", sa.String(32), nullable=False, server_default="resume"),
    )
    op.add_column("resumes", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column(
        "resumes",
        sa.Column("template_id", sa.String(64), nullable=False, server_default="ats_classic"),
    )
    op.drop_column("resumes", "resume_type")
    op.create_unique_constraint("uq_resumes_user_version", "resumes", ["user_id", "version"])


def downgrade():
    op.drop_constraint("uq_resumes_user_version", "resumes", type_="unique")
    op.add_column(
        "resumes", sa.Column("resume_type", sa.String(32), nullable=False, server_default="general")
    )
    op.drop_column("resumes", "template_id")
    op.drop_column("resumes", "version")
    op.drop_column("resumes", "document_type")
    op.alter_column("resumes", "content", type_=sa.JSON(), postgresql_using="content::json")
