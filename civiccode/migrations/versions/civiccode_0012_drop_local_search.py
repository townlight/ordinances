"""Drop module-local section embedding table.

Revision ID: civiccode_0012_drop_local_search
Revises: civiccode_0011_semantic_search
Create Date: 2026-05-22
"""

from __future__ import annotations

from alembic import op


revision = "civiccode_0012_drop_local_search"
down_revision = "civiccode_0011_semantic_search"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("section_search_embeddings", schema="civiccode", if_exists=True)


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the retired module-local embedding table."
    )
