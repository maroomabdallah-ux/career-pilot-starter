"""create career profile core tables"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260830_01"
down_revision = None
branch_labels = None
depends_on = None


def timestamps():
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        *timestamps(),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "career_profiles",
        *timestamps(),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("professional_title", sa.String(200)),
        sa.Column("professional_summary", sa.Text()),
        sa.Column("phone", sa.String(50)),
        sa.Column("city", sa.String(100)),
        sa.Column("country", sa.String(100)),
        sa.Column("linkedin_url", sa.String(2048)),
        sa.Column("github_url", sa.String(2048)),
        sa.Column("portfolio_url", sa.String(2048)),
        sa.Column(
            "target_roles",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "preferred_locations",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "preferred_work_modes",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("years_of_experience", sa.Float(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_profiles_user_id", "career_profiles", ["user_id"], unique=True)
    op.create_table(
        "education",
        *timestamps(),
        sa.Column("career_profile_id", sa.Uuid(), nullable=False),
        sa.Column("institution", sa.String(200), nullable=False),
        sa.Column("degree", sa.String(200)),
        sa.Column("field_of_study", sa.String(200)),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("grade", sa.String(100)),
        sa.Column("description", sa.Text()),
        sa.ForeignKeyConstraint(["career_profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "experiences",
        *timestamps(),
        sa.Column("career_profile_id", sa.Uuid(), nullable=False),
        sa.Column("company", sa.String(200), nullable=False),
        sa.Column("job_title", sa.String(200), nullable=False),
        sa.Column("employment_type", sa.String(100)),
        sa.Column("location", sa.String(200)),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "achievements",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "technologies",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["career_profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "projects",
        *timestamps(),
        sa.Column("career_profile_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("role", sa.String(200)),
        sa.Column(
            "technologies",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("project_url", sa.String(2048)),
        sa.Column("repository_url", sa.String(2048)),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.ForeignKeyConstraint(["career_profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "skills",
        *timestamps(),
        sa.Column("career_profile_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("proficiency_level", sa.String(100)),
        sa.Column("years_of_experience", sa.Float(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["career_profile_id"], ["career_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("career_profile_id", "name", name="uq_skill_profile_name"),
    )
    for table in ("education", "experiences", "projects", "skills"):
        op.create_index(f"ix_{table}_career_profile_id", table, ["career_profile_id"])


def downgrade() -> None:
    for table in ("skills", "projects", "experiences", "education", "career_profiles", "users"):
        op.drop_table(table)
