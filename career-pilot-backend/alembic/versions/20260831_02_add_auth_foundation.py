"""add authentication foundation"""
import sqlalchemy as sa
from alembic import op

revision = "20260831_02"
down_revision = "20260830_01"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Nullable preserves existing development users without inventing passwords.
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("onboarding_completed", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token_jti", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("user_agent", sa.String(512)),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_refresh_token_jti", "auth_sessions", ["refresh_token_jti"], unique=True)
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])

def downgrade() -> None:
    op.drop_table("auth_sessions")
    op.drop_column("users", "onboarding_completed")
    op.drop_column("users", "password_hash")
