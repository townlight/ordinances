"""Code section and version lifecycle rules for CivicCode Milestone 4."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Engine, create_engine
from sqlalchemy.dialects.postgresql import JSONB

from civiccode.semantic_search import (
    SemanticSearchError,
    embed_texts,
    embedding_config_from_env,
)


VERSION_STATUSES = {"draft", "pending", "adopted", "superseded", "retired"}
SECTION_NUMBER_RE = re.compile(r"\b\d{1,2}\.\d{2}\.\d{3}\b")
DEFAULT_SEMANTIC_SCORE_FLOOR = 0.58


class SectionLifecycleError(ValueError):
    """Validation error with an operator-facing fix path."""

    def __init__(self, message: str, fix: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.message = message
        self.fix = fix
        self.status_code = status_code

    def detail(self) -> dict[str, str]:
        return {"message": self.message, "fix": self.fix}


@dataclass(slots=True)
class CodeTitle:
    title_id: str
    title_number: str
    title_name: str
    sort_order: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class CodeChapter:
    chapter_id: str
    title_id: str
    chapter_number: str
    chapter_name: str
    sort_order: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class CodeSection:
    section_id: str
    chapter_id: str
    section_number: str
    section_heading: str
    parent_section_id: str | None = None
    sort_order: int = 0
    administrative_regulation_refs: list[str] = field(default_factory=list)
    resolution_refs: list[str] = field(default_factory=list)
    policy_refs: list[str] = field(default_factory=list)
    approved_summary_refs: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class SectionVersion:
    version_id: str
    section_id: str
    source_id: str
    version_label: str
    body: str
    effective_start: date
    effective_end: date | None = None
    status: str = "draft"
    is_current: bool = False
    adoption_event_id: str | None = None
    amendment_event_id: str | None = None
    amendment_summary: str | None = None
    prior_version_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def covers(self, as_of: date) -> bool:
        if as_of < self.effective_start:
            return False
        return self.effective_end is None or as_of <= self.effective_end


class SectionLifecycleStore:
    """In-memory section/version store for Milestone 4 API behavior."""

    def __init__(self) -> None:
        self._titles: dict[str, CodeTitle] = {}
        self._chapters: dict[str, CodeChapter] = {}
        self._sections: dict[str, CodeSection] = {}
        self._versions: dict[str, SectionVersion] = {}

    def create_title(self, data: dict[str, Any]) -> CodeTitle:
        title = CodeTitle(
            title_id=data.get("title_id") or f"title_{uuid4().hex}",
            title_number=data["title_number"],
            title_name=data["title_name"],
            sort_order=data.get("sort_order", 0),
        )
        if title.title_id in self._titles:
            raise SectionLifecycleError(
                f"Title '{title.title_id}' already exists.",
                "Use a unique title_id or reference the existing title.",
                status_code=409,
            )
        self._titles[title.title_id] = title
        return title

    def create_chapter(self, data: dict[str, Any]) -> CodeChapter:
        title_id = data["title_id"]
        if title_id not in self._titles:
            raise SectionLifecycleError(
                f"Title '{title_id}' was not found.",
                "Create the title before creating chapters under it.",
                status_code=404,
            )
        chapter = CodeChapter(
            chapter_id=data.get("chapter_id") or f"chapter_{uuid4().hex}",
            title_id=title_id,
            chapter_number=data["chapter_number"],
            chapter_name=data["chapter_name"],
            sort_order=data.get("sort_order", 0),
        )
        if chapter.chapter_id in self._chapters:
            raise SectionLifecycleError(
                f"Chapter '{chapter.chapter_id}' already exists.",
                "Use a unique chapter_id or reference the existing chapter.",
                status_code=409,
            )
        self._chapters[chapter.chapter_id] = chapter
        return chapter

    def create_section(self, data: dict[str, Any]) -> CodeSection:
        chapter_id = data["chapter_id"]
        if chapter_id not in self._chapters:
            raise SectionLifecycleError(
                f"Chapter '{chapter_id}' was not found.",
                "Create the chapter before creating sections under it.",
                status_code=404,
            )
        parent_section_id = data.get("parent_section_id")
        if parent_section_id and parent_section_id not in self._sections:
            raise SectionLifecycleError(
                f"Parent section '{parent_section_id}' was not found.",
                "Create the parent section first or omit parent_section_id.",
                status_code=404,
            )
        section = CodeSection(
            section_id=data.get("section_id") or f"section_{uuid4().hex}",
            chapter_id=chapter_id,
            section_number=data["section_number"],
            section_heading=data["section_heading"],
            parent_section_id=parent_section_id,
            sort_order=data.get("sort_order", 0),
            administrative_regulation_refs=list(data.get("administrative_regulation_refs", [])),
            resolution_refs=list(data.get("resolution_refs", [])),
            policy_refs=list(data.get("policy_refs", [])),
            approved_summary_refs=list(data.get("approved_summary_refs", [])),
        )
        if section.section_id in self._sections:
            raise SectionLifecycleError(
                f"Section '{section.section_id}' already exists.",
                "Use a unique section_id or reference the existing section.",
                status_code=409,
            )
        self._sections[section.section_id] = section
        return section

    def create_version(self, data: dict[str, Any]) -> SectionVersion:
        section_id = data["section_id"]
        if section_id not in self._sections:
            raise SectionLifecycleError(
                f"Section '{section_id}' was not found.",
                "Create the section before adding versions.",
                status_code=404,
            )
        status = data.get("status", "draft")
        if status not in VERSION_STATUSES:
            raise SectionLifecycleError(
                f"Unknown section version status '{status}'.",
                f"Use one of: {', '.join(sorted(VERSION_STATUSES))}.",
            )
        if data.get("is_current") and status != "adopted":
            raise SectionLifecycleError(
                "Only adopted section versions can be current law.",
                "Set status to adopted before marking a version as current.",
            )
        effective_end = data.get("effective_end")
        if effective_end and effective_end < data["effective_start"]:
            raise SectionLifecycleError(
                "effective_end cannot be before effective_start.",
                "Correct the effective date range before saving this version.",
            )
        prior_version_id = data.get("prior_version_id")
        if prior_version_id and prior_version_id not in self._versions:
            raise SectionLifecycleError(
                f"Prior version '{prior_version_id}' was not found.",
                "Reference an existing version or omit prior_version_id.",
                status_code=404,
            )

        version = SectionVersion(
            version_id=data.get("version_id") or f"version_{uuid4().hex}",
            section_id=section_id,
            source_id=data["source_id"],
            version_label=data["version_label"],
            body=data["body"],
            effective_start=data["effective_start"],
            effective_end=effective_end,
            status=status,
            is_current=data.get("is_current", False),
            adoption_event_id=data.get("adoption_event_id"),
            amendment_event_id=data.get("amendment_event_id"),
            amendment_summary=data.get("amendment_summary"),
            prior_version_id=prior_version_id,
        )
        if version.version_id in self._versions:
            raise SectionLifecycleError(
                f"Version '{version.version_id}' already exists.",
                "Use a unique version_id or reference the existing version.",
                status_code=409,
            )
        self._versions[version.version_id] = version
        if version.is_current:
            for prior in self._versions_for_section(section_id):
                if prior.version_id != version.version_id and prior.is_current:
                    prior.is_current = False
        return version

    def lookup_section(self, section_number: str, as_of: date | None = None) -> dict[str, Any]:
        matching_sections = [
            section for section in self._sections.values() if section.section_number == section_number
        ]
        if not matching_sections:
            raise SectionLifecycleError(
                f"Section '{section_number}' was not found.",
                "Create the section first or check the section number before lookup.",
                status_code=404,
            )
        if len(matching_sections) > 1:
            raise SectionLifecycleError(
                f"Section number '{section_number}' is ambiguous across multiple chapters.",
                "Lookup by section_id or include chapter context before relying on the result.",
                status_code=409,
            )

        section = matching_sections[0]
        versions = self._versions_for_section(section.section_id)
        if as_of is None:
            current_versions = [
                version
                for version in versions
                if version.status == "adopted" and version.is_current
            ]
            if len(current_versions) != 1:
                raise SectionLifecycleError(
                    f"Section '{section_number}' does not have one deterministic current version.",
                    "Provide as_of for historical lookup or correct the current-version flags.",
                    status_code=409,
                )
            return section_lookup_payload(section, current_versions[0], as_of=None)

        adopted_matches = [
            version
            for version in versions
            if version.status == "adopted" and version.covers(as_of)
        ]
        pending_matches = [
            version
            for version in versions
            if version.status == "pending" and version.covers(as_of)
        ]
        if pending_matches and not adopted_matches:
            raise SectionLifecycleError(
                f"Section '{section_number}' only has pending language for {as_of.isoformat()}.",
                "Wait for adoption/codification before treating this text as current law.",
                status_code=409,
            )
        if len(adopted_matches) > 1:
            raise SectionLifecycleError(
                f"Section '{section_number}' has overlapping adopted versions for {as_of.isoformat()}.",
                "Fix the effective date ranges before answering with this section.",
                status_code=409,
            )
        if not adopted_matches:
            raise SectionLifecycleError(
                f"Section '{section_number}' has no adopted version for {as_of.isoformat()}.",
                "Choose a different as_of date or add an adopted section version for that date.",
                status_code=404,
            )
        return section_lookup_payload(section, adopted_matches[0], as_of=as_of)

    def section_history(self, section_id: str) -> dict[str, Any]:
        section = self.get_section(section_id)
        versions = sorted(
            self._versions_for_section(section_id),
            key=lambda version: (version.effective_start, version.created_at),
        )
        return {
            "section": section_to_dict(section),
            "versions": [version_to_dict(version) for version in versions],
        }

    def list_sections(self) -> list[CodeSection]:
        return sorted(
            self._sections.values(),
            key=lambda section: (section.sort_order, section.section_number, section.section_id),
        )

    def list_versions(self, section_id: str) -> list[SectionVersion]:
        self.get_section(section_id)
        return sorted(
            self._versions_for_section(section_id),
            key=lambda version: (version.effective_start, version.created_at),
            reverse=True,
        )

    def permalink(self, section_id: str) -> dict[str, Any]:
        section = self.get_section(section_id)
        return {
            "section_id": section.section_id,
            "section_number": section.section_number,
            "permalink": section_permalink(section),
            "stable": True,
            "code_answer_behavior": "not_available",
        }

    def citation_context(self, section_number: str, as_of: date | None = None) -> dict[str, Any]:
        lookup = self.lookup_section(section_number, as_of=as_of)
        section = self.get_section(lookup["section"]["section_id"])
        chapter = self._chapters.get(section.chapter_id)
        if not chapter:
            raise SectionLifecycleError(
                f"Chapter '{section.chapter_id}' was not found for section '{section.section_id}'.",
                "Repair the section's chapter reference before building citations.",
                status_code=409,
            )
        title = self._titles.get(chapter.title_id)
        if not title:
            raise SectionLifecycleError(
                f"Title '{chapter.title_id}' was not found for chapter '{chapter.chapter_id}'.",
                "Repair the chapter's title reference before building citations.",
                status_code=409,
            )
        return {
            **lookup,
            "chapter": chapter_to_dict(chapter),
            "title": title_to_dict(title),
        }

    def search(self, query: str) -> dict[str, Any]:
        normalized = query.strip().lower()
        if not normalized:
            raise SectionLifecycleError(
                "Search query cannot be empty.",
                "Provide q with a section number or plain-language phrase.",
            )

        results: list[dict[str, Any]] = []
        result_by_section_id: dict[str, dict[str, Any]] = {}
        for section in self._sections.values():
            current = self._current_adopted_version(section.section_id)
            chapter = self._chapters.get(section.chapter_id)
            title = self._titles.get(chapter.title_id) if chapter else None
            haystack = " ".join(
                value
                for value in [
                    title.title_name if title else "",
                    chapter.chapter_name if chapter else "",
                    section.section_number,
                    section.section_heading,
                    current.body if current else "",
                ]
            ).lower()
            if normalized in haystack:
                result = search_result(section, current, result_type="code_section")
                results.append(result)
                result_by_section_id[section.section_id] = result

            results.extend(self._related_results(section, normalized))

        semantic_meta = self._semantic_search_metadata()
        semantic_ranked = self._rank_semantic_results(query)
        for rank, hit in enumerate(semantic_ranked[:5], start=1):
            section_id = str(hit["id"])
            if section_id in result_by_section_id:
                result_by_section_id[section_id]["semantic_score"] = hit["score"]
                result_by_section_id[section_id]["semantic_rank"] = rank
                continue
            try:
                section = self.get_section(section_id)
            except SectionLifecycleError:
                continue
            current = self._current_adopted_version(section.section_id)
            result = search_result(section, current, result_type="code_section")
            result["semantic_score"] = hit["score"]
            result["semantic_rank"] = rank
            result["match_type"] = "semantic"
            results.append(result)

        deduped: dict[tuple[str, str], dict[str, Any]] = {}
        for result in results:
            deduped[(result["result_type"], result["id"])] = result
        sorted_results = sorted(
            deduped.values(),
            key=lambda result: (
                result["result_type"] != "code_section",
                result.get("semantic_rank", 999),
                result["label"],
            ),
        )
        return {
            "query": query,
            "results": sorted_results,
            "count": len(sorted_results),
            "code_answer_behavior": "semantic_retrieval_available"
            if semantic_meta["enabled"]
            else "literal_and_related_lookup",
            "semantic_search": {
                **semantic_meta,
                "ranked_document_count": len(semantic_ranked),
            },
            "empty_state": None
            if sorted_results
            else {
                "message": "No public CivicCode results matched that search.",
                "fix": "Try an exact section number, fewer words, or a different code term.",
            },
        }

    def related_materials(self, section_number: str) -> dict[str, Any]:
        lookup = self.lookup_section(section_number)
        section = self.get_section(lookup["section"]["section_id"])
        related_groups = [
            ("administrative_regulation", section.administrative_regulation_refs),
            ("resolution", section.resolution_refs),
            ("policy", section.policy_refs),
            ("approved_summary", section.approved_summary_refs),
        ]
        items: list[dict[str, Any]] = []
        for result_type, references in related_groups:
            for reference in references:
                items.append(
                    {
                        "id": reference,
                        "result_type": result_type,
                        "label": reference,
                        "source_section_id": section.section_id,
                        "source_section_number": section.section_number,
                        "permalink": section_permalink(section),
                        "public_visible": True,
                    }
                )
        return {
            "section_number": section.section_number,
            "section_id": section.section_id,
            "items": items,
            "count": len(items),
            "classification": "navigation_aid_not_legal_determination",
            "legal_determination": "not_provided",
            "code_answer_behavior": "navigation_aid",
            "empty_state": None
            if items
            else {
                "message": "No approved related materials are attached to this section yet.",
                "fix": "Read the authoritative code text or contact the City Clerk for help locating related records.",
            },
        }

    def get_section(self, section_id: str) -> CodeSection:
        try:
            return self._sections[section_id]
        except KeyError as exc:
            raise SectionLifecycleError(
                f"Section '{section_id}' was not found.",
                "Create the section first or check the section_id in the request URL.",
                status_code=404,
            ) from exc

    def get_title(self, title_id: str) -> CodeTitle:
        try:
            return self._titles[title_id]
        except KeyError as exc:
            raise SectionLifecycleError(
                f"Title '{title_id}' was not found.",
                "Create the title before referencing it in an import.",
                status_code=404,
            ) from exc

    def get_chapter(self, chapter_id: str) -> CodeChapter:
        try:
            return self._chapters[chapter_id]
        except KeyError as exc:
            raise SectionLifecycleError(
                f"Chapter '{chapter_id}' was not found.",
                "Create the chapter before referencing it in an import.",
                status_code=404,
            ) from exc

    def get_version(self, version_id: str) -> SectionVersion:
        try:
            return self._versions[version_id]
        except KeyError as exc:
            raise SectionLifecycleError(
                f"Section version '{version_id}' was not found.",
                "Create the adopted section version before attaching summaries to it.",
                status_code=404,
            ) from exc

    def reset(self) -> None:
        self._titles.clear()
        self._chapters.clear()
        self._sections.clear()
        self._versions.clear()

    def _versions_for_section(self, section_id: str) -> list[SectionVersion]:
        return [
            version
            for version in self._versions.values()
            if version.section_id == section_id
        ]

    def _current_adopted_version(self, section_id: str) -> SectionVersion | None:
        current = [
            version
            for version in self._versions_for_section(section_id)
            if version.status == "adopted" and version.is_current
            ]
        if len(current) == 1:
            return current[0]
        return None

    def _semantic_search_metadata(self) -> dict[str, Any]:
        config = embedding_config_from_env()
        if not config:
            return {
                "enabled": False,
                "embedding_provider": None,
                "pgvector_runtime": "not_configured",
            }
        runtime_label = self._semantic_runtime_label()
        if runtime_label == "not_available_without_civiccore_pgvector":
            return {
                "enabled": False,
                "embedding_provider": f"ollama:{config.model}",
                "pgvector_runtime": runtime_label,
            }
        return {
            "enabled": True,
            "embedding_provider": f"ollama:{config.model}",
            "pgvector_runtime": runtime_label,
        }

    def _semantic_runtime_label(self) -> str:
        return "not_available_without_civiccore_pgvector"

    def _rank_semantic_results(self, query: str) -> list[dict[str, Any]]:
        return []

    def _related_results(self, section: CodeSection, normalized: str) -> list[dict[str, Any]]:
        related_groups = [
            ("administrative_regulation", section.administrative_regulation_refs),
            ("resolution", section.resolution_refs),
            ("policy", section.policy_refs),
            ("approved_summary", section.approved_summary_refs),
        ]
        results: list[dict[str, Any]] = []
        for result_type, references in related_groups:
            for reference in references:
                if normalized in reference.lower() or normalized.replace(" ", "-") in reference.lower():
                    results.append(
                        {
                            "id": reference,
                            "result_type": result_type,
                            "label": reference,
                            "source_section_id": section.section_id,
                            "source_section_number": section.section_number,
                            "permalink": section_permalink(section),
                            "public_visible": True,
                            "code_answer_behavior": "not_available",
                        }
                    )
        return results


metadata = sa.MetaData()
json_type = JSONB().with_variant(sa.JSON(), "sqlite")

code_title_records = sa.Table(
    "code_title_records",
    metadata,
    sa.Column("title_id", sa.String(255), primary_key=True),
    sa.Column("title_number", sa.String(80), nullable=False),
    sa.Column("title_name", sa.String(500), nullable=False),
    sa.Column("sort_order", sa.Integer(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)

code_chapter_records = sa.Table(
    "code_chapter_records",
    metadata,
    sa.Column("chapter_id", sa.String(255), primary_key=True),
    sa.Column("title_id", sa.String(255), nullable=False),
    sa.Column("chapter_number", sa.String(80), nullable=False),
    sa.Column("chapter_name", sa.String(500), nullable=False),
    sa.Column("sort_order", sa.Integer(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)

code_section_records = sa.Table(
    "code_section_records",
    metadata,
    sa.Column("section_id", sa.String(255), primary_key=True),
    sa.Column("chapter_id", sa.String(255), nullable=False),
    sa.Column("section_number", sa.String(120), nullable=False),
    sa.Column("section_heading", sa.String(500), nullable=False),
    sa.Column("parent_section_id", sa.String(255), nullable=True),
    sa.Column("sort_order", sa.Integer(), nullable=False),
    sa.Column("administrative_regulation_refs", json_type, nullable=False),
    sa.Column("resolution_refs", json_type, nullable=False),
    sa.Column("policy_refs", json_type, nullable=False),
    sa.Column("approved_summary_refs", json_type, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)

section_version_records = sa.Table(
    "section_version_records",
    metadata,
    sa.Column("version_id", sa.String(255), primary_key=True),
    sa.Column("section_id", sa.String(255), nullable=False),
    sa.Column("source_id", sa.String(255), nullable=False),
    sa.Column("version_label", sa.String(255), nullable=False),
    sa.Column("body", sa.Text(), nullable=False),
    sa.Column("effective_start", sa.Date(), nullable=False),
    sa.Column("effective_end", sa.Date(), nullable=True),
    sa.Column("status", sa.String(80), nullable=False),
    sa.Column("is_current", sa.Boolean(), nullable=False),
    sa.Column("adoption_event_id", sa.String(255), nullable=True),
    sa.Column("amendment_event_id", sa.String(255), nullable=True),
    sa.Column("amendment_summary", sa.Text(), nullable=True),
    sa.Column("prior_version_id", sa.String(255), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    schema="civiccode",
)

class SectionLifecycleRepository(SectionLifecycleStore):
    """Database-backed section lifecycle store for Docker/PostgreSQL product paths."""

    def __init__(self, *, db_url: str | None = None, engine: Engine | None = None) -> None:
        super().__init__()
        base_engine = engine or create_engine(db_url or "sqlite+pysqlite:///:memory:", future=True)
        if base_engine.dialect.name == "sqlite":
            self.engine = base_engine.execution_options(schema_translate_map={"civiccode": None})
        else:
            self.engine = base_engine
            with self.engine.begin() as connection:
                connection.execute(sa.text("CREATE SCHEMA IF NOT EXISTS civiccode"))
                connection.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
        metadata.create_all(self.engine)
        self._load()

    def create_title(self, data: dict[str, Any]) -> CodeTitle:
        title = super().create_title(data)
        with self.engine.begin() as connection:
            connection.execute(code_title_records.insert().values(**title_to_record(title)))
        return title

    def create_chapter(self, data: dict[str, Any]) -> CodeChapter:
        chapter = super().create_chapter(data)
        with self.engine.begin() as connection:
            connection.execute(code_chapter_records.insert().values(**chapter_to_record(chapter)))
        return chapter

    def create_section(self, data: dict[str, Any]) -> CodeSection:
        section = super().create_section(data)
        with self.engine.begin() as connection:
            connection.execute(code_section_records.insert().values(**section_to_record(section)))
        return section

    def create_version(self, data: dict[str, Any]) -> SectionVersion:
        version = super().create_version(data)
        with self.engine.begin() as connection:
            if version.is_current:
                connection.execute(
                    section_version_records.update()
                    .where(section_version_records.c.section_id == version.section_id)
                    .values(is_current=False)
                )
            connection.execute(section_version_records.insert().values(**version_to_record(version)))
        return version

    def reset(self) -> None:
        super().reset()
        with self.engine.begin() as connection:
            connection.execute(section_version_records.delete())
            connection.execute(code_section_records.delete())
            connection.execute(code_chapter_records.delete())
            connection.execute(code_title_records.delete())

    def _semantic_runtime_label(self) -> str:
        if self.engine.dialect.name == "postgresql":
            return "postgresql_pgvector"
        return "sqlite_json_vector_store"

    def _rank_semantic_results(self, query: str) -> list[dict[str, Any]]:
        config = embedding_config_from_env()
        if not config:
            return []
        if self.engine.dialect.name != "postgresql":
            return []
        try:
            query_embedding = embed_texts([query], config=config)[0]
        except SemanticSearchError:
            return []
        vector_literal = _pgvector_literal(query_embedding)
        score_floor = _semantic_score_floor()
        statement = sa.text(
            """
            SELECT content_text,
                   1 - (embedding <=> CAST(:query_embedding AS vector)) AS score
            FROM public.document_chunks
            WHERE embedding IS NOT NULL
              AND 1 - (embedding <=> CAST(:query_embedding AS vector)) >= :score_floor
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT 20
            """
        )
        ranked: list[dict[str, Any]] = []
        seen: set[str] = set()
        try:
            with self.engine.begin() as connection:
                rows = connection.execute(
                    statement,
                    {"query_embedding": vector_literal, "score_floor": score_floor},
                ).mappings()
                for row in rows:
                    match = self._section_for_shared_chunk(str(row["content_text"]))
                    if match is None or match.section_id in seen:
                        continue
                    current = self._current_adopted_version(match.section_id)
                    if current is None:
                        continue
                    ranked.append(
                        {
                            "id": match.section_id,
                            "version_id": current.version_id,
                            "score": round(float(row["score"]), 6),
                            "embedding_model": config.model,
                        }
                    )
                    seen.add(match.section_id)
                    if len(ranked) >= 5:
                        break
        except Exception:
            return []
        return ranked

    def _section_for_shared_chunk(self, chunk_text: str) -> CodeSection | None:
        for section_number in SECTION_NUMBER_RE.findall(chunk_text):
            matches = [
                section
                for section in self._sections.values()
                if section.section_number == section_number
            ]
            if matches:
                return matches[0]
        normalized_chunk = " ".join(chunk_text.lower().split())
        for version in self._versions.values():
            if version.status != "adopted" or not version.is_current:
                continue
            body = " ".join(version.body.lower().split())
            if not body:
                continue
            snippet = body[:240]
            if len(snippet) >= 80 and snippet in normalized_chunk:
                return self._sections.get(version.section_id)
        return None

    def _load(self) -> None:
        with self.engine.begin() as connection:
            for row in connection.execute(sa.select(code_title_records)).mappings():
                title = title_from_record(row)
                self._titles[title.title_id] = title
            for row in connection.execute(sa.select(code_chapter_records)).mappings():
                chapter = chapter_from_record(row)
                self._chapters[chapter.chapter_id] = chapter
            for row in connection.execute(sa.select(code_section_records)).mappings():
                section = section_from_record(row)
                self._sections[section.section_id] = section
            for row in connection.execute(sa.select(section_version_records)).mappings():
                version = version_from_record(row)
                self._versions[version.version_id] = version


def title_to_record(title: CodeTitle) -> dict[str, Any]:
    return {
        "title_id": title.title_id,
        "title_number": title.title_number,
        "title_name": title.title_name,
        "sort_order": title.sort_order,
        "created_at": title.created_at,
    }


def chapter_to_record(chapter: CodeChapter) -> dict[str, Any]:
    return {
        "chapter_id": chapter.chapter_id,
        "title_id": chapter.title_id,
        "chapter_number": chapter.chapter_number,
        "chapter_name": chapter.chapter_name,
        "sort_order": chapter.sort_order,
        "created_at": chapter.created_at,
    }


def section_to_record(section: CodeSection) -> dict[str, Any]:
    return {
        "section_id": section.section_id,
        "chapter_id": section.chapter_id,
        "section_number": section.section_number,
        "section_heading": section.section_heading,
        "parent_section_id": section.parent_section_id,
        "sort_order": section.sort_order,
        "administrative_regulation_refs": section.administrative_regulation_refs,
        "resolution_refs": section.resolution_refs,
        "policy_refs": section.policy_refs,
        "approved_summary_refs": section.approved_summary_refs,
        "created_at": section.created_at,
    }


def version_to_record(version: SectionVersion) -> dict[str, Any]:
    return {
        "version_id": version.version_id,
        "section_id": version.section_id,
        "source_id": version.source_id,
        "version_label": version.version_label,
        "body": version.body,
        "effective_start": version.effective_start,
        "effective_end": version.effective_end,
        "status": version.status,
        "is_current": version.is_current,
        "adoption_event_id": version.adoption_event_id,
        "amendment_event_id": version.amendment_event_id,
        "amendment_summary": version.amendment_summary,
        "prior_version_id": version.prior_version_id,
        "created_at": version.created_at,
    }


def title_from_record(row: Any) -> CodeTitle:
    return CodeTitle(
        title_id=row["title_id"],
        title_number=row["title_number"],
        title_name=row["title_name"],
        sort_order=row["sort_order"],
        created_at=row["created_at"],
    )


def chapter_from_record(row: Any) -> CodeChapter:
    return CodeChapter(
        chapter_id=row["chapter_id"],
        title_id=row["title_id"],
        chapter_number=row["chapter_number"],
        chapter_name=row["chapter_name"],
        sort_order=row["sort_order"],
        created_at=row["created_at"],
    )


def section_from_record(row: Any) -> CodeSection:
    return CodeSection(
        section_id=row["section_id"],
        chapter_id=row["chapter_id"],
        section_number=row["section_number"],
        section_heading=row["section_heading"],
        parent_section_id=row["parent_section_id"],
        sort_order=row["sort_order"],
        administrative_regulation_refs=list(row["administrative_regulation_refs"]),
        resolution_refs=list(row["resolution_refs"]),
        policy_refs=list(row["policy_refs"]),
        approved_summary_refs=list(row["approved_summary_refs"]),
        created_at=row["created_at"],
    )


def version_from_record(row: Any) -> SectionVersion:
    return SectionVersion(
        version_id=row["version_id"],
        section_id=row["section_id"],
        source_id=row["source_id"],
        version_label=row["version_label"],
        body=row["body"],
        effective_start=row["effective_start"],
        effective_end=row["effective_end"],
        status=row["status"],
        is_current=row["is_current"],
        adoption_event_id=row["adoption_event_id"],
        amendment_event_id=row["amendment_event_id"],
        amendment_summary=row["amendment_summary"],
        prior_version_id=row["prior_version_id"],
        created_at=row["created_at"],
    )


def _pgvector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{value:.9f}" for value in embedding) + "]"


def _semantic_score_floor() -> float:
    raw = os.environ.get("CIVICCODE_SEMANTIC_SCORE_FLOOR")
    if raw is None:
        return DEFAULT_SEMANTIC_SCORE_FLOOR
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_SEMANTIC_SCORE_FLOOR


def title_to_dict(title: CodeTitle) -> dict[str, Any]:
    return {
        "title_id": title.title_id,
        "title_number": title.title_number,
        "title_name": title.title_name,
        "sort_order": title.sort_order,
        "created_at": title.created_at.isoformat(),
    }


def chapter_to_dict(chapter: CodeChapter) -> dict[str, Any]:
    return {
        "chapter_id": chapter.chapter_id,
        "title_id": chapter.title_id,
        "chapter_number": chapter.chapter_number,
        "chapter_name": chapter.chapter_name,
        "sort_order": chapter.sort_order,
        "created_at": chapter.created_at.isoformat(),
    }


def section_to_dict(section: CodeSection) -> dict[str, Any]:
    return {
        "section_id": section.section_id,
        "chapter_id": section.chapter_id,
        "section_number": section.section_number,
        "section_heading": section.section_heading,
        "parent_section_id": section.parent_section_id,
        "sort_order": section.sort_order,
        "administrative_regulation_refs": section.administrative_regulation_refs,
        "resolution_refs": section.resolution_refs,
        "policy_refs": section.policy_refs,
        "approved_summary_refs": section.approved_summary_refs,
        "created_at": section.created_at.isoformat(),
    }


def version_to_dict(version: SectionVersion) -> dict[str, Any]:
    return {
        "version_id": version.version_id,
        "section_id": version.section_id,
        "source_id": version.source_id,
        "version_label": version.version_label,
        "body": version.body,
        "effective_start": version.effective_start.isoformat(),
        "effective_end": version.effective_end.isoformat() if version.effective_end else None,
        "status": version.status,
        "is_current": version.is_current,
        "adoption_event_id": version.adoption_event_id,
        "amendment_event_id": version.amendment_event_id,
        "amendment_summary": version.amendment_summary,
        "prior_version_id": version.prior_version_id,
        "created_at": version.created_at.isoformat(),
    }


def section_lookup_payload(
    section: CodeSection,
    version: SectionVersion,
    *,
    as_of: date | None,
) -> dict[str, Any]:
    return {
        "section": section_to_dict(section),
        "version": version_to_dict(version),
        "as_of": as_of.isoformat() if as_of else None,
        "legal_effect": "adopted_law",
        "code_answer_behavior": "not_available",
    }


def section_permalink(section: CodeSection) -> str:
    return f"/civiccode/sections/{section.section_id}"


def search_result(
    section: CodeSection,
    version: SectionVersion | None,
    *,
    result_type: str,
) -> dict[str, Any]:
    return {
        "id": section.section_id,
        "result_type": result_type,
        "label": f"{section.section_number} - {section.section_heading}",
        "section_number": section.section_number,
        "section_heading": section.section_heading,
        "version_id": version.version_id if version else None,
        "effective_start": version.effective_start.isoformat() if version else None,
        "permalink": section_permalink(section),
        "public_visible": True,
        "code_answer_behavior": "not_available",
    }
