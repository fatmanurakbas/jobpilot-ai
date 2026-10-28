
"""initial schema

Revision ID: 2767b1d3e388
Revises:
Create Date: 2026-09-22 10:27:00.766438
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "2767b1d3e388"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("university", sa.String(length=255), nullable=True),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("linkedin", sa.Text(), nullable=True),
        sa.Column("github", sa.Text(), nullable=True),
        sa.Column("portfolio", sa.Text(), nullable=True),
        sa.Column("master_cv_filename", sa.String(length=500), nullable=True),
        sa.Column("profile_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False,  server_default=sa.func.now()),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company", sa.String(length=150), nullable=False),
        sa.Column("position", sa.String(length=150), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=True),
        sa.Column("job_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="FOUND"),
        sa.Column("analysis_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_jobs_id", "jobs", ["id"], unique=False)

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("match_percentage", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="FOUND"),
        sa.Column("cv_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
    )


def downgrade() -> None:
    op.drop_table("applications")
    op.drop_index("ix_jobs_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("candidates")
