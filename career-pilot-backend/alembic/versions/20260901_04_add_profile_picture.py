"""add optional career profile picture

Revision ID: 20260901_04
Revises: 20260831_03
"""

import sqlalchemy as sa
from alembic import op

revision = "20260901_04"
down_revision = "20260831_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("career_profiles", sa.Column("profile_picture", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("career_profiles", "profile_picture")
