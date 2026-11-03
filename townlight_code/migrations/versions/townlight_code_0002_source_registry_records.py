"""Create persisted source registry records."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from townlight_code.migrations.guards import idempotent_create_table


revision = "townlight_code_0002"
down_revision = "townlight_code_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    idempotent_create_table(
        "source_registry_records",
        sa.Column("source_id", sa.String(255), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("publisher", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("source_category", sa.String(120), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("file_reference", sa.Text(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieval_method", sa.String(120), nullable=True),
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.Column("source_owner", sa.String(255), nullable=True),
        sa.Column("is_official", sa.Boolean(), nullable=False),
        sa.Column("official_status_note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(80), nullable=False),
        sa.Column("staff_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema="townlight_code",
    )


def downgrade() -> None:
    op.drop_table("source_registry_records", schema="townlight_code")
