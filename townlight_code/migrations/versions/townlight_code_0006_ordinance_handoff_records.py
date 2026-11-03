"""Add durable TownlightMeetings ordinance handoff records."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from townlight_code.migrations.guards import idempotent_create_table


revision = "townlight_code_0006"
down_revision = "townlight_code_0005"
branch_labels = None
depends_on = None


def _created_at() -> sa.Column:
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def upgrade() -> None:
    idempotent_create_table(
        "ordinance_handoff_records",
        sa.Column("event_id", sa.String(255), primary_key=True),
        sa.Column("external_event_id", sa.String(255), nullable=False),
        sa.Column("townlight_meetings_meeting_id", sa.String(255), nullable=False),
        sa.Column("townlight_meetings_agenda_item_id", sa.String(255), nullable=False),
        sa.Column("ordinance_number", sa.String(120), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.String(80), nullable=False),
        sa.Column("affected_sections", postgresql.JSONB(), nullable=False),
        sa.Column("source_document_url", sa.Text(), nullable=False),
        sa.Column("source_document_hash", sa.String(255), nullable=False),
        sa.Column("ordinance_text", sa.Text(), nullable=False),
        sa.Column("adopted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
        _created_at(),
        schema="townlight_code",
    )
    idempotent_create_table(
        "ordinance_handoff_audit_event_records",
        sa.Column("event_id", sa.String(255), primary_key=True),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("target_id", sa.String(255), nullable=False),
        _created_at(),
        schema="townlight_code",
    )


def downgrade() -> None:
    op.drop_table("ordinance_handoff_audit_event_records", schema="townlight_code")
    op.drop_table("ordinance_handoff_records", schema="townlight_code")
