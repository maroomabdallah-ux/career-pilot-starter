"""add current flag to projects

Revision ID: 20260906_08
Revises: 20260902_07
"""

import sqlalchemy as sa

from alembic import op

revision = "20260906_08"
down_revision = "20260902_07"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "projects",
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade():
    op.drop_column("projects", "is_current")
