"""Durable operational retry, replay, and cursor records for CivicCode."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Engine, create_engine
from sqlalchemy.dialects.postgresql import JSONB


OPERATIONAL_LANES = {"handoff", "import", "sync"}
OPERATIONAL_RECORD_TYPES = {"retry_queue", "replay_record", "delta_cursor"}


@dataclass(slots=True)
class OperationalStateRecord:
    """One operator-visible operational state record."""

    record_id: str
    lane: str
    record_type: str
    subject_id: str
    status: str
    actor: str = "system"
    attempt_count: int = 0
    next_attempt_at: datetime | None = None
    cursor_key: str | None = None
    cursor_value: str | None = None
    replay_of: str | None = None
    payload_hash: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    failure: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class OperationalStateStore:
    """In-memory operational state store for local development."""

    def __init__(self) -> None:
        self._records: dict[str, OperationalStateRecord] = {}

    def record_retry(
        self,
        *,
        lane: str,
        subject_id: str,
        actor: str,
        reason: str,
        next_attempt_at: datetime | None = None,
        attempt_count: int = 0,
        failure: dict[str, Any] | None = None,
    ) -> OperationalStateRecord:
        record = OperationalStateRecord(
            record_id=f"retry_{lane}_{subject_id}_{uuid4().hex}",
            lane=lane,
            record_type="retry_queue",
            subject_id=subject_id,
            status="queued",
            actor=actor,
            attempt_count=attempt_count,
            next_attempt_at=next_attempt_at,
            details={"reason": reason},
            failure=failure,
        )
        return self._save(record)

    def record_replay(
        self,
        *,
        lane: str,
        subject_id: str,
        actor: str,
        status: str,
        replay_of: str | None = None,
        payload_hash: str | None = None,
        details: dict[str, Any] | None = None,
        failure: dict[str, Any] | None = None,
    ) -> OperationalStateRecord:
        record = OperationalStateRecord(
            record_id=f"replay_{lane}_{subject_id}_{uuid4().hex}",
            lane=lane,
            record_type="replay_record",
            subject_id=subject_id,
            status=status,
            actor=actor,
            replay_of=replay_of,
            payload_hash=payload_hash,
            details=details or {},
            failure=failure,
        )
        return self._save(record)

    def record_cursor(
        self,
        *,
        lane: str,
        subject_id: str,
        cursor_key: str,
        cursor_value: str,
        actor: str = "system",
        details: dict[str, Any] | None = None,
    ) -> OperationalStateRecord:
        record_id = f"cursor_{lane}_{subject_id}_{cursor_key}"
        existing = self._records.get(record_id)
        created_at = existing.created_at if existing else datetime.now(UTC)
        record = OperationalStateRecord(
            record_id=record_id,
            lane=lane,
            record_type="delta_cursor",
            subject_id=subject_id,
            status="current",
            actor=actor,
            cursor_key=cursor_key,
            cursor_value=cursor_value,
            details=details or {},
            created_at=created_at,
            updated_at=datetime.now(UTC),
        )
        return self._save(record)

    def list_records(
        self,
        *,
        lane: str | None = None,
        record_type: str | None = None,
        subject_id: str | None = None,
    ) -> tuple[OperationalStateRecord, ...]:
        records = self._records.values()
        if lane is not None:
            records = [record for record in records if record.lane == lane]
        if record_type is not None:
            records = [record for record in records if record.record_type == record_type]
        if subject_id is not None:
            records = [record for record in records if record.subject_id == subject_id]
        return tuple(
            sorted(records, key=lambda record: (_as_aware_utc(record.created_at), record.record_id))
        )

    def reset(self) -> None:
        self._records.clear()

    def _save(self, record: OperationalStateRecord) -> OperationalStateRecord:
        _validate_operational_record(record)
        self._records[record.record_id] = record
        return record


metadata = sa.MetaData()
json_type = JSONB().with_variant(sa.JSON(), "sqlite")

operational_state_records = sa.Table(
    "operational_state_records",
    metadata,
    sa.Column("record_id", sa.String(255), primary_key=True),
    sa.Column("lane", sa.String(80), nullable=False),
    sa.Column("record_type", sa.String(80), nullable=False),
    sa.Column("subject_id", sa.String(255), nullable=False),
    sa.Column("status", sa.String(80), nullable=False),
    sa.Column("actor", sa.String(255), nullable=False),
    sa.Column("attempt_count", sa.Integer(), nullable=False),
    sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("cursor_key", sa.String(120), nullable=True),
    sa.Column("cursor_value", sa.String(255), nullable=True),
    sa.Column("replay_of", sa.String(255), nullable=True),
    sa.Column("payload_hash", sa.String(255), nullable=True),
    sa.Column("details", json_type, nullable=False),
    sa.Column("failure", json_type, nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)


class OperationalStateRepository(OperationalStateStore):
    """Database-backed operational state for Docker/PostgreSQL paths."""

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

    def reset(self) -> None:
        super().reset()
        with self.engine.begin() as connection:
            connection.execute(operational_state_records.delete())

    def _save(self, record: OperationalStateRecord) -> OperationalStateRecord:
        record = super()._save(record)
        with self.engine.begin() as connection:
            connection.execute(
                operational_state_records.delete().where(
                    operational_state_records.c.record_id == record.record_id
                )
            )
            connection.execute(operational_state_records.insert().values(**operational_record_to_row(record)))
        return record

    def _load(self) -> None:
        with self.engine.begin() as connection:
            for row in connection.execute(sa.select(operational_state_records)).mappings():
                record = operational_record_from_row(row)
                self._records[record.record_id] = record


def operational_record_to_dict(record: OperationalStateRecord) -> dict[str, Any]:
    return {
        "record_id": record.record_id,
        "lane": record.lane,
        "record_type": record.record_type,
        "subject_id": record.subject_id,
        "status": record.status,
        "actor": record.actor,
        "attempt_count": record.attempt_count,
        "next_attempt_at": record.next_attempt_at.isoformat() if record.next_attempt_at else None,
        "cursor_key": record.cursor_key,
        "cursor_value": record.cursor_value,
        "replay_of": record.replay_of,
        "payload_hash": record.payload_hash,
        "details": record.details,
        "failure": record.failure,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
    }


def operational_record_to_row(record: OperationalStateRecord) -> dict[str, Any]:
    return {
        "record_id": record.record_id,
        "lane": record.lane,
        "record_type": record.record_type,
        "subject_id": record.subject_id,
        "status": record.status,
        "actor": record.actor,
        "attempt_count": record.attempt_count,
        "next_attempt_at": record.next_attempt_at,
        "cursor_key": record.cursor_key,
        "cursor_value": record.cursor_value,
        "replay_of": record.replay_of,
        "payload_hash": record.payload_hash,
        "details": record.details,
        "failure": record.failure,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def operational_record_from_row(row: Any) -> OperationalStateRecord:
    return OperationalStateRecord(
        record_id=row["record_id"],
        lane=row["lane"],
        record_type=row["record_type"],
        subject_id=row["subject_id"],
        status=row["status"],
        actor=row["actor"],
        attempt_count=row["attempt_count"],
        next_attempt_at=_as_optional_aware_utc(row["next_attempt_at"]),
        cursor_key=row["cursor_key"],
        cursor_value=row["cursor_value"],
        replay_of=row["replay_of"],
        payload_hash=row["payload_hash"],
        details=dict(row["details"] or {}),
        failure=dict(row["failure"]) if row["failure"] else None,
        created_at=_as_aware_utc(row["created_at"]),
        updated_at=_as_aware_utc(row["updated_at"]),
    )


def _as_optional_aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_aware_utc(value)


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _validate_operational_record(record: OperationalStateRecord) -> None:
    if record.lane not in OPERATIONAL_LANES:
        raise ValueError(f"Unknown operational lane {record.lane!r}.")
    if record.record_type not in OPERATIONAL_RECORD_TYPES:
        raise ValueError(f"Unknown operational record_type {record.record_type!r}.")


__all__ = [
    "OperationalStateRecord",
    "OperationalStateRepository",
    "OperationalStateStore",
    "operational_record_to_dict",
]
