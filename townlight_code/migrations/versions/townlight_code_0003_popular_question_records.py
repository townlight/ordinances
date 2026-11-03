"""Add durable popular-question discovery records."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from townlight_code.migrations.guards import idempotent_create_table


revision = "townlight_code_0003"
down_revision = "townlight_code_0002"
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    ]


def upgrade() -> None:
    idempotent_create_table(
        "popular_question_records",
        sa.Column("question_id", sa.String(255), primary_key=True),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("section_id", sa.String(255), nullable=False),
        sa.Column("section_number", sa.String(120), nullable=False),
        sa.Column("section_heading", sa.String(500), nullable=False),
        sa.Column("answer_excerpt", sa.Text(), nullable=False),
        sa.Column("citation_payload", postgresql.JSONB(), nullable=False),
        sa.Column("audience", sa.String(80), nullable=False),
        sa.Column("status", sa.String(80), nullable=False),
        sa.Column("is_popular", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        schema="townlight_code",
    )


def downgrade() -> None:
    op.drop_table("popular_question_records", schema="townlight_code")
