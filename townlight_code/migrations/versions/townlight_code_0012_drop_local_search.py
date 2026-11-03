"""Drop module-local section embedding table.

Revision ID: townlight_code_0012_drop_local_search
Revises: townlight_code_0011_semantic_search
Create Date: 2026-05-22
"""

from __future__ import annotations

from alembic import op


revision = "townlight_code_0012"
down_revision = "townlight_code_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("section_search_embeddings", schema="townlight_code", if_exists=True)


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the retired module-local embedding table."
    )
