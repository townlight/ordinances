"""Add durable codifier sync source state."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from townlight_code.migrations.guards import idempotent_create_table


revision = "townlight_code_0008"
down_revision = "townlight_code_0007"
branch_labels = None
depends_on = None


def _updated_at() -> sa.Column:
    return sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def upgrade() -> None:
    idempotent_create_table(
        "codifier_sync_source_records",
        sa.Column("source_id", sa.String(255), primary_key=True),
        sa.Column("connector", sa.String(120), nullable=False),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("sync_schedule", sa.String(120), nullable=False),
        sa.Column("allowlisted_hosts", postgresql.JSONB(), nullable=False),
        sa.Column("host_validation", postgresql.JSONB(), nullable=False),
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempted_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_import_job_id", sa.String(255), nullable=True),
        sa.Column("next_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_failure_count", sa.Integer(), nullable=False),
        sa.Column("active_failure_count", sa.Integer(), nullable=False),
        sa.Column("sync_paused", sa.Boolean(), nullable=False),
        sa.Column("sync_paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_paused_reason", sa.Text(), nullable=True),
        sa.Column("last_sync_status", sa.String(80), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        _updated_at(),
        schema="townlight_code",
    )
    idempotent_create_table(
        "codifier_sync_delta_plan_records",
        sa.Column("plan_id", sa.String(255), primary_key=True),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("connector", sa.String(120), nullable=False),
        sa.Column("request_url", sa.Text(), nullable=False),
        sa.Column("delta_enabled", sa.Boolean(), nullable=False),
        sa.Column("cursor_param", sa.String(120), nullable=True),
        sa.Column("cursor_value", sa.String(120), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("fix", sa.Text(), nullable=False),
        sa.Column("planned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("import_job_id", sa.String(255), nullable=True),
        schema="townlight_code",
    )


def downgrade() -> None:
    op.drop_table("codifier_sync_delta_plan_records", schema="townlight_code")
    op.drop_table("codifier_sync_source_records", schema="townlight_code")
