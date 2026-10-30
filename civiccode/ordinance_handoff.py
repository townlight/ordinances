"""CivicClerk ordinance/adoption handoff intake for CivicCode."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Engine, create_engine
from sqlalchemy.dialects.postgresql import JSONB

from civiccode.operational_state import (
    OperationalStateRepository,
    OperationalStateStore,
    operational_record_to_dict,
)


HANDOFF_STATUSES = {"adopted", "pending", "failed"}
CONFLICT_TERMS = ("amend", "amending", "repeal", "repealing", "supersede", "replace")


class OrdinanceHandoffError(ValueError):
    """Validation error with an operator-facing fix path."""

    def __init__(self, message: str, fix: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.message = message
        self.fix = fix
        self.status_code = status_code

    def detail(self) -> dict[str, str]:
        return {"message": self.message, "fix": self.fix}


@dataclass(slots=True)
class OrdinanceEvent:
    event_id: str
    external_event_id: str
    civicclerk_meeting_id: str
    civicclerk_agenda_item_id: str
    ordinance_number: str
    title: str
    status: str
    affected_sections: list[str]
    source_document_url: str
    source_document_hash: str
    ordinance_text: str = ""
    adopted_at: datetime | None = None
    failure_reason: str | None = None
    resolved_section_version_id: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    created_by: str = "unknown"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def handoff_state(self) -> str:
        if self.status == "failed":
            return "failed"
        if self.status == "codified":
            return "codified"
        return "pending_codification"


@dataclass(slots=True)
class HandoffAuditEvent:
    event_id: str
    event_type: str
    actor: str
    target_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class OrdinanceHandoffStore:
    """In-memory CivicClerk handoff store for Milestone 10 API behavior."""

    def __init__(self, *, operational_store: OperationalStateStore | None = None) -> None:
        self._events: dict[str, OrdinanceEvent] = {}
        self._audit_events: list[HandoffAuditEvent] = []
        self._operational_store = operational_store or OperationalStateStore()

    def create_event(self, data: dict[str, Any], *, actor: str) -> OrdinanceEvent:
        status = data.get("status", "pending")
        if status not in HANDOFF_STATUSES:
            raise OrdinanceHandoffError(
                f"Unknown CivicClerk handoff status '{status}'.",
                f"Use one of: {', '.join(sorted(HANDOFF_STATUSES))}.",
            )
        affected_sections = list(data.get("affected_sections", []))
        if not affected_sections:
            raise OrdinanceHandoffError(
                "CivicClerk handoff must identify at least one affected section.",
                "Populate affected_sections with the section numbers touched by the ordinance.",
            )
        for required in [
            "external_event_id",
            "civicclerk_meeting_id",
            "civicclerk_agenda_item_id",
            "ordinance_number",
            "title",
            "source_document_url",
            "source_document_hash",
        ]:
            if not data.get(required):
                raise OrdinanceHandoffError(
                    f"CivicClerk handoff is missing {required}.",
                    f"Include {required} from CivicClerk before sending the handoff.",
                )
        if status == "failed" and not data.get("failure_reason"):
            raise OrdinanceHandoffError(
                "Failed CivicClerk handoffs require a failure_reason.",
                "Explain what failed so staff can repair and resend the handoff.",
            )

        event = OrdinanceEvent(
            event_id=data.get("event_id") or f"ord_{uuid4().hex}",
            external_event_id=data["external_event_id"],
            civicclerk_meeting_id=data["civicclerk_meeting_id"],
            civicclerk_agenda_item_id=data["civicclerk_agenda_item_id"],
            ordinance_number=data["ordinance_number"],
            title=data["title"],
            status=status,
            affected_sections=affected_sections,
            source_document_url=data["source_document_url"],
            source_document_hash=data["source_document_hash"],
            ordinance_text=data.get("ordinance_text", ""),
            adopted_at=data.get("adopted_at"),
            failure_reason=data.get("failure_reason"),
            created_by=actor,
        )
        if event.event_id in self._events:
            raise OrdinanceHandoffError(
                f"CivicClerk ordinance event '{event.event_id}' already exists.",
                "Use a unique event_id or read the existing handoff.",
                status_code=409,
            )
        existing_event = self._find_event_by_external_event_id(event.external_event_id)
        if existing_event:
            if _events_match_for_replay(existing_event, event):
                return existing_event
            raise OrdinanceHandoffError(
                f"CivicClerk event '{event.external_event_id}' has already been accepted with different payload data.",
                (
                    "Read the existing handoff before replaying. If CivicClerk corrected the event, "
                    "send a new external_event_id or reconcile the stored handoff with clerk staff."
                ),
                status_code=409,
            )
        self._events[event.event_id] = event
        self._append_event("civicclerk_handoff_received", actor=actor, target_id=event.event_id)
        if event.status == "failed":
            self._operational_store.record_retry(
                lane="handoff",
                subject_id=event.event_id,
                actor=actor,
                reason=event.failure_reason or "CivicClerk handoff failed.",
                failure={"message": event.failure_reason or "CivicClerk handoff failed."},
            )
        self._operational_store.record_replay(
            lane="handoff",
            subject_id=event.event_id,
            actor=actor,
            status=event.handoff_state,
            payload_hash=event.source_document_hash,
            details={"external_event_id": event.external_event_id, "ordinance_number": event.ordinance_number},
            failure={"message": event.failure_reason} if event.failure_reason else None,
        )
        return event

    def _find_event_by_external_event_id(self, external_event_id: str) -> OrdinanceEvent | None:
        return next(
            (event for event in self._events.values() if event.external_event_id == external_event_id),
            None,
        )

    def warnings_for_section(self, section_number: str) -> list[dict[str, Any]]:
        warnings = []
        for event in self._events.values():
            if section_number not in event.affected_sections:
                continue
            if event.handoff_state == "codified":
                continue
            warnings.append(
                {
                    "source": "CivicClerk",
                    "external_event_id": event.external_event_id,
                    "ordinance_number": event.ordinance_number,
                    "handoff_state": event.handoff_state,
                    "message": (
                        f"CivicClerk ordinance {event.ordinance_number} may affect "
                        f"section {section_number}."
                    ),
                    "fix": (
                        f"Review CivicClerk event {event.external_event_id} before treating "
                        "the codified text as fully current."
                    ),
                    "failure_reason": event.failure_reason,
                }
            )
        return warnings

    def public_warnings_for_section(self, section_number: str) -> list[dict[str, Any]]:
        warnings = []
        for warning in self.warnings_for_section(section_number):
            warnings.append(
                {
                    "source": warning["source"],
                    "ordinance_number": warning["ordinance_number"],
                    "handoff_state": warning["handoff_state"],
                    "message": warning["message"],
                    "fix": (
                        "Ask municipal staff to confirm the ordinance codification status "
                        "before relying on this section as fully current."
                    ),
                }
            )
        return warnings

    def list_events(self) -> list[OrdinanceEvent]:
        return sorted(self._events.values(), key=lambda event: event.created_at)

    def resolve_event(
        self,
        event_id: str,
        *,
        actor: str,
        section_version_id: str,
    ) -> OrdinanceEvent:
        event = self._events.get(event_id)
        if event is None:
            raise OrdinanceHandoffError(
                f"CivicClerk ordinance event '{event_id}' was not found.",
                "Read the handoff list and resolve an existing event.",
                status_code=404,
            )
        if event.status == "failed":
            raise OrdinanceHandoffError(
                "Failed CivicClerk handoffs cannot be marked codified.",
                "Repair and resend the failed handoff before resolving codification.",
                status_code=409,
            )
        event.status = "codified"
        event.resolved_section_version_id = section_version_id
        event.resolved_by = actor
        event.resolved_at = datetime.now(UTC)
        self._append_event("civicclerk_handoff_codified", actor=actor, target_id=event.event_id)
        self._operational_store.record_replay(
            lane="handoff",
            subject_id=event.event_id,
            actor=actor,
            status=event.handoff_state,
            payload_hash=event.source_document_hash,
            details={
                "external_event_id": event.external_event_id,
                "ordinance_number": event.ordinance_number,
                "section_version_id": section_version_id,
            },
        )
        return event

    def audit_events(self) -> list[HandoffAuditEvent]:
        return list(self._audit_events)

    def reset(self) -> None:
        self._events.clear()
        self._audit_events.clear()
        self._operational_store.reset()

    def operational_records(self) -> tuple[dict[str, Any], ...]:
        return tuple(operational_record_to_dict(record) for record in self._operational_store.list_records())

    def _append_event(self, event_type: str, *, actor: str, target_id: str) -> None:
        self._audit_events.append(
            HandoffAuditEvent(
                event_id=f"audit_{uuid4().hex}",
                event_type=event_type,
                actor=actor,
                target_id=target_id,
            )
        )


metadata = sa.MetaData()
json_type = JSONB().with_variant(sa.JSON(), "sqlite")

ordinance_handoff_records = sa.Table(
    "ordinance_handoff_records",
    metadata,
    sa.Column("event_id", sa.String(255), primary_key=True),
    sa.Column("external_event_id", sa.String(255), nullable=False),
    sa.Column("civicclerk_meeting_id", sa.String(255), nullable=False),
    sa.Column("civicclerk_agenda_item_id", sa.String(255), nullable=False),
    sa.Column("ordinance_number", sa.String(120), nullable=False),
    sa.Column("title", sa.Text(), nullable=False),
    sa.Column("status", sa.String(80), nullable=False),
    sa.Column("affected_sections", json_type, nullable=False),
    sa.Column("source_document_url", sa.Text(), nullable=False),
    sa.Column("source_document_hash", sa.String(255), nullable=False),
    sa.Column("ordinance_text", sa.Text(), nullable=False),
    sa.Column("adopted_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("failure_reason", sa.Text(), nullable=True),
    sa.Column("resolved_section_version_id", sa.String(255), nullable=True),
    sa.Column("resolved_by", sa.String(255), nullable=True),
    sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("created_by", sa.String(255), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)

ordinance_handoff_audit_event_records = sa.Table(
    "ordinance_handoff_audit_event_records",
    metadata,
    sa.Column("event_id", sa.String(255), primary_key=True),
    sa.Column("event_type", sa.String(120), nullable=False),
    sa.Column("actor", sa.String(255), nullable=False),
    sa.Column("target_id", sa.String(255), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)


class OrdinanceHandoffRepository(OrdinanceHandoffStore):
    """Database-backed CivicClerk handoff store for Docker/PostgreSQL paths."""

    def __init__(
        self,
        *,
        operational_store: OperationalStateStore | None = None,
        db_url: str | None = None,
        engine: Engine | None = None,
    ) -> None:
        super().__init__(operational_store=operational_store or OperationalStateRepository(db_url=db_url, engine=engine))
        base_engine = engine or create_engine(db_url or "sqlite+pysqlite:///:memory:", future=True)
        if base_engine.dialect.name == "sqlite":
            self.engine = base_engine.execution_options(schema_translate_map={"civiccode": None})
        else:
            self.engine = base_engine
            with self.engine.begin() as connection:
                connection.execute(sa.text("CREATE SCHEMA IF NOT EXISTS civiccode"))
        metadata.create_all(self.engine)
        self._load()

    def create_event(self, data: dict[str, Any], *, actor: str) -> OrdinanceEvent:
        existing_event_ids = set(self._events)
        event = super().create_event(data, actor=actor)
        if event.event_id in existing_event_ids:
            return event
        with self.engine.begin() as connection:
            connection.execute(ordinance_handoff_records.insert().values(**event_to_record(event)))
        return event

    def resolve_event(
        self,
        event_id: str,
        *,
        actor: str,
        section_version_id: str,
    ) -> OrdinanceEvent:
        event = super().resolve_event(event_id, actor=actor, section_version_id=section_version_id)
        with self.engine.begin() as connection:
            connection.execute(
                ordinance_handoff_records.update()
                .where(ordinance_handoff_records.c.event_id == event.event_id)
                .values(
                    status=event.status,
                    resolved_section_version_id=event.resolved_section_version_id,
                    resolved_by=event.resolved_by,
                    resolved_at=event.resolved_at,
                )
            )
        return event

    def reset(self) -> None:
        super().reset()
        with self.engine.begin() as connection:
            connection.execute(ordinance_handoff_audit_event_records.delete())
            connection.execute(ordinance_handoff_records.delete())

    def _append_event(self, event_type: str, *, actor: str, target_id: str) -> None:
        super()._append_event(event_type, actor=actor, target_id=target_id)
        event = self._audit_events[-1]
        with self.engine.begin() as connection:
            connection.execute(ordinance_handoff_audit_event_records.insert().values(**audit_event_to_record(event)))

    def _load(self) -> None:
        with self.engine.begin() as connection:
            for row in connection.execute(sa.select(ordinance_handoff_records)).mappings():
                event = event_from_record(row)
                self._events[event.event_id] = event
            for row in connection.execute(sa.select(ordinance_handoff_audit_event_records)).mappings():
                self._audit_events.append(audit_event_from_record(row))


def event_to_record(event: OrdinanceEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "external_event_id": event.external_event_id,
        "civicclerk_meeting_id": event.civicclerk_meeting_id,
        "civicclerk_agenda_item_id": event.civicclerk_agenda_item_id,
        "ordinance_number": event.ordinance_number,
        "title": event.title,
        "status": event.status,
        "affected_sections": event.affected_sections,
        "source_document_url": event.source_document_url,
        "source_document_hash": event.source_document_hash,
        "ordinance_text": event.ordinance_text,
        "adopted_at": event.adopted_at,
        "failure_reason": event.failure_reason,
        "resolved_section_version_id": event.resolved_section_version_id,
        "resolved_by": event.resolved_by,
        "resolved_at": event.resolved_at,
        "created_by": event.created_by,
        "created_at": event.created_at,
    }


def event_from_record(row: Any) -> OrdinanceEvent:
    return OrdinanceEvent(
        event_id=row["event_id"],
        external_event_id=row["external_event_id"],
        civicclerk_meeting_id=row["civicclerk_meeting_id"],
        civicclerk_agenda_item_id=row["civicclerk_agenda_item_id"],
        ordinance_number=row["ordinance_number"],
        title=row["title"],
        status=row["status"],
        affected_sections=list(row["affected_sections"]),
        source_document_url=row["source_document_url"],
        source_document_hash=row["source_document_hash"],
        ordinance_text=row["ordinance_text"],
        adopted_at=row["adopted_at"],
        failure_reason=row["failure_reason"],
        resolved_section_version_id=row.get("resolved_section_version_id"),
        resolved_by=row.get("resolved_by"),
        resolved_at=row.get("resolved_at"),
        created_by=row["created_by"],
        created_at=row["created_at"],
    )


def _events_match_for_replay(existing: OrdinanceEvent, incoming: OrdinanceEvent) -> bool:
    existing_record = event_to_record(existing)
    incoming_record = event_to_record(incoming)
    for generated_field in ("event_id", "created_by", "created_at"):
        existing_record.pop(generated_field)
        incoming_record.pop(generated_field)
    return existing_record == incoming_record


def audit_event_to_record(event: HandoffAuditEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "actor": event.actor,
        "target_id": event.target_id,
        "created_at": event.created_at,
    }


def audit_event_from_record(row: Any) -> HandoffAuditEvent:
    return HandoffAuditEvent(
        event_id=row["event_id"],
        event_type=row["event_type"],
        actor=row["actor"],
        target_id=row["target_id"],
        created_at=row["created_at"],
    )


def event_to_dict(event: OrdinanceEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "external_event_id": event.external_event_id,
        "ordinance_number": event.ordinance_number,
        "title": event.title,
        "status": event.status,
        "handoff_state": event.handoff_state,
        "affected_sections": event.affected_sections,
        "source_document_url": event.source_document_url,
        "source_document_hash": event.source_document_hash,
        "failure_reason": event.failure_reason,
        "resolution": {
            "section_version_id": event.resolved_section_version_id,
            "resolved_by": event.resolved_by,
            "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None,
        }
        if event.handoff_state == "codified"
        else None,
        "provenance": {
            "civicclerk_meeting_id": event.civicclerk_meeting_id,
            "civicclerk_agenda_item_id": event.civicclerk_agenda_item_id,
        },
        "likely_conflicts": likely_conflicts(event),
        "code_answer_behavior": "not_available",
    }


def likely_conflicts(event: OrdinanceEvent) -> list[dict[str, str]]:
    lowered = f"{event.title} {event.ordinance_text}".lower()
    has_conflict_term = any(term in lowered for term in CONFLICT_TERMS)
    conflicts = []
    for section_number in event.affected_sections:
        if has_conflict_term or section_number.lower() in lowered:
            conflicts.append(
                {
                    "section_number": section_number,
                    "trigger": "ordinance_text_or_title_references_existing_section",
                    "source_event_id": event.external_event_id,
                }
            )
    return conflicts


def handoff_audit_event_to_dict(event: HandoffAuditEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "actor": event.actor,
        "target_id": event.target_id,
        "created_at": event.created_at.isoformat(),
    }
