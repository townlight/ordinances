"""FastAPI runtime foundation for CivicCode."""

from __future__ import annotations

import os
from contextvars import ContextVar
from datetime import date, datetime
from typing import Any

from civiccore.auth import (
    TrustedHeaderAuthConfig,
    authorize_trusted_header_roles,
    enforce_trusted_proxy_source,
    load_trusted_header_auth_config,
)
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import HTMLResponse

from civiccode import __version__
from civiccode.citation_contract import build_citation_payload, refusal
from civiccode.codifier_sync import (
    CodifierSyncError,
    CodifierSyncRepository,
    CodifierSyncStore,
    sync_source_to_dict,
)
from civiccode.import_connectors import (
    CONNECTOR_TYPES,
    CivicCodeImportError,
    ImportConnectorRepository,
    ImportConnectorStore,
    imported_tree_snapshot,
    job_to_dict,
    provenance_report,
)
from civiccode.mock_city_environment import mock_city_codifier_contracts, mock_city_import_payload
from civiccode.operational_readiness import build_operational_readiness
from civiccode.ordinance_handoff import (
    OrdinanceHandoffError,
    OrdinanceHandoffRepository,
    OrdinanceHandoffStore,
    event_to_dict,
    handoff_audit_event_to_dict,
)
from civiccode.plain_language import (
    PlainLanguageSummaryError,
    PlainLanguageSummaryRepository,
    PlainLanguageSummaryStore,
    summary_audit_event_to_dict,
    summary_to_public_dict,
    summary_to_staff_dict,
)
from civiccode.public_lookup import (
    is_legal_advice_query,
    render_answer_page,
    render_error_page,
    render_home_page,
    render_refusal_page,
    render_search_page,
    render_section_page,
)
from civiccode.public_exports import (
    build_records_ready_export,
    render_records_ready_export_page,
)
from civiccode.public_discovery import (
    PopularQuestionRepository,
    PopularQuestionStore,
    PublicDiscoveryError,
    popular_question_to_public_dict,
    related_material_to_public_dict,
)
from civiccode.qa_harness import (
    QuestionRequestContext,
    build_grounded_answer,
    looks_like_legal_determination,
)
from civiccode.section_lifecycle import (
    SectionLifecycleError,
    SectionLifecycleRepository,
    SectionLifecycleStore,
    chapter_to_dict,
    section_to_dict,
    title_to_dict,
    version_to_dict,
)
from civiccode.staff_sources import (
    render_staff_source_required_page,
    render_staff_source_workspace,
)
from civiccode.staff_imports import (
    render_staff_import_ledger,
    render_staff_import_required_page,
)
from civiccode.staff_sync import (
    render_staff_sync_required_page,
    render_staff_sync_workspace,
)
from civiccode.staff_code import (
    render_staff_code_required_page,
    render_staff_code_workspace,
)
from civiccode.staff_workbench import (
    StaffWorkbenchError,
    StaffWorkbenchRepository,
    StaffWorkbenchStore,
    audit_event_to_dict,
    note_to_staff_dict,
)
from civiccode.source_registry import (
    SOURCE_CATEGORIES,
    SOURCE_STATES,
    SOURCE_TRANSITIONS,
    SOURCE_TYPES,
    SourceRegistryRepository,
    SourceRegistryError,
    SourceRegistryStore,
    compute_reference_checksum,
    source_to_public_dict,
    source_to_staff_dict,
)
from civiccore import __version__ as CIVICCORE_VERSION

app = FastAPI(
    title="CivicCode",
    version=__version__,
    summary="Runtime foundation for CivicCode municipal code access workflows.",
)
_current_request: ContextVar[Request | None] = ContextVar("current_request", default=None)

SOURCE_STORE = SourceRegistryStore()
_source_registry_repository: SourceRegistryRepository | None = None
_source_registry_db_url: str | None = None
SECTION_MEMORY_STORE = SectionLifecycleStore()
_section_lifecycle_repository: SectionLifecycleRepository | None = None
_section_lifecycle_db_url: str | None = None
_staff_workbench_repository: StaffWorkbenchRepository | None = None
_staff_workbench_db_url: str | None = None
_plain_language_repository: PlainLanguageSummaryRepository | None = None
_plain_language_db_url: str | None = None
_ordinance_handoff_repository: OrdinanceHandoffRepository | None = None
_ordinance_handoff_db_url: str | None = None


class SectionLifecycleRouter:
    """Route lifecycle calls to memory or the configured durable repository."""

    def __init__(self, memory_store: SectionLifecycleStore) -> None:
        self._memory_store = memory_store

    def _target(self) -> SectionLifecycleRepository | SectionLifecycleStore:
        global _section_lifecycle_db_url, _section_lifecycle_repository
        db_url = os.environ.get("CIVICCODE_SOURCE_REGISTRY_DB_URL")
        if db_url is None:
            return self._memory_store
        if _section_lifecycle_repository is None or db_url != _section_lifecycle_db_url:
            _section_lifecycle_db_url = db_url
            _section_lifecycle_repository = SectionLifecycleRepository(db_url=db_url)
        return _section_lifecycle_repository

    def reset(self) -> None:
        self._target().reset()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target(), name)


SECTION_STORE = SectionLifecycleRouter(SECTION_MEMORY_STORE)
STAFF_NOTE_MEMORY_STORE = StaffWorkbenchStore()
SUMMARY_MEMORY_STORE = PlainLanguageSummaryStore()


class StaffWorkbenchRouter:
    """Route staff note calls to memory or the configured durable repository."""

    def __init__(self, memory_store: StaffWorkbenchStore) -> None:
        self._memory_store = memory_store

    def _target(self) -> StaffWorkbenchRepository | StaffWorkbenchStore:
        global _staff_workbench_db_url, _staff_workbench_repository
        db_url = os.environ.get("CIVICCODE_SOURCE_REGISTRY_DB_URL")
        if db_url is None:
            return self._memory_store
        if _staff_workbench_repository is None or db_url != _staff_workbench_db_url:
            _staff_workbench_db_url = db_url
            _staff_workbench_repository = StaffWorkbenchRepository(db_url=db_url)
        return _staff_workbench_repository

    def reset(self) -> None:
        self._target().reset()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target(), name)


class PlainLanguageSummaryRouter:
    """Route summary calls to memory or the configured durable repository."""

    def __init__(self, memory_store: PlainLanguageSummaryStore) -> None:
        self._memory_store = memory_store

    def _target(self) -> PlainLanguageSummaryRepository | PlainLanguageSummaryStore:
        global _plain_language_db_url, _plain_language_repository
        db_url = os.environ.get("CIVICCODE_SOURCE_REGISTRY_DB_URL")
        if db_url is None:
            return self._memory_store
        if _plain_language_repository is None or db_url != _plain_language_db_url:
            _plain_language_db_url = db_url
            _plain_language_repository = PlainLanguageSummaryRepository(db_url=db_url)
        return _plain_language_repository

    def reset(self) -> None:
        self._target().reset()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target(), name)


STAFF_NOTE_STORE = StaffWorkbenchRouter(STAFF_NOTE_MEMORY_STORE)
SUMMARY_STORE = PlainLanguageSummaryRouter(SUMMARY_MEMORY_STORE)
HANDOFF_MEMORY_STORE = OrdinanceHandoffStore()


class OrdinanceHandoffRouter:
    """Route CivicClerk handoff calls to memory or the configured durable repository."""

    def __init__(self, memory_store: OrdinanceHandoffStore) -> None:
        self._memory_store = memory_store

    def _target(self) -> OrdinanceHandoffRepository | OrdinanceHandoffStore:
        global _ordinance_handoff_db_url, _ordinance_handoff_repository
        db_url = os.environ.get("CIVICCODE_SOURCE_REGISTRY_DB_URL")
        if db_url is None:
            return self._memory_store
        if _ordinance_handoff_repository is None or db_url != _ordinance_handoff_db_url:
            _ordinance_handoff_db_url = db_url
            _ordinance_handoff_repository = OrdinanceHandoffRepository(db_url=db_url)
        return _ordinance_handoff_repository

    def reset(self) -> None:
        self._target().reset()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target(), name)


HANDOFF_STORE = OrdinanceHandoffRouter(HANDOFF_MEMORY_STORE)
POPULAR_QUESTION_STORE = PopularQuestionStore()
_popular_question_repository: PopularQuestionRepository | None = None
_popular_question_db_url: str | None = None
_import_store: ImportConnectorStore | None = None
_import_store_source_key: str | None = None
_codifier_sync_store: CodifierSyncStore | None = None
_codifier_sync_store_source_key: str | None = None
IMPORT_STORE = ImportConnectorStore(
    source_store=SOURCE_STORE,
    section_store=SECTION_STORE,
)
CODIFIER_SYNC_STORE = CodifierSyncStore(
    source_store=SOURCE_STORE,
    import_store=IMPORT_STORE,
)
_demo_seed_key: str | None = None


class SourceCreate(BaseModel):
    """Request body for registering an official or explicitly labeled source."""

    model_config = ConfigDict(extra="forbid")

    source_id: str | None = None
    name: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_category: str = Field(min_length=1)
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


class SourceTransitionRequest(BaseModel):
    """Request body for source-state changes."""

    model_config = ConfigDict(extra="forbid")

    to_status: str
    actor: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class TitleCreate(BaseModel):
    """Request body for creating a code title."""

    model_config = ConfigDict(extra="forbid")

    title_id: str | None = None
    title_number: str = Field(min_length=1)
    title_name: str = Field(min_length=1)
    sort_order: int = 0


class ChapterCreate(BaseModel):
    """Request body for creating a code chapter."""

    model_config = ConfigDict(extra="forbid")

    chapter_id: str | None = None
    title_id: str = Field(min_length=1)
    chapter_number: str = Field(min_length=1)
    chapter_name: str = Field(min_length=1)
    sort_order: int = 0


class SectionCreate(BaseModel):
    """Request body for creating a code section or subsection."""

    model_config = ConfigDict(extra="forbid")

    section_id: str | None = None
    chapter_id: str = Field(min_length=1)
    section_number: str = Field(min_length=1)
    section_heading: str = Field(min_length=1)
    parent_section_id: str | None = None
    sort_order: int = 0
    administrative_regulation_refs: list[str] = Field(default_factory=list)
    resolution_refs: list[str] = Field(default_factory=list)
    policy_refs: list[str] = Field(default_factory=list)
    approved_summary_refs: list[str] = Field(default_factory=list)


class SectionVersionCreate(BaseModel):
    """Request body for adding an immutable section version."""

    model_config = ConfigDict(extra="forbid")

    version_id: str | None = None
    section_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    version_label: str = Field(min_length=1)
    body: str = Field(min_length=1)
    effective_start: date
    effective_end: date | None = None
    status: str = "draft"
    is_current: bool = False
    adoption_event_id: str | None = None
    amendment_event_id: str | None = None
    amendment_summary: str | None = None
    prior_version_id: str | None = None


class QuestionAnswerRequest(BaseModel):
    """Request body for citation-grounded code Q&A."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    section_number: str | None = None
    as_of: date | None = None


class SectionResolveRequest(BaseModel):
    """Request body for downstream module section-resolution clients."""

    model_config = ConfigDict(extra="forbid")

    consumer_module: str = Field(min_length=1)
    section_number: str | None = None
    query: str | None = None
    as_of: date | None = None


class PopularQuestionCreate(BaseModel):
    """Request body for a staff-approved public popular-question navigation aid."""

    model_config = ConfigDict(extra="forbid")

    question_id: str | None = None
    question_text: str = Field(min_length=1)
    section_number: str = Field(min_length=1)
    answer_excerpt: str = Field(min_length=1)
    audience: str = "public"
    status: str = "approved"
    is_popular: bool = True


class InterpretationNoteCreate(BaseModel):
    """Request body for staff-only interpretation notes."""

    model_config = ConfigDict(extra="forbid")

    note_id: str | None = None
    note_text: str = Field(min_length=1)
    status: str = "draft"


class PlainLanguageSummaryCreate(BaseModel):
    """Request body for staff-drafted plain-language summaries."""

    model_config = ConfigDict(extra="forbid")

    summary_id: str | None = None
    section_version_id: str = Field(min_length=1)
    summary_text: str = Field(min_length=1)
    language_code: str = "en"
    status: str = "draft"


class CivicClerkOrdinanceEventCreate(BaseModel):
    """Request body for CivicClerk ordinance/adoption handoff intake."""

    model_config = ConfigDict(extra="forbid")

    event_id: str | None = None
    external_event_id: str = Field(min_length=1)
    civicclerk_meeting_id: str = Field(min_length=1)
    civicclerk_agenda_item_id: str = Field(min_length=1)
    ordinance_number: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: str = "pending"
    affected_sections: list[str] = Field(default_factory=list)
    source_document_url: str = Field(min_length=1)
    source_document_hash: str = Field(min_length=1)
    ordinance_text: str = ""
    adopted_at: datetime | None = None
    failure_reason: str | None = None


class CivicClerkOrdinanceEventResolve(BaseModel):
    """Request body for resolving a handoff after staff codifies the amendment."""

    model_config = ConfigDict(extra="forbid")

    section_version_id: str = Field(min_length=1)


class ImportBundleCreate(BaseModel):
    """Request body for local fixture/file-drop import jobs."""

    model_config = ConfigDict(extra="forbid")

    job_id: str | None = None
    connector_type: str = Field(min_length=1)
    source: SourceCreate
    titles: list[TitleCreate] = Field(default_factory=list)
    chapters: list[ChapterCreate] = Field(default_factory=list)
    sections: list[SectionCreate] = Field(default_factory=list)
    versions: list[SectionVersionCreate] = Field(default_factory=list)
    provenance: dict[str, str] = Field(default_factory=dict)


class CodifierSyncConfigureRequest(BaseModel):
    """Request body for enabling staff-controlled codifier sync readiness."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    sync_schedule: str = Field(min_length=1)
    allowlisted_hosts: list[str] = Field(default_factory=list)


class CodifierSyncRunRequest(BaseModel):
    """Request body for a local codifier sync run."""

    model_config = ConfigDict(extra="forbid")

    payload: ImportBundleCreate
    changed_since: datetime | None = None


def _raise_source_error(exc: SourceRegistryError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail()) from exc


def _raise_codifier_sync_error(exc: CodifierSyncError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail()) from exc


def _raise_section_error(exc: SectionLifecycleError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail()) from exc


def _raise_staff_error(exc: StaffWorkbenchError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail()) from exc


def _raise_summary_error(exc: PlainLanguageSummaryError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail()) from exc


def _raise_handoff_error(exc: OrdinanceHandoffError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail()) from exc


def _raise_import_error(exc: CivicCodeImportError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail()) from exc


def _raise_public_discovery_error(exc: PublicDiscoveryError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail()) from exc


def _require_staff(
    x_civiccode_role: str | None,
    x_civiccode_actor: str | None,
) -> str:
    request = _current_request.get()
    config = _staff_trusted_header_config() if request is not None else None
    if request is not None and (
        config.principal_header_name != "X-CivicCode-Actor"
        or config.roles_header_name != "X-CivicCode-Role"
    ):
        return _require_staff_from_trusted_headers(request, config)
    if x_civiccode_role != "staff":
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Staff role required for this CivicCode endpoint.",
                "fix": "Send X-CivicCode-Role: staff from the trusted staff shell or service account.",
            },
        )
    actor = (x_civiccode_actor or "").strip()
    if not actor:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Staff actor required for this CivicCode endpoint.",
                "fix": "Send X-CivicCode-Actor with the staff email or service account.",
            },
        )
    if request is None:
        return actor
    if config is None:
        config = _staff_trusted_header_config()
    return _require_staff_from_trusted_headers(request, config)


def _require_staff_from_trusted_headers(
    request: Request,
    config: TrustedHeaderAuthConfig,
) -> str:
    enforce_trusted_proxy_source(
        request.client.host if request.client else None,
        service_name="CivicCode",
        feature_name="staff endpoint access",
        config=config,
        trusted_proxy_env_var="CIVICCODE_STAFF_TRUSTED_PROXY_CIDRS",
    )
    principal = authorize_trusted_header_roles(
        request.headers,
        service_name="CivicCode",
        feature_name="staff endpoint access",
        principal_header_name=config.principal_header_name,
        roles_header_name=config.roles_header_name,
        allowed_roles={"staff"},
        provider_name=config.provider_name,
    )
    return principal.subject or ""


def _staff_trusted_header_config() -> TrustedHeaderAuthConfig:
    config = load_trusted_header_auth_config(
        provider_env_var="CIVICCODE_STAFF_AUTH_PROVIDER",
        provider_default="CivicCode staff shell",
        principal_header_env_var="CIVICCODE_STAFF_PRINCIPAL_HEADER",
        principal_header_default="X-CivicCode-Actor",
        roles_header_env_var="CIVICCODE_STAFF_ROLES_HEADER",
        roles_header_default="X-CivicCode-Role",
        trusted_proxy_env_var="CIVICCODE_STAFF_TRUSTED_PROXY_CIDRS",
    )
    if config.trusted_proxy_cidrs:
        return config
    return TrustedHeaderAuthConfig(
        provider_name=config.provider_name,
        principal_header_name=config.principal_header_name,
        roles_header_name=config.roles_header_name,
        trusted_proxy_cidrs=("127.0.0.1/32", "::1/128"),
    )


def _staff_code_payload() -> dict[str, Any]:
    sources = [source_to_staff_dict(source) for source in _get_source_store().list_sources(include_staff_only=True)]
    source_by_id = {source["source_id"]: source for source in sources}
    source_status = {
        "active": sum(1 for source in sources if source["status"] == "active"),
        "stale": sum(1 for source in sources if source["status"] == "stale"),
        "failed": sum(1 for source in sources if source["status"] == "failed"),
    }
    section_cards = []
    current_versions = 0
    draft_summaries = 0
    handoff_warnings = 0
    for section in SECTION_STORE.list_sections():
        section_payload = section_to_dict(section)
        versions = [version_to_dict(version) for version in SECTION_STORE.list_versions(section.section_id)]
        current_version = next(
            (version for version in versions if version["is_current"] and version["status"] == "adopted"),
            None,
        )
        if current_version:
            current_versions += 1
        summaries = [
            summary_to_staff_dict(summary)
            for summary in SUMMARY_STORE.list_for_section(section.section_id, include_unapproved=True)
        ]
        draft_summaries += sum(1 for summary in summaries if summary["status"] == "draft")
        warnings = HANDOFF_STORE.warnings_for_section(section.section_number)
        handoff_warnings += len(warnings)
        source_label = None
        if current_version:
            source = source_by_id.get(current_version["source_id"])
            source_label = source["name"] if source else current_version["source_id"]
        section_cards.append(
            {
                **section_payload,
                "public_url": f"/civiccode/sections/{section.section_number}",
                "current_version": current_version,
                "source_label": source_label,
                "summaries": summaries,
                "handoff_warnings": warnings,
                "staff_note_count": len(STAFF_NOTE_STORE.list_notes(section.section_id)),
                "next_action": _staff_code_next_action(current_version, summaries, warnings),
            }
        )
    blockers = []
    if source_status["active"] == 0:
        blockers.append("Register or reactivate an official source before staff publishes new adopted code text.")
    if section_cards and current_versions < len(section_cards):
        blockers.append("One or more sections do not have a current adopted version.")
    if draft_summaries:
        blockers.append("Draft plain-language summaries need staff approval before residents can see them.")
    if handoff_warnings:
        blockers.append("Pending CivicClerk handoffs require codification review before staff treats text as fully current.")
    return {
        "source_status": source_status,
        "counts": {
            "sections": len(section_cards),
            "current_versions": current_versions,
            "draft_summaries": draft_summaries,
            "handoff_warnings": handoff_warnings,
        },
        "blockers": blockers,
        "sections": section_cards,
    }


def _staff_code_next_action(
    current_version: dict[str, Any] | None,
    summaries: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> str:
    if current_version is None:
        return "Fix: add an adopted current version from an active official source before this section powers resident lookup."
    if warnings:
        return "Fix: review the CivicClerk handoff and update the codified text or mark the event resolved before relying on this section."
    if not summaries:
        return "Fix: draft and approve a non-authoritative plain-language summary if residents need a plain explanation."
    if any(summary["status"] == "draft" for summary in summaries):
        return "Fix: approve, revise, or retire draft summaries so public pages show only reviewed guidance."
    return "Ready: current adopted text and approved summary state are aligned for staff review."


def _staff_import_payload() -> dict[str, Any]:
    jobs = []
    for job in _get_import_store().list_jobs():
        jobs.append(provenance_report(job, _get_source_store()))
    connector_types = sorted({item["job"]["connector_type"] for item in jobs})
    connector_label = ", ".join(connector_types) if connector_types else ", ".join(sorted(CONNECTOR_TYPES))
    return {
        "jobs": jobs,
        "connector_types": connector_label,
        "counts": {
            "total_jobs": len(jobs),
            "completed_jobs": sum(1 for item in jobs if item["job"]["status"] == "completed"),
            "failed_jobs": sum(1 for item in jobs if item["job"]["status"] == "failed"),
            "retried_jobs": sum(1 for item in jobs if item["job"].get("retry_of")),
        },
    }


def _operational_readiness_payload() -> dict[str, Any]:
    records = []
    for store in (HANDOFF_STORE, _get_import_store(), _get_codifier_sync_store()):
        records.extend(store.operational_records())
    payload = build_operational_readiness(records)
    payload["api"] = {
        "path": "/api/v1/civiccode/staff/operational-state",
        "audience": "staff_operator",
        "auth": "X-CivicCode-Role: staff and X-CivicCode-Actor required",
    }
    return payload


@app.middleware("http")
async def _demo_seed_middleware(request: Any, call_next: Any) -> Any:
    """Seed the opt-in demo city before the first rendered/API request."""
    token = _current_request.set(request)
    try:
        _seed_demo_city_if_enabled()
        return await call_next(request)
    finally:
        _current_request.reset(token)


@app.get("/")
async def root() -> dict[str, str]:
    """Describe the current shipped runtime boundary."""
    return {
        "name": "CivicCode",
        "status": "docker demo codifier runtime",
        "message": (
            "CivicCode runtime, canonical schema, official source registry API, and "
            "section/version lifecycle APIs are online. Search and stable section permalink "
            "APIs are online. Deterministic citations and refusal objects are online. "
            "Citation-grounded Q&A harness is online for adopted sections. Staff "
            "interpretation-note APIs and staff Q&A context are online. Staff-approved "
            "plain-language summaries are online and labeled non-authoritative. "
            "Staff-approved popular questions and related-material navigation "
            "aids are online with citations and no legal determinations. "
            "CivicClerk ordinance handoff intake, durable handoff records, audit "
            "events, and affected-section warnings are online. Resident-facing "
            "public lookup pages are online at /civiccode. "
            "The downstream section-resolution service is online for CivicZone, "
            "CivicLegal, CivicAccess, and CivicComms. The resident cited-answer "
            "page is online at /civiccode/answer. "
            "Local file-drop and fixture import jobs are online with provenance, "
            "retry, and no required outbound dependency. Records-ready section "
            "exports are online with citation, version, and source metadata. "
            "The staff source registry workspace is online at /staff/sources "
            "and the staff code lifecycle workspace is online at /staff/code "
            "with staff-header protection for staff-only source notes. "
            "Staff-controlled codifier sync readiness is online with schedule "
            "validation, SSRF-safe host checks, local payload runs, delta "
            "request planning, circuit-breaker health, and actionable operator "
            "copy. Live LLM calls, bundled vendor credentials, automatic "
            "ordinance codification, and legal determinations are not "
            "implemented."
        ),
        "code_answer_behavior": "citation_grounded",
        "api_base": "/api/v1/civiccode",
        "future_public_path": "/civiccode",
        "next_step": (
            "CivicCode v1.0.0 persists section/version lifecycle records, "
            "popular-question discovery aids, staff notes, plain-language "
            "summaries, CivicClerk handoff records, handoff audit events, and "
            "local import job ledgers, codifier sync source state, and "
            "operational retry, replay, and cursor state "
            "in the configured database; next work follows the CivicSuite roadmap."
        ),
    }


@app.get("/civiccode", response_class=HTMLResponse)
async def public_lookup_home() -> str:
    """Render the resident-facing public code lookup home page."""
    questions = [
        popular_question_to_public_dict(question)
        for question in _get_popular_question_store().public_popular_questions()
    ]
    return render_home_page(questions)


@app.get("/civiccode/search", response_class=HTMLResponse)
async def public_lookup_search(q: str = "") -> str:
    """Render public search results, empty states, or refusal states."""
    query = q.strip()
    if not query:
        return render_error_page(
            "Search query required",
            "Search query cannot be empty.",
            "Enter a section number like 6.12.040 or a resident phrase like backyard chickens.",
            status_label="Empty search",
        )
    if is_legal_advice_query(query):
        return render_refusal_page(query)
    try:
        results = SECTION_STORE.search(query)["results"]
    except SectionLifecycleError:
        results = []
    return render_search_page(query, results)


@app.get("/civiccode/answer", response_class=HTMLResponse)
async def public_lookup_answer(
    q: str = "",
    section_number: str | None = None,
    as_of: date | None = None,
) -> str:
    """Render a resident-facing cited answer for one adopted section."""
    query = q.strip()
    if not query:
        return render_error_page(
            "Question required",
            "Question cannot be empty.",
            "Ask what one adopted section says and include the exact section number.",
            status_label="Empty question",
        )
    payload = build_grounded_answer(
        QuestionRequestContext(question=query, section_number=section_number, as_of=as_of),
        search=SECTION_STORE.search,
        build_citation=_build_citation_for_section,
    )
    return render_answer_page(query, payload)


@app.get("/civiccode/sections/{section_ref}", response_class=HTMLResponse)
async def public_section_detail(section_ref: str, as_of: date | None = None) -> str:
    """Render a public section detail page with citation and warning context."""
    try:
        try:
            lookup = SECTION_STORE.lookup_section(section_ref, as_of=as_of)
        except SectionLifecycleError:
            section = SECTION_STORE.get_section(section_ref)
            lookup = SECTION_STORE.lookup_section(section.section_number, as_of=as_of)
    except SectionLifecycleError as exc:
        return render_error_page(
            "Section not found",
            exc.message,
            exc.fix,
            status_label="Section lookup problem",
        )
    section_number = lookup["section"]["section_number"]
    citation_payload = _build_citation_for_section(section_number, as_of=as_of)
    summaries = []
    for summary in SUMMARY_STORE.list_for_section(lookup["section"]["section_id"]):
        version = SECTION_STORE.get_version(summary.section_version_id)
        summaries.append(
            summary_to_public_dict(
                summary,
                authoritative_section=lookup["section"],
                authoritative_text=version.body,
            )
        )
    warnings = HANDOFF_STORE.public_warnings_for_section(section_number)
    related = [
        related_material_to_public_dict(item)
        for item in SECTION_STORE.related_materials(section_number)["items"]
    ]
    return render_section_page(lookup, citation_payload, summaries, warnings, related)


@app.get("/civiccode/sections/{section_ref}/export", response_class=HTMLResponse)
async def public_section_export(section_ref: str, as_of: date | None = None) -> str:
    """Render an accessible records-ready export page for a section."""
    try:
        export = _build_export_for_section(section_ref, as_of)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail), "fix": "Try again."}
        return render_error_page(
            "Export unavailable",
            detail["message"],
            detail["fix"],
            status_label="Export problem",
        )
    return render_records_ready_export_page(export)


@app.get("/staff/sources", response_class=HTMLResponse)
async def staff_source_workspace(
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> HTMLResponse:
    """Render the staff source registry workspace."""
    try:
        actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    except HTTPException:
        return HTMLResponse(render_staff_source_required_page(), status_code=403)
    sources = [
        source_to_staff_dict(source)
        for source in _get_source_store().list_sources(include_staff_only=True)
    ]
    return HTMLResponse(render_staff_source_workspace(sources, actor=actor))


@app.get("/staff/code", response_class=HTMLResponse)
async def staff_code_workspace(
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> HTMLResponse:
    """Render the staff code lifecycle workspace."""
    try:
        actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    except HTTPException:
        return HTMLResponse(render_staff_code_required_page(), status_code=403)
    return HTMLResponse(render_staff_code_workspace(_staff_code_payload(), actor=actor))


@app.get("/staff/sync", response_class=HTMLResponse)
async def staff_sync_workspace(
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> HTMLResponse:
    """Render the staff codifier sync health workspace."""
    try:
        actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    except HTTPException:
        return HTMLResponse(render_staff_sync_required_page(), status_code=403)
    sources = [
        sync_source_to_dict(source)
        for source in _get_codifier_sync_store().list_sources()
    ]
    return HTMLResponse(render_staff_sync_workspace(sources, actor=actor))


@app.get("/staff/imports", response_class=HTMLResponse)
async def staff_import_ledger(
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> HTMLResponse:
    """Render the staff import job and provenance ledger."""
    try:
        actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    except HTTPException:
        return HTMLResponse(render_staff_import_required_page(), status_code=403)
    return HTMLResponse(render_staff_import_ledger(_staff_import_payload(), actor=actor))


@app.get("/health")
async def health() -> dict[str, str]:
    """Provide a simple operational health check for IT staff."""
    return {
        "status": "ok",
        "service": "civiccode",
        "version": __version__,
        "civiccore": CIVICCORE_VERSION,
    }


@app.get("/api/v1/civiccode/staff/operational-state")
async def get_staff_operational_state(
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Return current operational readiness state for staff operators."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    return _operational_readiness_payload()


@app.get("/api/v1/civiccode/sources/catalog")
async def source_registry_catalog() -> dict[str, Any]:
    """Expose allowed source registry vocabulary for staff integration clients."""
    return {
        "source_types": sorted(SOURCE_TYPES),
        "source_categories": SOURCE_CATEGORIES,
        "source_states": sorted(SOURCE_STATES),
        "import_connector_types": sorted(CONNECTOR_TYPES),
        "source_transitions": {
            status: sorted(targets) for status, targets in SOURCE_TRANSITIONS.items()
        },
    }


@app.post("/api/v1/civiccode/sources", status_code=201)
async def create_source(
    request: SourceCreate,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Register a municipal code source without importing its contents yet."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    data = request.model_dump()
    if data["checksum"] is None and data.get("file_reference"):
        data["checksum"] = compute_reference_checksum(data["file_reference"])
    try:
        source = _get_source_store().create(data)
    except SourceRegistryError as exc:
        _raise_source_error(exc)
    return source_to_staff_dict(source)


@app.get("/api/v1/civiccode/sources")
async def list_public_sources() -> dict[str, Any]:
    """List public-visible sources without exposing staff-only notes."""
    return {
        "sources": [
            source_to_public_dict(source)
            for source in _get_source_store().list_sources(include_staff_only=False)
        ]
    }


@app.get("/api/v1/civiccode/sources/{source_id}")
async def get_public_source(source_id: str) -> dict[str, Any]:
    """Read a public source record without leaking staff-only notes."""
    try:
        source = _get_source_store().get(source_id)
    except SourceRegistryError as exc:
        _raise_source_error(exc)
    if not source.public_visible:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Source '{source_id}' is not public-visible.",
                "fix": "Use the staff source endpoint if you are authorized to view it.",
            },
        )
    return source_to_public_dict(source)


@app.get("/api/v1/civiccode/staff/sources")
async def list_staff_sources(
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """List all registered sources for staff workflows."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    return {
        "sources": [
            source_to_staff_dict(source)
            for source in _get_source_store().list_sources(include_staff_only=True)
        ]
    }


@app.get("/api/v1/civiccode/staff/sources/{source_id}")
async def get_staff_source(
    source_id: str,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Read a staff source record including staff-only notes."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        source = _get_source_store().get(source_id)
    except SourceRegistryError as exc:
        _raise_source_error(exc)
    return source_to_staff_dict(source)


@app.post("/api/v1/civiccode/sources/{source_id}/transitions")
async def transition_source(
    source_id: str,
    request: SourceTransitionRequest,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Transition a source through the official registry lifecycle."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        source = _get_source_store().transition(
            source_id,
            request.to_status,
            actor=request.actor,
            reason=request.reason,
        )
    except SourceRegistryError as exc:
        _raise_source_error(exc)
    return source_to_staff_dict(source)


@app.post("/api/v1/civiccode/titles", status_code=201)
async def create_title(
    request: TitleCreate,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Create a municipal code title container."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        title = SECTION_STORE.create_title(request.model_dump())
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    return title_to_dict(title)


@app.post("/api/v1/civiccode/chapters", status_code=201)
async def create_chapter(
    request: ChapterCreate,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Create a municipal code chapter under a title."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        chapter = SECTION_STORE.create_chapter(request.model_dump())
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    return chapter_to_dict(chapter)


@app.post("/api/v1/civiccode/sections", status_code=201)
async def create_section(
    request: SectionCreate,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Create a code section or subsection without generating answers."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        section = SECTION_STORE.create_section(request.model_dump())
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    return section_to_dict(section)


@app.post("/api/v1/civiccode/sections/{section_id}/versions", status_code=201)
async def create_section_version(
    section_id: str,
    request: SectionVersionCreate,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Create an immutable section version for adopted, pending, or retired text."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    data = request.model_dump()
    if data["section_id"] != section_id:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Path section_id must match request body section_id.",
                "fix": "Use the same section_id in the URL and JSON body.",
            },
        )
    try:
        source = _get_source_store().get(data["source_id"])
    except SourceRegistryError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Source '{data['source_id']}' was not found for this section version.",
                "fix": "Register the source before adding section text from it.",
            },
        ) from exc
    if source.status in {"failed", "superseded"}:
        raise HTTPException(
            status_code=409,
            detail={
                "message": f"Source '{source.source_id}' is {source.status} and cannot back section text.",
                "fix": "Use an active source or refresh the source registry record first.",
            },
        )
    if data["status"] == "adopted" and (source.status != "active" or not source.public_visible):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Adopted section versions require an active public-visible source.",
                "fix": "Activate an official source in the registry before marking text as adopted law.",
            },
        )
    try:
        version = SECTION_STORE.create_version(data)
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    return version_to_dict(version)


@app.get("/api/v1/civiccode/sections/lookup")
async def lookup_section(section_number: str, as_of: date | None = None) -> dict[str, Any]:
    """Lookup adopted section text by current flag or effective date."""
    try:
        payload = SECTION_STORE.lookup_section(section_number, as_of=as_of)
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    payload["handoff_warnings"] = HANDOFF_STORE.public_warnings_for_section(section_number)
    return payload


@app.post("/api/v1/civiccode/sections/resolve")
async def resolve_section(request: SectionResolveRequest) -> dict[str, Any]:
    """Resolve adopted code context for downstream CivicSuite module clients."""
    allowed_consumers = {"CivicZone", "CivicLegal", "CivicAccess", "CivicComms"}
    if request.consumer_module not in allowed_consumers:
        return {
            "status": "refused",
            "reason": "unsupported_consumer_module",
            "message": f"CivicCode does not expose a section-resolution contract for {request.consumer_module}.",
            "fix": f"Use one of: {', '.join(sorted(allowed_consumers))}.",
            "consumer_module": request.consumer_module,
            "code_answer_behavior": "not_available",
        }
    query = (request.query or "").strip()
    if query and (is_legal_advice_query(query) or looks_like_legal_determination(query)):
        refused = build_grounded_answer(
            QuestionRequestContext(question=query, section_number=request.section_number, as_of=request.as_of),
            search=SECTION_STORE.search,
            build_citation=_build_citation_for_section,
        )
        refused["consumer_module"] = request.consumer_module
        return refused
    section_number = request.section_number
    resolution_mode = "exact_section"
    if section_number is None:
        if not query:
            return {
                "status": "refused",
                "reason": "missing_resolution_input",
                "message": "Section resolution requires section_number or query.",
                "fix": "Send an exact section_number when possible; use query only for public-safe code-text matching.",
                "consumer_module": request.consumer_module,
                "code_answer_behavior": "not_available",
            }
        search_payload = SECTION_STORE.search(query)
        matches = [
            result
            for result in search_payload["results"]
            if result.get("result_type") == "code_section" and result.get("section_number")
        ]
        if len(matches) != 1:
            return {
                "status": "refused",
                "reason": "ambiguous_resolution" if matches else "no_resolution",
                "message": f"{len(matches)} adopted code sections matched the resolution query.",
                "fix": "Send an exact section_number so CivicCode can resolve one authoritative section.",
                "consumer_module": request.consumer_module,
                "code_answer_behavior": "not_available",
            }
        section_number = matches[0]["section_number"]
        resolution_mode = "query_single_match"
    try:
        lookup = SECTION_STORE.lookup_section(section_number, as_of=request.as_of)
    except SectionLifecycleError as exc:
        return {
            "status": "refused",
            "reason": "section_lookup",
            "message": exc.message,
            "fix": exc.fix,
            "consumer_module": request.consumer_module,
            "code_answer_behavior": "not_available",
        }
    citation_payload = _build_citation_for_section(section_number, as_of=request.as_of)
    if citation_payload.get("status") != "ok":
        citation_payload["consumer_module"] = request.consumer_module
        return citation_payload
    warnings = HANDOFF_STORE.public_warnings_for_section(section_number)
    return {
        "status": "ok",
        "consumer_module": request.consumer_module,
        "resolution_mode": resolution_mode,
        "section": lookup["section"],
        "version": lookup["version"],
        "citation": citation_payload["citation"],
        "handoff_warnings": warnings,
        "version_context": {
            "as_of": request.as_of.isoformat() if request.as_of else lookup["as_of"],
            "preserves_date_context": True,
        },
        "legal_boundary": {
            "classification": "information_not_determination",
            "legal_determination": "not_provided",
            "legal_advice": "not_provided",
            "pending_language_is_adopted_law": False,
        },
        "stable_contract": {
            "contract_name": "civiccode.section_resolution.v1",
            "guarantee": "Resolved payload cites one adopted section/version/source or returns a structured refusal.",
        },
        "downstream_usage": {
            "CivicZone": "Use citations for zoning-context explanations, not official determinations.",
            "CivicLegal": "Use as city-code source context; attorney review controls legal conclusions.",
            "CivicAccess": "Use for accessible/plain-language transforms while retaining authoritative text.",
            "CivicComms": "Use for public explainers with exact citation and no advocacy or legal advice.",
        }[request.consumer_module],
        "code_answer_behavior": "section_resolution",
    }


@app.get("/api/v1/civiccode/sections/{section_id}/history")
async def section_history(section_id: str) -> dict[str, Any]:
    """Return immutable amendment/version history for a section."""
    try:
        return SECTION_STORE.section_history(section_id)
    except SectionLifecycleError as exc:
        _raise_section_error(exc)


@app.get("/api/v1/civiccode/sections/{section_id}/permalink")
async def section_permalink(section_id: str) -> dict[str, Any]:
    """Return the stable public-facing permalink for a section."""
    try:
        return SECTION_STORE.permalink(section_id)
    except SectionLifecycleError as exc:
        _raise_section_error(exc)


@app.get("/api/v1/civiccode/search")
async def search_sections(q: str) -> dict[str, Any]:
    """Search public-visible code sections and related public materials."""
    try:
        return SECTION_STORE.search(q)
    except SectionLifecycleError as exc:
        _raise_section_error(exc)


@app.get("/api/v1/civiccode/popular-questions")
async def list_popular_questions() -> dict[str, Any]:
    """List staff-approved public popular questions as navigation aids."""
    questions = [
        popular_question_to_public_dict(question)
        for question in _get_popular_question_store().public_popular_questions()
    ]
    return {
        "questions": questions,
        "count": len(questions),
        "classification": "navigation_aid_not_legal_determination",
        "legal_determination": "not_provided",
        "code_answer_behavior": "navigation_aid",
        "empty_state": None
        if questions
        else {
            "message": "No staff-approved popular questions are published yet.",
            "fix": "Search by section number or ask the City Clerk to approve public questions.",
        },
    }


@app.post("/api/v1/civiccode/staff/popular-questions", status_code=201)
async def create_popular_question(
    request: PopularQuestionCreate,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Create a staff-approved public popular question tied to cited adopted code."""
    actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    question_text = request.question_text.strip()
    if is_legal_advice_query(question_text) or looks_like_legal_determination(question_text):
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Popular questions cannot ask CivicCode for a legal determination.",
                "fix": (
                    "Rewrite the question as a navigation prompt, such as "
                    "'Where do I read the backyard chicken permit rule?'"
                ),
            },
        )
    citation_payload = _build_citation_for_section(request.section_number)
    if citation_payload.get("status") != "ok":
        raise HTTPException(
            status_code=409,
            detail={
                "message": citation_payload.get("reason", "Citation could not be built."),
                "fix": citation_payload.get("fix", "Attach the question to cited adopted code."),
            },
        )
    try:
        lookup = SECTION_STORE.lookup_section(request.section_number)
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    citation = citation_payload["citation"]
    try:
        question = _get_popular_question_store().create(
            {
                **request.model_dump(),
                "section_id": citation["section_id"],
                "section_number": citation["section_number"],
                "section_heading": lookup["section"]["section_heading"],
                "citation_payload": citation_payload,
            },
            actor=actor,
        )
    except PublicDiscoveryError as exc:
        _raise_public_discovery_error(exc)
    return popular_question_to_public_dict(question)


@app.get("/api/v1/civiccode/sections/{section_number}/related")
async def related_materials(section_number: str) -> dict[str, Any]:
    """List explicit public related materials for one adopted section."""
    try:
        payload = SECTION_STORE.related_materials(section_number)
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    return {
        **payload,
        "items": [related_material_to_public_dict(item) for item in payload["items"]],
    }


@app.get("/api/v1/civiccode/citations/build")
async def build_citation(section_number: str, as_of: date | None = None) -> dict[str, Any]:
    """Build a deterministic citation object or a structured refusal."""
    return _build_citation_for_section(section_number, as_of)


@app.get("/api/v1/civiccode/sections/{section_ref}/export")
async def export_section(section_ref: str, as_of: date | None = None) -> dict[str, Any]:
    """Return a records-ready section export with citation and source provenance."""
    return _build_export_for_section(section_ref, as_of)


@app.post("/api/v1/civiccode/questions/answer")
async def answer_question(request: QuestionAnswerRequest) -> dict[str, Any]:
    """Answer code questions only when an adopted section citation grounds them."""
    payload = build_grounded_answer(
        QuestionRequestContext(
            question=request.question,
            section_number=request.section_number,
            as_of=request.as_of,
        ),
        search=SECTION_STORE.search,
        build_citation=_build_citation_for_section,
    )
    payload["audience"] = "public"
    return payload


@app.post("/api/v1/civiccode/staff/sections/{section_id}/notes", status_code=201)
async def create_interpretation_note(
    section_id: str,
    request: InterpretationNoteCreate,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Create a staff-only interpretation note without exposing it publicly."""
    actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        SECTION_STORE.get_section(section_id)
        note = STAFF_NOTE_STORE.create_note(
            section_id,
            request.model_dump(),
            actor=actor,
        )
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    except StaffWorkbenchError as exc:
        _raise_staff_error(exc)
    return note_to_staff_dict(note)


@app.get("/api/v1/civiccode/staff/sections/{section_id}/notes")
async def list_interpretation_notes(
    section_id: str,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """List staff-only interpretation notes for authorized staff clients."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        SECTION_STORE.get_section(section_id)
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    return {"notes": [note_to_staff_dict(note) for note in STAFF_NOTE_STORE.list_notes(section_id)]}


@app.get("/api/v1/civiccode/staff/audit-events")
async def list_staff_audit_events(
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """List staff workbench audit events for authorized staff clients."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    events = [
        *[audit_event_to_dict(event) for event in STAFF_NOTE_STORE.audit_events()],
        *[summary_audit_event_to_dict(event) for event in SUMMARY_STORE.audit_events()],
        *[handoff_audit_event_to_dict(event) for event in HANDOFF_STORE.audit_events()],
    ]
    events.sort(key=lambda event: event["created_at"])
    return {"events": events}


@app.post("/api/v1/civiccode/staff/imports/local-bundle", status_code=201)
async def create_local_import_job(
    request: ImportBundleCreate,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Import a local codifier/file-drop fixture without outbound network calls."""
    actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    job = _get_import_store().run_import(request.model_dump(), actor=actor)
    return job_to_dict(job)


@app.get("/api/v1/civiccode/staff/imports")
async def list_import_jobs(
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """List local import jobs and their visible success/failure states."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    return {"imports": [job_to_dict(job) for job in _get_import_store().list_jobs()]}


@app.get("/api/v1/civiccode/staff/imports/{job_id}")
async def get_import_job(
    job_id: str,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Read a local import job, including actionable failure details."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        job = _get_import_store().get(job_id)
    except CivicCodeImportError as exc:
        _raise_import_error(exc)
    return job_to_dict(job)


@app.post("/api/v1/civiccode/staff/imports/{job_id}/retry", status_code=201)
async def retry_import_job(
    job_id: str,
    request: ImportBundleCreate,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Retry a failed import job with a corrected local bundle."""
    actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        job = _get_import_store().retry_import(job_id, request.model_dump(), actor=actor)
    except CivicCodeImportError as exc:
        _raise_import_error(exc)
    return job_to_dict(job)


@app.get("/api/v1/civiccode/staff/imports/{job_id}/provenance")
async def get_import_provenance(
    job_id: str,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Return a provenance report for a local import job."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        job = _get_import_store().get(job_id)
    except CivicCodeImportError as exc:
        _raise_import_error(exc)
    return provenance_report(job, _get_source_store())


@app.get("/api/v1/civiccode/staff/imports/{job_id}/tree")
async def get_imported_tree(
    job_id: str,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Show imported title/chapter/section/version tree for staff verification."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        job = _get_import_store().get(job_id)
        if job.status != "completed" or not job.source_id:
            raise CivicCodeImportError(
                f"Import job '{job_id}' does not have a completed source tree.",
                "Open the job details, fix the failure, and retry before reading its imported tree.",
                status_code=409,
            )
        return imported_tree_snapshot(job.source_id, _get_source_store(), SECTION_STORE)
    except CivicCodeImportError as exc:
        _raise_import_error(exc)
    except SourceRegistryError as exc:
        _raise_source_error(exc)


@app.post("/api/v1/civiccode/staff/sync/codifier-sources", status_code=201)
async def configure_codifier_sync_source(
    request: CodifierSyncConfigureRequest,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Enable staff-controlled codifier sync readiness for an official source."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        source = _get_codifier_sync_store().configure_source(
            source_id=request.source_id,
            sync_schedule=request.sync_schedule,
            allowlisted_hosts=tuple(request.allowlisted_hosts),
        )
    except CodifierSyncError as exc:
        _raise_codifier_sync_error(exc)
    except SourceRegistryError as exc:
        _raise_source_error(exc)
    return sync_source_to_dict(source)


@app.get("/api/v1/civiccode/staff/sync/codifier-sources")
async def list_codifier_sync_sources(
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """List codifier sync readiness and circuit health for staff."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    return {
        "sources": [
            sync_source_to_dict(source)
            for source in _get_codifier_sync_store().list_sources()
        ]
    }


@app.post("/api/v1/civiccode/staff/sync/codifier-sources/{source_id}/run", status_code=201)
async def run_codifier_sync_source(
    source_id: str,
    request: CodifierSyncRunRequest,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Run one staff-controlled codifier sync using an already fetched local payload."""
    actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        run = _get_codifier_sync_store().run_local_payload(
            source_id=source_id,
            payload=request.payload.model_dump(),
            actor=actor,
            changed_since=request.changed_since,
        )
    except CodifierSyncError as exc:
        _raise_codifier_sync_error(exc)
    return run.public_dict()


@app.post("/api/v1/civiccode/staff/civicclerk/ordinance-events", status_code=201)
async def create_civicclerk_ordinance_event(
    request: CivicClerkOrdinanceEventCreate,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Receive CivicClerk ordinance/adoption events without codifying them."""
    actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        for section_number in request.affected_sections:
            SECTION_STORE.lookup_section(section_number)
        event = HANDOFF_STORE.create_event(request.model_dump(), actor=actor)
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    except OrdinanceHandoffError as exc:
        _raise_handoff_error(exc)
    return event_to_dict(event)


@app.post("/api/v1/civiccode/staff/civicclerk/ordinance-events/{event_id}/resolve")
async def resolve_civicclerk_ordinance_event(
    event_id: str,
    request: CivicClerkOrdinanceEventResolve,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Mark a CivicClerk handoff codified after staff creates the adopted code version."""
    actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        version = SECTION_STORE.get_version(request.section_version_id)
        section = SECTION_STORE.get_section(version.section_id)
        event = next((item for item in HANDOFF_STORE.list_events() if item.event_id == event_id), None)
        if event is None:
            raise OrdinanceHandoffError(
                f"CivicClerk ordinance event '{event_id}' was not found.",
                "Read the handoff list and resolve an existing event.",
                status_code=404,
            )
        if section.section_number not in event.affected_sections:
            raise OrdinanceHandoffError(
                "Resolved section version does not belong to an affected section.",
                "Create or select an adopted version for one of the handoff's affected_sections.",
                status_code=409,
            )
        if version.status != "adopted" or not version.is_current:
            raise OrdinanceHandoffError(
                "Resolved handoffs require a current adopted section version.",
                "Create the codified adopted version and mark it current before resolving the handoff.",
                status_code=409,
            )
        event = HANDOFF_STORE.resolve_event(
            event_id,
            actor=actor,
            section_version_id=request.section_version_id,
        )
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    except OrdinanceHandoffError as exc:
        _raise_handoff_error(exc)
    return event_to_dict(event)


@app.post("/api/v1/civiccode/staff/sections/{section_id}/summaries", status_code=201)
async def create_plain_language_summary(
    section_id: str,
    request: PlainLanguageSummaryCreate,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Create a staff-drafted plain-language summary tied to adopted code text."""
    actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        SECTION_STORE.get_section(section_id)
        version = SECTION_STORE.get_version(request.section_version_id)
        if version.section_id != section_id:
            raise PlainLanguageSummaryError(
                "Plain-language summary section does not match the cited section version.",
                "Use a section_version_id that belongs to the section in the request URL.",
                status_code=409,
            )
        if version.status != "adopted":
            raise PlainLanguageSummaryError(
                "Plain-language summaries require an adopted section version.",
                "Attach summaries only to adopted law, not draft or pending text.",
            )
        summary = SUMMARY_STORE.create_summary(
            section_id,
            request.model_dump(),
            actor=actor,
        )
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    except PlainLanguageSummaryError as exc:
        _raise_summary_error(exc)
    return summary_to_staff_dict(summary)


@app.post("/api/v1/civiccode/staff/summaries/{summary_id}/approve")
async def approve_plain_language_summary(
    summary_id: str,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Approve a plain-language summary for public display after staff review."""
    actor = _require_staff(x_civiccode_role, x_civiccode_actor)
    try:
        summary = SUMMARY_STORE.get_summary(summary_id)
        version = SECTION_STORE.get_version(summary.section_version_id)
        if version.status != "adopted":
            raise PlainLanguageSummaryError(
                "Only summaries tied to adopted section text can be approved.",
                "Attach the summary to an adopted section version before approving it.",
                status_code=409,
            )
        summary = SUMMARY_STORE.approve_summary(summary_id, actor=actor)
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    except PlainLanguageSummaryError as exc:
        _raise_summary_error(exc)
    return summary_to_staff_dict(summary)


@app.get("/api/v1/civiccode/sections/{section_id}/summaries")
async def list_public_plain_language_summaries(section_id: str) -> dict[str, Any]:
    """List public approved summaries while keeping authoritative code visible."""
    try:
        section = SECTION_STORE.get_section(section_id)
        summaries = []
        for summary in SUMMARY_STORE.list_for_section(section_id):
            version = SECTION_STORE.get_version(summary.section_version_id)
            summaries.append(
                summary_to_public_dict(
                    summary,
                    authoritative_section={
                        "section_id": section.section_id,
                        "section_number": section.section_number,
                        "section_heading": section.section_heading,
                    },
                    authoritative_text=version.body,
                )
            )
    except SectionLifecycleError as exc:
        _raise_section_error(exc)
    return {
        "section_id": section_id,
        "summaries": summaries,
        "count": len(summaries),
        "code_answer_behavior": "not_available",
    }


@app.post("/api/v1/civiccode/staff/questions/answer")
async def answer_staff_question(
    request: QuestionAnswerRequest,
    x_civiccode_role: str | None = Header(default=None),
    x_civiccode_actor: str | None = Header(default=None),
) -> dict[str, Any]:
    """Answer staff questions with staff-only notes kept out of public responses."""
    _require_staff(x_civiccode_role, x_civiccode_actor)
    payload = build_grounded_answer(
        QuestionRequestContext(
            question=request.question,
            section_number=request.section_number,
            as_of=request.as_of,
        ),
        search=SECTION_STORE.search,
        build_citation=_build_citation_for_section,
    )
    payload["audience"] = "staff"
    if payload.get("status") == "ok":
        section_id = payload["citations"][0]["section_id"]
        payload["staff_context"] = {
            "warning": "staff_only_do_not_publish",
            "notes": [
                note_to_staff_dict(note)
                for note in STAFF_NOTE_STORE.list_notes(section_id)
                if note.status == "approved"
            ],
        }
    return payload


def _build_citation_for_section(section_number: str, as_of: date | None = None) -> dict[str, Any]:
    try:
        context = SECTION_STORE.citation_context(section_number, as_of=as_of)
    except SectionLifecycleError as exc:
        return refusal(exc.message, exc.fix, "section_lookup")
    source_id = context["version"]["source_id"]
    try:
        source = _get_source_store().get(source_id)
    except SourceRegistryError:
        return refusal(
            f"Source '{source_id}' was not found for this citation.",
            "Register or restore the source before building a citation.",
            "missing_source",
        )
    if source.status != "active":
        return refusal(
            f"Source '{source.source_id}' is {source.status}, not active.",
            "Refresh or reactivate the source before using it for citations.",
            "stale_source",
        )
    return build_citation_payload(
        section=context["section"],
        version=context["version"],
        title=context["title"],
        chapter=context["chapter"],
        source=source_to_public_dict(source),
        as_of=context["as_of"],
    )


def _build_export_for_section(section_ref: str, as_of: date | None = None) -> dict[str, Any]:
    try:
        try:
            lookup = SECTION_STORE.lookup_section(section_ref, as_of=as_of)
        except SectionLifecycleError:
            section = SECTION_STORE.get_section(section_ref)
            lookup = SECTION_STORE.lookup_section(section.section_number, as_of=as_of)
    except SectionLifecycleError as exc:
        _raise_section_error(exc)

    section_number = lookup["section"]["section_number"]
    citation_payload = _build_citation_for_section(section_number, as_of)
    if citation_payload.get("status") != "ok":
        raise HTTPException(
            status_code=409,
            detail={
                "message": citation_payload.get("reason", "Citation could not be built for this export."),
                "fix": citation_payload.get("fix", "Refresh the source and try exporting again."),
            },
        )
    try:
        source = _get_source_store().get(citation_payload["citation"]["source_id"])
    except SourceRegistryError as exc:
        _raise_source_error(exc)
    return build_records_ready_export(
        lookup=lookup,
        citation_payload=citation_payload,
        source=source_to_public_dict(source),
    )


def _get_source_store() -> SourceRegistryRepository | SourceRegistryStore:
    global _source_registry_db_url, _source_registry_repository
    db_url = os.environ.get("CIVICCODE_SOURCE_REGISTRY_DB_URL")
    if db_url is None:
        return SOURCE_STORE
    if _source_registry_repository is None or db_url != _source_registry_db_url:
        _source_registry_db_url = db_url
        _source_registry_repository = SourceRegistryRepository(db_url=db_url)
    return _source_registry_repository


def _get_popular_question_store() -> PopularQuestionRepository | PopularQuestionStore:
    global _popular_question_db_url, _popular_question_repository
    db_url = os.environ.get("CIVICCODE_SOURCE_REGISTRY_DB_URL")
    if db_url is None:
        return POPULAR_QUESTION_STORE
    if _popular_question_repository is None or db_url != _popular_question_db_url:
        _popular_question_db_url = db_url
        _popular_question_repository = PopularQuestionRepository(db_url=db_url)
    return _popular_question_repository


def _get_section_store() -> SectionLifecycleRepository | SectionLifecycleStore:
    global _section_lifecycle_db_url, _section_lifecycle_repository
    db_url = os.environ.get("CIVICCODE_SOURCE_REGISTRY_DB_URL")
    if db_url is None:
        return SECTION_STORE
    if _section_lifecycle_repository is None or db_url != _section_lifecycle_db_url:
        _section_lifecycle_db_url = db_url
        _section_lifecycle_repository = SectionLifecycleRepository(db_url=db_url)
    return _section_lifecycle_repository


def _source_store_key() -> str:
    return os.environ.get("CIVICCODE_SOURCE_REGISTRY_DB_URL") or "memory"


def _get_import_store() -> ImportConnectorStore:
    global _import_store, _import_store_source_key
    source_key = _source_store_key()
    if source_key == "memory":
        return IMPORT_STORE
    if _import_store is None or _import_store_source_key != source_key:
        _import_store_source_key = source_key
        _import_store = ImportConnectorRepository(
            source_store=_get_source_store(),
            section_store=SECTION_STORE,
            db_url=source_key,
        )
    return _import_store


def _get_codifier_sync_store() -> CodifierSyncStore:
    global _codifier_sync_store, _codifier_sync_store_source_key
    source_key = _source_store_key()
    if source_key == "memory":
        return CODIFIER_SYNC_STORE
    if _codifier_sync_store is None or _codifier_sync_store_source_key != source_key:
        _codifier_sync_store_source_key = source_key
        _codifier_sync_store = CodifierSyncRepository(
            source_store=_get_source_store(),
            import_store=_get_import_store(),
            db_url=source_key,
        )
    return _codifier_sync_store


def _seed_demo_city_if_enabled() -> None:
    """Populate a deterministic Brookfield demo when CIVICCODE_DEMO_SEED is enabled."""
    global _demo_seed_key
    if os.environ.get("CIVICCODE_DEMO_SEED", "").strip().lower() not in {"1", "true", "yes"}:
        return
    seed_key = f"{_source_store_key()}:brookfield-v1"
    if _demo_seed_key == seed_key:
        return

    actor = os.environ.get("CIVICCODE_DEMO_ACTOR", "demo-seed@brookfield.example.gov")
    import_store = _get_import_store()
    for contract in mock_city_codifier_contracts():
        payload = mock_city_import_payload(contract)
        for version in payload.get("versions", []):
            if isinstance(version.get("effective_start"), str):
                version["effective_start"] = date.fromisoformat(version["effective_start"])
            if isinstance(version.get("effective_end"), str):
                version["effective_end"] = date.fromisoformat(version["effective_end"])
        import_store.run_import(payload, actor=actor)

    try:
        SUMMARY_STORE.create_summary(
            "sec_municode_sample",
            {
                "summary_id": "summary_brookfield_chickens",
                "section_version_id": "version_municode_current",
                "summary_text": (
                    "Residents can find the adopted Brookfield chicken-permit "
                    "rule here, but this summary is not law."
                ),
            },
            actor=actor,
        )
        SUMMARY_STORE.approve_summary("summary_brookfield_chickens", actor=actor)
    except PlainLanguageSummaryError:
        pass

    try:
        STAFF_NOTE_STORE.create_note(
            "sec_municode_sample",
            {
                "note_id": "note_brookfield_staff_permit_routing",
                "note_text": (
                    "Route permit-processing interpretation questions to the "
                    "Planning counter before publishing resident guidance."
                ),
                "status": "approved",
            },
            actor=actor,
        )
    except StaffWorkbenchError:
        pass

    try:
        HANDOFF_STORE.create_event(
            {
                "event_id": "ord_brookfield_2026_041",
                "external_event_id": "cc_event_2026_041",
                "civicclerk_meeting_id": "meeting_2026_04_27",
                "civicclerk_agenda_item_id": "agenda_14",
                "ordinance_number": "2026-041",
                "title": "Ordinance amending backyard chicken permits",
                "status": "adopted",
                "affected_sections": ["6.12.040"],
                "source_document_url": "https://brookfield.example.gov/minutes/2026-041.pdf",
                "source_document_hash": "sha256:brookfield-demo-ordinance-2026-041",
                "ordinance_text": "An ordinance amending Section 6.12.040.",
            },
            actor=actor,
        )
    except OrdinanceHandoffError:
        pass

    try:
        citation_payload = _build_citation_for_section("6.12.040")
        if citation_payload.get("status") == "ok":
            _get_popular_question_store().create(
                {
                    "question_id": "popular_brookfield_chickens",
                    "question_text": "Where do I read the backyard chicken permit rule?",
                    "section_id": "sec_municode_sample",
                    "section_number": "6.12.040",
                    "section_heading": "Backyard chickens",
                    "answer_excerpt": (
                        "Open Section 6.12.040 for the adopted chicken-permit rule "
                        "and its official source citation."
                    ),
                    "citation_payload": citation_payload,
                    "status": "approved",
                    "audience": "public",
                    "is_popular": True,
                },
                actor=actor,
            )
    except PublicDiscoveryError:
        pass

    _demo_seed_key = seed_key
