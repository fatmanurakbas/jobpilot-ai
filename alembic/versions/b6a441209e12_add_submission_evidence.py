"""add form preparation and submission evidence

Revision ID: b6a441209e12
Revises: dc4674df6b85
Create Date: 2026-09-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b6a441209e12"
down_revision: Union[str, Sequence[str], None] = "dc4674df6b85"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("form_prepared_at", sa.DateTime(), nullable=True))
    op.add_column("applications", sa.Column("form_verification_data", postgresql.JSONB(), nullable=True))
    op.add_column("applications", sa.Column("submission_attempted_at", sa.DateTime(), nullable=True))
    op.add_column("applications", sa.Column("submission_screenshot_path", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "submission_screenshot_path")
    op.drop_column("applications", "submission_attempted_at")
    op.drop_column("applications", "form_verification_data")
    op.drop_column("applications", "form_prepared_at")
