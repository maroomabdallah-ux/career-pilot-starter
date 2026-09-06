"""store resume design settings

Revision ID: 20260906_09
Revises: 20260906_08
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260906_09"
down_revision = "20260906_08"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "resumes",
        sa.Column(
            "design",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade():
    op.drop_column("resumes", "design")
