"""Add semantic-search embedding storage."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from civiccode.migrations.guards import idempotent_create_table


revision = "civiccode_0011_semantic_search"
down_revision = "civiccode_0010_handoff_resolve"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        embedding_type = sa.Text()
    else:
        embedding_type = sa.JSON()
    idempotent_create_table(
        "section_search_embeddings",
        sa.Column("section_id", sa.String(255), primary_key=True),
        sa.Column("section_version_id", sa.String(255), nullable=False),
        sa.Column("embedding_model", sa.String(255), nullable=False),
        sa.Column("embedding", embedding_type, nullable=False),
        sa.Column("source_text_checksum", sa.String(128), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="civiccode",
    )
    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE civiccode.section_search_embeddings "
            "ALTER COLUMN embedding TYPE vector(768) USING embedding::vector"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_section_search_embeddings_embedding "
            "ON civiccode.section_search_embeddings "
            "USING ivfflat (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    op.drop_table("section_search_embeddings", schema="civiccode")
