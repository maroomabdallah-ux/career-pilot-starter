"""add optional education grade system"""

import sqlalchemy as sa
from alembic import op

revision = "20260831_03"
down_revision = "20260831_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("education", sa.Column("grade_system", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("education", "grade_system")
