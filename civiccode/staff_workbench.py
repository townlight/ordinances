"""Staff-only interpretation notes and audit events for CivicCode."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Engine, create_engine


NOTE_STATUSES = {"draft", "approved", "retired"}


class StaffWorkbenchError(ValueError):
    """Validation error with an operator-facing fix path."""

    def __init__(self, message: str, fix: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.message = message
        self.fix = fix
        self.status_code = status_code

    def detail(self) -> dict[str, str]:
        return {"message": self.message, "fix": self.fix}


@dataclass(slots=True)
class InterpretationNote:
    note_id: str
    section_id: str
    note_text: str
    status: str
    visibility: str = "staff_only"
    created_by: str = "unknown"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class AuditEvent:
    event_id: str
    event_type: str
    actor: str
    section_id: str | None = None
    target_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class StaffWorkbenchStore:
    """In-memory staff note and audit store for the Milestone 8 API."""

    def __init__(self) -> None:
        self._notes: dict[str, InterpretationNote] = {}
        self._audit_events: list[AuditEvent] = []

    def create_note(self, section_id: str, data: dict[str, Any], *, actor: str) -> InterpretationNote:
        status = data.get("status", "draft")
        if status not in NOTE_STATUSES:
            raise StaffWorkbenchError(
                f"Unknown interpretation note status '{status}'.",
                f"Use one of: {', '.join(sorted(NOTE_STATUSES))}.",
            )
        note = InterpretationNote(
            note_id=data.get("note_id") or f"note_{uuid4().hex}",
            section_id=section_id,
            note_text=data["note_text"],
            status=status,
            created_by=actor,
        )
        if note.note_id in self._notes:
            raise StaffWorkbenchError(
                f"Interpretation note '{note.note_id}' already exists.",
                "Use a unique note_id or read the existing note.",
                status_code=409,
            )
        self._notes[note.note_id] = note
        self._append_event(
            "interpretation_note_created",
            actor=actor,
            section_id=section_id,
            target_id=note.note_id,
        )
        return note

    def list_notes(self, section_id: str) -> list[InterpretationNote]:
        return sorted(
            [note for note in self._notes.values() if note.section_id == section_id],
            key=lambda note: note.created_at,
        )

    def audit_events(self) -> list[AuditEvent]:
        return list(self._audit_events)

    def reset(self) -> None:
        self._notes.clear()
        self._audit_events.clear()

    def _append_event(
        self,
        event_type: str,
        *,
        actor: str,
        section_id: str | None = None,
        target_id: str | None = None,
    ) -> None:
        self._audit_events.append(
            AuditEvent(
                event_id=f"audit_{uuid4().hex}",
                event_type=event_type,
                actor=actor,
                section_id=section_id,
                target_id=target_id,
            )
        )


metadata = sa.MetaData()

staff_interpretation_note_records = sa.Table(
    "staff_interpretation_note_records",
    metadata,
    sa.Column("note_id", sa.String(255), primary_key=True),
    sa.Column("section_id", sa.String(255), nullable=False),
    sa.Column("note_text", sa.Text(), nullable=False),
    sa.Column("status", sa.String(80), nullable=False),
    sa.Column("visibility", sa.String(80), nullable=False),
    sa.Column("created_by", sa.String(255), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)

staff_workbench_audit_event_records = sa.Table(
    "staff_workbench_audit_event_records",
    metadata,
    sa.Column("event_id", sa.String(255), primary_key=True),
    sa.Column("event_type", sa.String(120), nullable=False),
    sa.Column("actor", sa.String(255), nullable=False),
    sa.Column("section_id", sa.String(255), nullable=True),
    sa.Column("target_id", sa.String(255), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)


class StaffWorkbenchRepository(StaffWorkbenchStore):
    """Database-backed staff notes and audit trail for Docker/PostgreSQL paths."""

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

    def create_note(self, section_id: str, data: dict[str, Any], *, actor: str) -> InterpretationNote:
        note = super().create_note(section_id, data, actor=actor)
        with self.engine.begin() as connection:
            connection.execute(staff_interpretation_note_records.insert().values(**note_to_record(note)))
        return note

    def reset(self) -> None:
        super().reset()
        with self.engine.begin() as connection:
            connection.execute(staff_workbench_audit_event_records.delete())
            connection.execute(staff_interpretation_note_records.delete())

    def _append_event(
        self,
        event_type: str,
        *,
        actor: str,
        section_id: str | None = None,
        target_id: str | None = None,
    ) -> None:
        super()._append_event(event_type, actor=actor, section_id=section_id, target_id=target_id)
        event = self._audit_events[-1]
        with self.engine.begin() as connection:
            connection.execute(staff_workbench_audit_event_records.insert().values(**audit_event_to_record(event)))

    def _load(self) -> None:
        with self.engine.begin() as connection:
            for row in connection.execute(sa.select(staff_interpretation_note_records)).mappings():
                note = note_from_record(row)
                self._notes[note.note_id] = note
            for row in connection.execute(sa.select(staff_workbench_audit_event_records)).mappings():
                self._audit_events.append(audit_event_from_record(row))


def note_to_record(note: InterpretationNote) -> dict[str, Any]:
    return {
        "note_id": note.note_id,
        "section_id": note.section_id,
        "note_text": note.note_text,
        "status": note.status,
        "visibility": note.visibility,
        "created_by": note.created_by,
        "created_at": note.created_at,
    }


def note_from_record(row: Any) -> InterpretationNote:
    return InterpretationNote(
        note_id=row["note_id"],
        section_id=row["section_id"],
        note_text=row["note_text"],
        status=row["status"],
        visibility=row["visibility"],
        created_by=row["created_by"],
        created_at=row["created_at"],
    )


def audit_event_to_record(event: AuditEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "actor": event.actor,
        "section_id": event.section_id,
        "target_id": event.target_id,
        "created_at": event.created_at,
    }


def audit_event_from_record(row: Any) -> AuditEvent:
    return AuditEvent(
        event_id=row["event_id"],
        event_type=row["event_type"],
        actor=row["actor"],
        section_id=row["section_id"],
        target_id=row["target_id"],
        created_at=row["created_at"],
    )


def note_to_staff_dict(note: InterpretationNote) -> dict[str, Any]:
    return {
        "note_id": note.note_id,
        "section_id": note.section_id,
        "note_text": note.note_text,
        "visibility": note.visibility,
        "status": note.status,
        "created_by": note.created_by,
        "created_at": note.created_at.isoformat(),
    }


def audit_event_to_dict(event: AuditEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "actor": event.actor,
        "section_id": event.section_id,
        "target_id": event.target_id,
        "created_at": event.created_at.isoformat(),
    }
