"""Public discovery aids for CivicCode resident lookup surfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Engine, create_engine
from sqlalchemy.dialects.postgresql import JSONB


QUESTION_STATUSES = {"draft", "approved", "retired"}
QUESTION_AUDIENCES = {"public", "staff"}
DISCOVERY_CLASSIFICATION = "navigation_aid_not_legal_determination"


class PublicDiscoveryError(ValueError):
    """Validation error with a public/staff-facing fix path."""

    def __init__(self, message: str, fix: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.message = message
        self.fix = fix
        self.status_code = status_code

    def detail(self) -> dict[str, str]:
        return {"message": self.message, "fix": self.fix}


@dataclass(slots=True)
class PopularQuestion:
    question_id: str
    question_text: str
    section_id: str
    section_number: str
    section_heading: str
    answer_excerpt: str
    citation_payload: dict[str, Any]
    audience: str = "public"
    status: str = "draft"
    is_popular: bool = True
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class PopularQuestionStore:
    """In-memory popular-question store with public-safe filtering."""

    def __init__(self) -> None:
        self._questions: dict[str, PopularQuestion] = {}

    def create(self, data: dict[str, Any], *, actor: str) -> PopularQuestion:
        question = build_popular_question(data, actor=actor)
        if question.question_id in self._questions:
            raise PublicDiscoveryError(
                f"Popular question '{question.question_id}' already exists.",
                "Use a unique question_id or update the existing question instead.",
                status_code=409,
            )
        self._questions[question.question_id] = question
        return question

    def public_popular_questions(self) -> list[PopularQuestion]:
        return sorted(
            [
                question
                for question in self._questions.values()
                if question.status == "approved"
                and question.audience == "public"
                and question.is_popular
            ],
            key=lambda question: (question.section_number, question.question_text),
        )

    def reset(self) -> None:
        self._questions.clear()


metadata = sa.MetaData()

popular_question_records = sa.Table(
    "popular_question_records",
    metadata,
    sa.Column("question_id", sa.String(255), primary_key=True),
    sa.Column("question_text", sa.Text(), nullable=False),
    sa.Column("section_id", sa.String(255), nullable=False),
    sa.Column("section_number", sa.String(120), nullable=False),
    sa.Column("section_heading", sa.String(500), nullable=False),
    sa.Column("answer_excerpt", sa.Text(), nullable=False),
    sa.Column("citation_payload", JSONB().with_variant(sa.JSON(), "sqlite"), nullable=False),
    sa.Column("audience", sa.String(80), nullable=False),
    sa.Column("status", sa.String(80), nullable=False),
    sa.Column("is_popular", sa.Boolean(), nullable=False),
    sa.Column("approved_by", sa.String(255), nullable=True),
    sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)


class PopularQuestionRepository(PopularQuestionStore):
    """SQLAlchemy-backed popular questions for shared Docker/PostgreSQL demos."""

    def __init__(self, *, db_url: str | None = None, engine: Engine | None = None) -> None:
        base_engine = engine or create_engine(db_url or "sqlite+pysqlite:///:memory:", future=True)
        if base_engine.dialect.name == "sqlite":
            self.engine = base_engine.execution_options(schema_translate_map={"civiccode": None})
        else:
            self.engine = base_engine
            with self.engine.begin() as connection:
                connection.execute(sa.text("CREATE SCHEMA IF NOT EXISTS civiccode"))
        metadata.create_all(self.engine)

    def create(self, data: dict[str, Any], *, actor: str) -> PopularQuestion:
        question = build_popular_question(data, actor=actor)
        with self.engine.begin() as connection:
            if self._exists(connection, question.question_id):
                raise PublicDiscoveryError(
                    f"Popular question '{question.question_id}' already exists.",
                    "Use a unique question_id or update the existing question instead.",
                    status_code=409,
                )
            connection.execute(
                popular_question_records.insert().values(
                    question_id=question.question_id,
                    question_text=question.question_text,
                    section_id=question.section_id,
                    section_number=question.section_number,
                    section_heading=question.section_heading,
                    answer_excerpt=question.answer_excerpt,
                    citation_payload=question.citation_payload,
                    audience=question.audience,
                    status=question.status,
                    is_popular=question.is_popular,
                    approved_by=question.approved_by,
                    approved_at=question.approved_at,
                    created_at=question.created_at,
                    updated_at=question.created_at,
                )
            )
        return question

    def public_popular_questions(self) -> list[PopularQuestion]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                sa.select(popular_question_records)
                .where(
                    popular_question_records.c.status == "approved",
                    popular_question_records.c.audience == "public",
                    popular_question_records.c.is_popular.is_(True),
                )
                .order_by(
                    popular_question_records.c.section_number,
                    popular_question_records.c.question_text,
                )
            ).mappings().all()
        return [_row_to_popular_question(row) for row in rows]

    def reset(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(popular_question_records.delete())

    @staticmethod
    def _exists(connection: sa.Connection, question_id: str) -> bool:
        return (
            connection.execute(
                sa.select(popular_question_records.c.question_id).where(
                    popular_question_records.c.question_id == question_id
                )
            ).first()
            is not None
        )


def build_popular_question(data: dict[str, Any], *, actor: str) -> PopularQuestion:
    status = data.get("status", "draft")
    audience = data.get("audience", "public")
    if status not in QUESTION_STATUSES:
        raise PublicDiscoveryError(
            f"Unknown popular-question status '{status}'.",
            f"Use one of: {', '.join(sorted(QUESTION_STATUSES))}.",
        )
    if audience not in QUESTION_AUDIENCES:
        raise PublicDiscoveryError(
            f"Unknown popular-question audience '{audience}'.",
            f"Use one of: {', '.join(sorted(QUESTION_AUDIENCES))}.",
        )
    return PopularQuestion(
        question_id=data.get("question_id") or f"question_{uuid4().hex}",
        question_text=data["question_text"],
        section_id=data["section_id"],
        section_number=data["section_number"],
        section_heading=data["section_heading"],
        answer_excerpt=data["answer_excerpt"],
        citation_payload=data["citation_payload"],
        audience=audience,
        status=status,
        is_popular=bool(data.get("is_popular", True)),
        approved_by=actor if status == "approved" else None,
        approved_at=datetime.now(UTC) if status == "approved" else None,
    )


def _row_to_popular_question(row: Any) -> PopularQuestion:
    data = dict(row)
    return PopularQuestion(
        question_id=data["question_id"],
        question_text=data["question_text"],
        section_id=data["section_id"],
        section_number=data["section_number"],
        section_heading=data["section_heading"],
        answer_excerpt=data["answer_excerpt"],
        citation_payload=data["citation_payload"],
        audience=data["audience"],
        status=data["status"],
        is_popular=data["is_popular"],
        approved_by=data["approved_by"],
        approved_at=data["approved_at"],
        created_at=data["created_at"],
    )


def popular_question_to_public_dict(question: PopularQuestion) -> dict[str, Any]:
    citation = question.citation_payload.get("citation") or {}
    return {
        "question_id": question.question_id,
        "question_text": question.question_text,
        "section_id": question.section_id,
        "section_number": question.section_number,
        "section_heading": question.section_heading,
        "answer_excerpt": question.answer_excerpt,
        "section_url": f"/civiccode/sections/{question.section_number}",
        "citation": citation,
        "classification": DISCOVERY_CLASSIFICATION,
        "legal_determination": "not_provided",
        "code_answer_behavior": "navigation_aid",
        "public_label": "Staff-approved navigation aid, not a legal determination.",
    }


def related_material_to_public_dict(item: dict[str, Any]) -> dict[str, Any]:
    return {
        **item,
        "classification": DISCOVERY_CLASSIFICATION,
        "legal_determination": "not_provided",
        "code_answer_behavior": "navigation_aid",
        "public_label": "Related material is a navigation aid, not a legal determination.",
    }
