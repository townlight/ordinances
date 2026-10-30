"""Staff-approved non-authoritative summaries for CivicCode."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Engine, create_engine


SUMMARY_STATUSES = {"draft", "approved", "retired"}


class PlainLanguageSummaryError(ValueError):
    """Validation error with an operator-facing fix path."""

    def __init__(self, message: str, fix: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.message = message
        self.fix = fix
        self.status_code = status_code

    def detail(self) -> dict[str, str]:
        return {"message": self.message, "fix": self.fix}


@dataclass(slots=True)
class PlainLanguageSummary:
    summary_id: str
    section_id: str
    section_version_id: str
    summary_text: str
    status: str
    language_code: str = "en"
    created_by: str = "unknown"
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def public_visible(self) -> bool:
        return self.status == "approved"


@dataclass(slots=True)
class SummaryAuditEvent:
    event_id: str
    event_type: str
    actor: str
    section_id: str
    target_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class PlainLanguageSummaryStore:
    """In-memory summary and audit store for the Milestone 9 API."""

    def __init__(self) -> None:
        self._summaries: dict[str, PlainLanguageSummary] = {}
        self._audit_events: list[SummaryAuditEvent] = []

    def create_summary(
        self,
        section_id: str,
        data: dict[str, Any],
        *,
        actor: str,
    ) -> PlainLanguageSummary:
        status = data.get("status", "draft")
        if status not in SUMMARY_STATUSES:
            raise PlainLanguageSummaryError(
                f"Unknown plain-language summary status '{status}'.",
                f"Use one of: {', '.join(sorted(SUMMARY_STATUSES))}.",
            )
        if status == "approved":
            raise PlainLanguageSummaryError(
                "Plain-language summaries must be approved through the approval endpoint.",
                "Create the summary as draft first, then approve it after staff review.",
            )
        summary = PlainLanguageSummary(
            summary_id=data.get("summary_id") or f"summary_{uuid4().hex}",
            section_id=section_id,
            section_version_id=data["section_version_id"],
            summary_text=data["summary_text"],
            status=status,
            language_code=data.get("language_code", "en"),
            created_by=actor,
        )
        if summary.summary_id in self._summaries:
            raise PlainLanguageSummaryError(
                f"Plain-language summary '{summary.summary_id}' already exists.",
                "Use a unique summary_id or read the existing summary.",
                status_code=409,
            )
        self._summaries[summary.summary_id] = summary
        self._append_event(
            "plain_language_summary_created",
            actor=actor,
            section_id=section_id,
            target_id=summary.summary_id,
        )
        return summary

    def approve_summary(self, summary_id: str, *, actor: str) -> PlainLanguageSummary:
        summary = self.get_summary(summary_id)
        if summary.status == "retired":
            raise PlainLanguageSummaryError(
                f"Plain-language summary '{summary_id}' is retired.",
                "Create a new draft summary for staff review instead of approving a retired one.",
                status_code=409,
            )
        summary.status = "approved"
        summary.approved_by = actor
        summary.approved_at = datetime.now(UTC)
        self._append_event(
            "plain_language_summary_approved",
            actor=actor,
            section_id=summary.section_id,
            target_id=summary.summary_id,
        )
        return summary

    def list_for_section(
        self,
        section_id: str,
        *,
        include_unapproved: bool = False,
    ) -> list[PlainLanguageSummary]:
        summaries = [
            summary
            for summary in self._summaries.values()
            if summary.section_id == section_id
            and (include_unapproved or summary.public_visible)
        ]
        return sorted(summaries, key=lambda summary: summary.created_at)

    def list_all(self, *, include_unapproved: bool = False) -> list[PlainLanguageSummary]:
        summaries = [
            summary
            for summary in self._summaries.values()
            if include_unapproved or summary.public_visible
        ]
        return sorted(summaries, key=lambda summary: summary.created_at)

    def get_summary(self, summary_id: str) -> PlainLanguageSummary:
        try:
            return self._summaries[summary_id]
        except KeyError as exc:
            raise PlainLanguageSummaryError(
                f"Plain-language summary '{summary_id}' was not found.",
                "Create the summary before trying to approve or read it.",
                status_code=404,
            ) from exc

    def audit_events(self) -> list[SummaryAuditEvent]:
        return list(self._audit_events)

    def reset(self) -> None:
        self._summaries.clear()
        self._audit_events.clear()

    def _append_event(
        self,
        event_type: str,
        *,
        actor: str,
        section_id: str,
        target_id: str,
    ) -> None:
        self._audit_events.append(
            SummaryAuditEvent(
                event_id=f"audit_{uuid4().hex}",
                event_type=event_type,
                actor=actor,
                section_id=section_id,
                target_id=target_id,
            )
        )


metadata = sa.MetaData()

plain_language_summary_records = sa.Table(
    "plain_language_summary_records",
    metadata,
    sa.Column("summary_id", sa.String(255), primary_key=True),
    sa.Column("section_id", sa.String(255), nullable=False),
    sa.Column("section_version_id", sa.String(255), nullable=False),
    sa.Column("summary_text", sa.Text(), nullable=False),
    sa.Column("status", sa.String(80), nullable=False),
    sa.Column("language_code", sa.String(40), nullable=False),
    sa.Column("created_by", sa.String(255), nullable=False),
    sa.Column("approved_by", sa.String(255), nullable=True),
    sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)

plain_language_summary_audit_event_records = sa.Table(
    "plain_language_summary_audit_event_records",
    metadata,
    sa.Column("event_id", sa.String(255), primary_key=True),
    sa.Column("event_type", sa.String(120), nullable=False),
    sa.Column("actor", sa.String(255), nullable=False),
    sa.Column("section_id", sa.String(255), nullable=False),
    sa.Column("target_id", sa.String(255), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)


class PlainLanguageSummaryRepository(PlainLanguageSummaryStore):
    """Database-backed plain-language summaries and audit events."""

    def __init__(self, *, db_url: str | None = None, engine: Engine | None = None) -> None:
        super().__init__()
        base_engine = engine or create_engine(db_url or "sqlite+pysqlite:///:memory:", future=True)
        if base_engine.dialect.name == "sqlite":
            self.engine = base_engine.execution_options(schema_translate_map={"civiccode": None})
        else:
            self.engine = base_engine
            with self.engine.begin() as connection:
                connection.execute(sa.text("CREATE SCHEMA IF NOT EXISTS civiccode"))
        metadata.create_all(self.engine)
        self._load()

    def create_summary(
        self,
        section_id: str,
        data: dict[str, Any],
        *,
        actor: str,
    ) -> PlainLanguageSummary:
        summary = super().create_summary(section_id, data, actor=actor)
        with self.engine.begin() as connection:
            connection.execute(plain_language_summary_records.insert().values(**summary_to_record(summary)))
        return summary

    def approve_summary(self, summary_id: str, *, actor: str) -> PlainLanguageSummary:
        summary = super().approve_summary(summary_id, actor=actor)
        with self.engine.begin() as connection:
            connection.execute(
                plain_language_summary_records.update()
                .where(plain_language_summary_records.c.summary_id == summary.summary_id)
                .values(
                    status=summary.status,
                    approved_by=summary.approved_by,
                    approved_at=summary.approved_at,
                    updated_at=datetime.now(UTC),
                )
            )
        return summary

    def reset(self) -> None:
        super().reset()
        with self.engine.begin() as connection:
            connection.execute(plain_language_summary_audit_event_records.delete())
            connection.execute(plain_language_summary_records.delete())

    def _append_event(
        self,
        event_type: str,
        *,
        actor: str,
        section_id: str,
        target_id: str,
    ) -> None:
        super()._append_event(event_type, actor=actor, section_id=section_id, target_id=target_id)
        event = self._audit_events[-1]
        with self.engine.begin() as connection:
            connection.execute(
                plain_language_summary_audit_event_records.insert().values(
                    **summary_audit_event_to_record(event)
                )
            )

    def _load(self) -> None:
        with self.engine.begin() as connection:
            for row in connection.execute(sa.select(plain_language_summary_records)).mappings():
                summary = summary_from_record(row)
                self._summaries[summary.summary_id] = summary
            for row in connection.execute(sa.select(plain_language_summary_audit_event_records)).mappings():
                self._audit_events.append(summary_audit_event_from_record(row))


def summary_to_record(summary: PlainLanguageSummary) -> dict[str, Any]:
    return {
        "summary_id": summary.summary_id,
        "section_id": summary.section_id,
        "section_version_id": summary.section_version_id,
        "summary_text": summary.summary_text,
        "status": summary.status,
        "language_code": summary.language_code,
        "created_by": summary.created_by,
        "approved_by": summary.approved_by,
        "approved_at": summary.approved_at,
        "created_at": summary.created_at,
        "updated_at": summary.approved_at or summary.created_at,
    }


def summary_from_record(row: Any) -> PlainLanguageSummary:
    return PlainLanguageSummary(
        summary_id=row["summary_id"],
        section_id=row["section_id"],
        section_version_id=row["section_version_id"],
        summary_text=row["summary_text"],
        status=row["status"],
        language_code=row["language_code"],
        created_by=row["created_by"],
        approved_by=row["approved_by"],
        approved_at=row["approved_at"],
        created_at=row["created_at"],
    )


def summary_audit_event_to_record(event: SummaryAuditEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "actor": event.actor,
        "section_id": event.section_id,
        "target_id": event.target_id,
        "created_at": event.created_at,
    }


def summary_audit_event_from_record(row: Any) -> SummaryAuditEvent:
    return SummaryAuditEvent(
        event_id=row["event_id"],
        event_type=row["event_type"],
        actor=row["actor"],
        section_id=row["section_id"],
        target_id=row["target_id"],
        created_at=row["created_at"],
    )


def summary_to_staff_dict(summary: PlainLanguageSummary) -> dict[str, Any]:
    return {
        "summary_id": summary.summary_id,
        "section_id": summary.section_id,
        "section_version_id": summary.section_version_id,
        "summary_text": summary.summary_text,
        "status": summary.status,
        "language_code": summary.language_code,
        "authority": "non_authoritative_explanation",
        "warning": "Plain-language summaries are not law.",
        "public_visible": summary.public_visible,
        "created_by": summary.created_by,
        "approved_by": summary.approved_by,
        "approved_at": summary.approved_at.isoformat() if summary.approved_at else None,
        "created_at": summary.created_at.isoformat(),
    }


def summary_to_public_dict(
    summary: PlainLanguageSummary,
    *,
    authoritative_section: dict[str, Any],
    authoritative_text: str,
) -> dict[str, Any]:
    return {
        "summary_id": summary.summary_id,
        "section_id": summary.section_id,
        "section_version_id": summary.section_version_id,
        "summary_text": summary.summary_text,
        "language_code": summary.language_code,
        "authority": "non_authoritative_explanation",
        "warning": "Plain-language summaries are not law.",
        "authoritative_section": authoritative_section,
        "authoritative_text": authoritative_text,
    }


def summary_audit_event_to_dict(event: SummaryAuditEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "actor": event.actor,
        "section_id": event.section_id,
        "target_id": event.target_id,
        "created_at": event.created_at.isoformat(),
    }
