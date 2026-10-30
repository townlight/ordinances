"""CivicCode canonical schema metadata.

Milestone 2 defines table metadata only. Source registration, imports, search,
Q&A, summaries, and public lookup behavior land in later milestones.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from civiccore.db import Base


SCHEMA = "civiccode"


def id_column() -> sa.Column:
    return sa.Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    ]


code_sources = sa.Table(
    "code_sources",
    Base.metadata,
    id_column(),
    sa.Column("name", sa.String(255), nullable=False),
    sa.Column("publisher", sa.String(255), nullable=False),
    sa.Column("source_type", sa.String(80), nullable=False),
    sa.Column("source_category", sa.String(120), nullable=False),
    sa.Column("source_url", sa.Text(), nullable=True),
    sa.Column("file_reference", sa.Text(), nullable=True),
    sa.Column("retrieval_method", sa.String(120), nullable=False),
    sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("checksum", sa.String(128), nullable=True),
    sa.Column("is_official", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    sa.Column("status", sa.String(80), nullable=False),
    sa.Column("staff_notes", sa.Text(), nullable=True),
    sa.Column("metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    *timestamps(),
    schema=SCHEMA,
)

code_titles = sa.Table(
    "code_titles",
    Base.metadata,
    id_column(),
    sa.Column("source_id", UUID(as_uuid=True), nullable=False),
    sa.Column("title_number", sa.String(80), nullable=False),
    sa.Column("title_name", sa.String(500), nullable=False),
    sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
    *timestamps(),
    sa.ForeignKeyConstraint(["source_id"], ["civiccode.code_sources.id"]),
    schema=SCHEMA,
)

code_chapters = sa.Table(
    "code_chapters",
    Base.metadata,
    id_column(),
    sa.Column("title_id", UUID(as_uuid=True), nullable=False),
    sa.Column("chapter_number", sa.String(80), nullable=False),
    sa.Column("chapter_name", sa.String(500), nullable=False),
    sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
    *timestamps(),
    sa.ForeignKeyConstraint(["title_id"], ["civiccode.code_titles.id"]),
    schema=SCHEMA,
)

code_sections = sa.Table(
    "code_sections",
    Base.metadata,
    id_column(),
    sa.Column("chapter_id", UUID(as_uuid=True), nullable=False),
    sa.Column("section_number", sa.String(120), nullable=False),
    sa.Column("section_heading", sa.String(500), nullable=False),
    sa.Column("parent_section_id", UUID(as_uuid=True), nullable=True),
    sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
    *timestamps(),
    sa.ForeignKeyConstraint(["chapter_id"], ["civiccode.code_chapters.id"]),
    sa.ForeignKeyConstraint(["parent_section_id"], ["civiccode.code_sections.id"]),
    schema=SCHEMA,
)

section_versions = sa.Table(
    "section_versions",
    Base.metadata,
    id_column(),
    sa.Column("section_id", UUID(as_uuid=True), nullable=False),
    sa.Column("source_id", UUID(as_uuid=True), nullable=False),
    sa.Column("version_label", sa.String(120), nullable=False),
    sa.Column("body", sa.Text(), nullable=False),
    sa.Column("effective_start", sa.Date(), nullable=False),
    sa.Column("effective_end", sa.Date(), nullable=True),
    sa.Column("adoption_event_id", UUID(as_uuid=True), nullable=True),
    sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    *timestamps(),
    sa.ForeignKeyConstraint(["section_id"], ["civiccode.code_sections.id"]),
    sa.ForeignKeyConstraint(["source_id"], ["civiccode.code_sources.id"]),
    schema=SCHEMA,
)

section_citations = sa.Table(
    "section_citations",
    Base.metadata,
    id_column(),
    sa.Column("section_version_id", UUID(as_uuid=True), nullable=False),
    sa.Column("citation_text", sa.String(500), nullable=False),
    sa.Column("canonical_url", sa.Text(), nullable=True),
    sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
    *timestamps(),
    sa.ForeignKeyConstraint(["section_version_id"], ["civiccode.section_versions.id"]),
    schema=SCHEMA,
)

interpretation_notes = sa.Table(
    "interpretation_notes",
    Base.metadata,
    id_column(),
    sa.Column("section_id", UUID(as_uuid=True), nullable=False),
    sa.Column("note_text", sa.Text(), nullable=False),
    sa.Column("visibility", sa.String(80), nullable=False),
    sa.Column("status", sa.String(80), nullable=False),
    sa.Column("approved_by", sa.String(255), nullable=True),
    sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    *timestamps(),
    sa.ForeignKeyConstraint(["section_id"], ["civiccode.code_sections.id"]),
    schema=SCHEMA,
)

plain_language_summaries = sa.Table(
    "plain_language_summaries",
    Base.metadata,
    id_column(),
    sa.Column("section_version_id", UUID(as_uuid=True), nullable=False),
    sa.Column("summary_text", sa.Text(), nullable=False),
    sa.Column("status", sa.String(80), nullable=False),
    sa.Column("approved_by", sa.String(255), nullable=True),
    sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("language_code", sa.String(20), nullable=False, server_default=sa.text("'en'")),
    *timestamps(),
    sa.ForeignKeyConstraint(["section_version_id"], ["civiccode.section_versions.id"]),
    schema=SCHEMA,
)

code_questions = sa.Table(
    "code_questions",
    Base.metadata,
    id_column(),
    sa.Column("question_text", sa.Text(), nullable=False),
    sa.Column("audience", sa.String(80), nullable=False),
    sa.Column("status", sa.String(80), nullable=False),
    sa.Column("answer_text", sa.Text(), nullable=True),
    sa.Column("citation_payload", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    sa.Column("is_popular", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    *timestamps(),
    schema=SCHEMA,
)

ordinance_events = sa.Table(
    "ordinance_events",
    Base.metadata,
    id_column(),
    sa.Column("external_event_id", sa.String(255), nullable=False),
    sa.Column("civicclerk_meeting_id", sa.String(255), nullable=True),
    sa.Column("civicclerk_agenda_item_id", sa.String(255), nullable=True),
    sa.Column("ordinance_number", sa.String(120), nullable=False),
    sa.Column("title", sa.String(500), nullable=False),
    sa.Column("adopted_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("affected_sections", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    sa.Column("status", sa.String(80), nullable=False),
    sa.Column("source_document_url", sa.Text(), nullable=True),
    sa.Column("source_document_hash", sa.String(128), nullable=True),
    *timestamps(),
    schema=SCHEMA,
)


__all__ = [
    "Base",
    "SCHEMA",
    "code_sources",
    "code_titles",
    "code_chapters",
    "code_sections",
    "section_versions",
    "section_citations",
    "interpretation_notes",
    "plain_language_summaries",
    "code_questions",
    "ordinance_events",
]
