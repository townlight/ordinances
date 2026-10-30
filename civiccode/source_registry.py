"""Official source registry rules for CivicCode Milestone 3."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Engine, create_engine


SOURCE_TYPES = {
    "municode",
    "american_legal",
    "code_publishing",
    "general_code",
    "official_xml_export",
    "official_docx_export",
    "official_file_drop",
    "official_web_scrape",
    "official_web_export",
}

SOURCE_CATEGORIES = {
    "municipal_code": {"public_visible": True, "search_eligible": True},
    "administrative_regulations": {"public_visible": True, "search_eligible": True},
    "resolutions": {"public_visible": True, "search_eligible": True},
    "policies": {"public_visible": True, "search_eligible": True},
    "adopted_ordinances": {"public_visible": True, "search_eligible": True},
    "historical_versions": {"public_visible": True, "search_eligible": True},
    "approved_summaries": {"public_visible": True, "search_eligible": True},
    "internal_staff_notes": {"public_visible": False, "search_eligible": False},
}

SOURCE_STATES = {"draft", "active", "stale", "superseded", "failed"}

SOURCE_TRANSITIONS = {
    "draft": {"active", "stale", "superseded", "failed"},
    "active": {"stale", "superseded", "failed"},
    "stale": {"active", "superseded", "failed"},
    "failed": {"draft", "superseded"},
    "superseded": set(),
}

ACTIONABLE_STATE_MESSAGES = {
    "stale": {
        "warning": "This source is stale and should not be used for new code answers.",
        "fix": "Refresh the source from the official publisher, then transition it back to active.",
    },
    "failed": {
        "warning": "This source failed ingestion or verification.",
        "fix": "Review the failure note, correct the retrieval problem, and transition it to draft.",
    },
}


class SourceRegistryError(ValueError):
    """Validation error with an operator-facing fix path."""

    def __init__(self, message: str, fix: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.message = message
        self.fix = fix
        self.status_code = status_code

    def detail(self) -> dict[str, str]:
        return {"message": self.message, "fix": self.fix}


@dataclass(slots=True)
class CodeSource:
    """Runtime representation of an official or explicitly non-official source."""

    source_id: str
    name: str
    publisher: str
    source_type: str
    source_category: str
    source_url: str | None = None
    file_reference: str | None = None
    retrieved_at: datetime | None = None
    retrieval_method: str | None = None
    checksum: str | None = None
    source_owner: str | None = None
    is_official: bool = True
    official_status_note: str | None = None
    status: str = "draft"
    staff_notes: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def public_visible(self) -> bool:
        return SOURCE_CATEGORIES[self.source_category]["public_visible"]

    @property
    def search_eligible(self) -> bool:
        return self.status == "active" and SOURCE_CATEGORIES[self.source_category]["search_eligible"]


class SourceRegistryStore:
    """In-memory source registry for Milestone 3 API behavior."""

    def __init__(self) -> None:
        self._sources: dict[str, CodeSource] = {}

    def create(self, data: dict[str, Any]) -> CodeSource:
        source = CodeSource(
            source_id=data.get("source_id") or f"src_{uuid4().hex}",
            name=data["name"],
            publisher=data["publisher"],
            source_type=data["source_type"],
            source_category=data["source_category"],
            source_url=data.get("source_url"),
            file_reference=data.get("file_reference"),
            retrieved_at=_coerce_datetime(data.get("retrieved_at")),
            retrieval_method=data.get("retrieval_method"),
            checksum=data.get("checksum"),
            source_owner=data.get("source_owner"),
            is_official=data.get("is_official", True),
            official_status_note=data.get("official_status_note"),
            status=data.get("status", "draft"),
            staff_notes=data.get("staff_notes"),
        )
        validate_source(source)
        if source.source_id in self._sources:
            raise SourceRegistryError(
                f"Source '{source.source_id}' already exists.",
                "Use a unique source_id or update the existing source instead.",
                status_code=409,
            )
        self._sources[source.source_id] = source
        return source

    def get(self, source_id: str) -> CodeSource:
        try:
            return self._sources[source_id]
        except KeyError as exc:
            raise SourceRegistryError(
                f"Source '{source_id}' was not found.",
                "Create the source first or check the source_id in the request URL.",
                status_code=404,
            ) from exc

    def list_sources(self, *, include_staff_only: bool = False) -> list[CodeSource]:
        sources = sorted(self._sources.values(), key=lambda source: source.created_at)
        if include_staff_only:
            return sources
        return [source for source in sources if source.public_visible]

    def transition(
        self,
        source_id: str,
        to_status: str,
        *,
        actor: str,
        reason: str,
    ) -> CodeSource:
        source = self.get(source_id)
        if not actor.strip():
            raise SourceRegistryError(
                "Source transition requires an actor.",
                "Provide the staff email or service account making the transition.",
            )
        if not reason.strip():
            raise SourceRegistryError(
                "Source transition requires a reason.",
                "Explain why this source state is changing.",
            )
        validate_transition(source.status, to_status)
        candidate = replace(source, status=to_status)
        validate_source(candidate)
        source.status = to_status
        source.updated_at = datetime.now(UTC)
        return source

    def reset(self) -> None:
        self._sources.clear()


metadata = sa.MetaData()

source_registry_records = sa.Table(
    "source_registry_records",
    metadata,
    sa.Column("source_id", sa.String(255), primary_key=True),
    sa.Column("name", sa.String(255), nullable=False),
    sa.Column("publisher", sa.String(255), nullable=False),
    sa.Column("source_type", sa.String(80), nullable=False),
    sa.Column("source_category", sa.String(120), nullable=False),
    sa.Column("source_url", sa.Text(), nullable=True),
    sa.Column("file_reference", sa.Text(), nullable=True),
    sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("retrieval_method", sa.String(120), nullable=True),
    sa.Column("checksum", sa.String(128), nullable=True),
    sa.Column("source_owner", sa.String(255), nullable=True),
    sa.Column("is_official", sa.Boolean(), nullable=False),
    sa.Column("official_status_note", sa.Text(), nullable=True),
    sa.Column("status", sa.String(80), nullable=False),
    sa.Column("staff_notes", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)


class SourceRegistryRepository:
    """SQLAlchemy-backed source registry records.

    Configure with `CIVICCODE_SOURCE_REGISTRY_DB_URL` in the FastAPI runtime or
    pass a SQLAlchemy URL directly in local smoke checks and tests.
    """

    def __init__(self, *, db_url: str | None = None, engine: Engine | None = None) -> None:
        base_engine = engine or create_engine(db_url or "sqlite+pysqlite:///:memory:", future=True)
        if base_engine.dialect.name == "sqlite":
            self.engine = base_engine.execution_options(schema_translate_map={"civiccode": None})
        else:
            self.engine = base_engine
            with self.engine.begin() as connection:
                connection.execute(sa.text("CREATE SCHEMA IF NOT EXISTS civiccode"))
        metadata.create_all(self.engine)

    def create(self, data: dict[str, Any]) -> CodeSource:
        source = CodeSource(
            source_id=data.get("source_id") or f"src_{uuid4().hex}",
            name=data["name"],
            publisher=data["publisher"],
            source_type=data["source_type"],
            source_category=data["source_category"],
            source_url=data.get("source_url"),
            file_reference=data.get("file_reference"),
            retrieved_at=_coerce_datetime(data.get("retrieved_at")),
            retrieval_method=data.get("retrieval_method"),
            checksum=data.get("checksum"),
            source_owner=data.get("source_owner"),
            is_official=data.get("is_official", True),
            official_status_note=data.get("official_status_note"),
            status=data.get("status", "draft"),
            staff_notes=data.get("staff_notes"),
        )
        validate_source(source)
        now = datetime.now(UTC)
        with self.engine.begin() as connection:
            if self._exists(connection, source.source_id):
                raise SourceRegistryError(
                    f"Source '{source.source_id}' already exists.",
                    "Use a unique source_id or update the existing source instead.",
                    status_code=409,
                )
            connection.execute(
                source_registry_records.insert().values(
                    source_id=source.source_id,
                    name=source.name,
                    publisher=source.publisher,
                    source_type=source.source_type,
                    source_category=source.source_category,
                    source_url=source.source_url,
                    file_reference=source.file_reference,
                    retrieved_at=source.retrieved_at,
                    retrieval_method=source.retrieval_method,
                    checksum=source.checksum,
                    source_owner=source.source_owner,
                    is_official=source.is_official,
                    official_status_note=source.official_status_note,
                    status=source.status,
                    staff_notes=source.staff_notes,
                    created_at=now,
                    updated_at=now,
                )
            )
        return source

    def get(self, source_id: str) -> CodeSource:
        with self.engine.begin() as connection:
            row = connection.execute(
                sa.select(source_registry_records).where(
                    source_registry_records.c.source_id == source_id
                )
            ).mappings().first()
        if row is None:
            raise SourceRegistryError(
                f"Source '{source_id}' was not found.",
                "Create the source first or check the source_id in the request URL.",
                status_code=404,
            )
        return _row_to_source(row)

    def list_sources(self, *, include_staff_only: bool = False) -> list[CodeSource]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                sa.select(source_registry_records).order_by(source_registry_records.c.created_at)
            ).mappings().all()
        sources = [_row_to_source(row) for row in rows]
        if include_staff_only:
            return sources
        return [source for source in sources if source.public_visible]

    def transition(
        self,
        source_id: str,
        to_status: str,
        *,
        actor: str,
        reason: str,
    ) -> CodeSource:
        source = self.get(source_id)
        if not actor.strip():
            raise SourceRegistryError(
                "Source transition requires an actor.",
                "Provide the staff email or service account making the transition.",
            )
        if not reason.strip():
            raise SourceRegistryError(
                "Source transition requires a reason.",
                "Explain why this source state is changing.",
            )
        validate_transition(source.status, to_status)
        candidate = replace(source, status=to_status)
        validate_source(candidate)
        with self.engine.begin() as connection:
            connection.execute(
                source_registry_records.update()
                .where(source_registry_records.c.source_id == source_id)
                .values(status=to_status, updated_at=datetime.now(UTC))
            )
        return self.get(source_id)

    def reset(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(source_registry_records.delete())

    @staticmethod
    def _exists(connection: sa.Connection, source_id: str) -> bool:
        return (
            connection.execute(
                sa.select(source_registry_records.c.source_id).where(
                    source_registry_records.c.source_id == source_id
                )
            ).first()
            is not None
        )


def validate_transition(from_status: str, to_status: str) -> None:
    if from_status not in SOURCE_STATES:
        raise SourceRegistryError(
            f"Unknown source status '{from_status}'.",
            f"Use one of: {', '.join(sorted(SOURCE_STATES))}.",
        )
    if to_status not in SOURCE_STATES:
        raise SourceRegistryError(
            f"Unknown target source status '{to_status}'.",
            f"Use one of: {', '.join(sorted(SOURCE_STATES))}.",
        )
    if to_status not in SOURCE_TRANSITIONS[from_status]:
        allowed = ", ".join(sorted(SOURCE_TRANSITIONS[from_status])) or "none"
        raise SourceRegistryError(
            f"Cannot transition source from {from_status} to {to_status}.",
            f"Allowed target states from {from_status}: {allowed}.",
            status_code=409,
        )


def validate_source(source: CodeSource) -> None:
    if source.source_type not in SOURCE_TYPES:
        raise SourceRegistryError(
            f"Unknown source_type '{source.source_type}'.",
            f"Use one of: {', '.join(sorted(SOURCE_TYPES))}.",
        )
    if source.source_category not in SOURCE_CATEGORIES:
        raise SourceRegistryError(
            f"Unknown source_category '{source.source_category}'.",
            f"Use one of: {', '.join(sorted(SOURCE_CATEGORIES))}.",
        )
    if source.status not in SOURCE_STATES:
        raise SourceRegistryError(
            f"Unknown source status '{source.status}'.",
            f"Use one of: {', '.join(sorted(SOURCE_STATES))}.",
        )
    if not source.source_url and not source.file_reference:
        raise SourceRegistryError(
            "Source requires a URL or file reference.",
            "Provide source_url for web sources or file_reference for an official file drop.",
        )
    if source.source_url and not source.source_url.startswith(("http://", "https://")):
        raise SourceRegistryError(
            "source_url must be an HTTP or HTTPS URL.",
            "Use a full URL such as https://library.municode.com/example.",
        )
    if source.file_reference and ".." in source.file_reference.replace("\\", "/").split("/"):
        raise SourceRegistryError(
            "file_reference cannot contain path traversal segments.",
            "Use a safe file reference under the configured municipal file-drop location.",
        )
    if source.status == "active":
        validate_active_source_metadata(source)


def validate_active_source_metadata(source: CodeSource) -> None:
    if source.is_official:
        missing = [
            label
            for label, value in {
                "publisher": source.publisher,
                "source_owner": source.source_owner,
                "retrieval_method": source.retrieval_method,
                "retrieved_at": source.retrieved_at,
            }.items()
            if not value
        ]
        if missing:
            raise SourceRegistryError(
                "Active official sources require complete official-source metadata.",
                f"Add these fields before activation: {', '.join(missing)}.",
            )
        return

    if not source.official_status_note:
        raise SourceRegistryError(
            "Active non-official sources require an explicit non-official label.",
            "Set is_official=false and provide official_status_note explaining the limitation.",
        )


def source_to_public_dict(source: CodeSource) -> dict[str, Any]:
    payload = _source_base_dict(source)
    payload.pop("staff_notes", None)
    payload.update(
        {
            "public_visible": source.public_visible,
            "search_eligible": source.search_eligible,
        }
    )
    payload.update(ACTIONABLE_STATE_MESSAGES.get(source.status, {}))
    return payload


def source_to_staff_dict(source: CodeSource) -> dict[str, Any]:
    payload = _source_base_dict(source)
    payload.update(
        {
            "public_visible": source.public_visible,
            "search_eligible": source.search_eligible,
        }
    )
    payload.update(ACTIONABLE_STATE_MESSAGES.get(source.status, {}))
    return payload


def _source_base_dict(source: CodeSource) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "name": source.name,
        "publisher": source.publisher,
        "source_type": source.source_type,
        "source_category": source.source_category,
        "source_url": source.source_url,
        "file_reference": source.file_reference,
        "retrieved_at": source.retrieved_at.isoformat() if source.retrieved_at else None,
        "retrieval_method": source.retrieval_method,
        "checksum": source.checksum,
        "source_owner": source.source_owner,
        "is_official": source.is_official,
        "official_status_note": source.official_status_note,
        "status": source.status,
        "staff_notes": source.staff_notes,
        "created_at": source.created_at.isoformat(),
        "updated_at": source.updated_at.isoformat(),
    }


def _row_to_source(row: Any) -> CodeSource:
    data = dict(row)
    return CodeSource(
        source_id=data["source_id"],
        name=data["name"],
        publisher=data["publisher"],
        source_type=data["source_type"],
        source_category=data["source_category"],
        source_url=data["source_url"],
        file_reference=data["file_reference"],
        retrieved_at=data["retrieved_at"],
        retrieval_method=data["retrieval_method"],
        checksum=data["checksum"],
        source_owner=data["source_owner"],
        is_official=data["is_official"],
        official_status_note=data["official_status_note"],
        status=data["status"],
        staff_notes=data["staff_notes"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _coerce_datetime(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise SourceRegistryError(
        "retrieved_at must be an ISO 8601 timestamp.",
        "Use a timestamp such as 2026-04-27T12:00:00Z or omit retrieved_at until retrieval completes.",
    )


def compute_reference_checksum(value: str) -> str:
    """Return a deterministic checksum helper for fixture and operator smoke tests."""
    return sha256(value.encode("utf-8")).hexdigest()
