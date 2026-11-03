"""Add durable local import job records."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from townlight_code.migrations.guards import idempotent_create_table


revision = "townlight_code_0007"
down_revision = "townlight_code_0006"
branch_labels = None
depends_on = None


def _created_at() -> sa.Column:
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def upgrade() -> None:
    idempotent_create_table(
        "import_job_records",
        sa.Column("job_id", sa.String(255), primary_key=True),
        sa.Column("connector_type", sa.String(120), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("status", sa.String(80), nullable=False),
        sa.Column("retry_of", sa.String(255), nullable=True),
        sa.Column("counts", postgresql.JSONB(), nullable=False),
        sa.Column("provenance", postgresql.JSONB(), nullable=False),
        sa.Column("failure", postgresql.JSONB(), nullable=True),
        sa.Column("source_id", sa.String(255), nullable=True),
        _created_at(),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        schema="townlight_code",
    )


def downgrade() -> None:
    op.drop_table("import_job_records", schema="townlight_code")
