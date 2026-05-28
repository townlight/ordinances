from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from civiccode.import_connectors import ImportConnectorRepository
from civiccode.main import app
from civiccode.mock_city_environment import mock_city_codifier_contracts, mock_city_import_payload
from civiccode.ordinance_handoff import OrdinanceHandoffRepository
from civiccode.plain_language import PlainLanguageSummaryRepository
from civiccode.public_discovery import PopularQuestionRepository
from civiccode.staff_workbench import StaffWorkbenchRepository
from civiccode.source_registry import SourceRegistryRepository


from conftest import build_suite_staff_headers

STAFF_HEADERS = build_suite_staff_headers()


def active_official_source(source_id: str = "municode_persistent") -> dict[str, object]:
    return {
        "source_id": source_id,
        "name": "Example Municipal Code",
        "publisher": "Municode",
        "source_type": "municode",
        "source_category": "municipal_code",
        "source_url": "https://library.municode.com/example/codes/code_of_ordinances",
        "retrieved_at": "2026-04-27T12:00:00Z",
        "retrieval_method": "official_web_export",
        "source_owner": "City Clerk",
        "is_official": True,
        "status": "active",
        "staff_notes": "Internal source review note.",
    }


def test_source_registry_records_persist_status_and_staff_notes(tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path / 'sources.db'}"
    first = SourceRegistryRepository(db_url=db_url)
    created = first.create(active_official_source())
    transitioned = first.transition(
        created.source_id,
        "stale",
        actor="clerk@example.gov",
        reason="Publisher posted a newer official export.",
    )

    second = SourceRegistryRepository(db_url=db_url)
    persisted = second.get(created.source_id)

    assert transitioned.status == "stale"
    assert persisted.status == "stale"
    assert persisted.staff_notes == "Internal source review note."
    assert persisted.source_owner == "City Clerk"


@pytest.mark.asyncio
async def test_api_sources_use_configured_database(monkeypatch, tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path / 'api-sources.db'}"
    monkeypatch.setenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", db_url)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        created = await client.post(
            "/api/v1/civiccode/sources",
            headers=STAFF_HEADERS,
            json=active_official_source(),
        )
        transitioned = await client.post(
            "/api/v1/civiccode/sources/municode_persistent/transitions",
            headers=STAFF_HEADERS,
            json={
                "to_status": "stale",
                "actor": "clerk@example.gov",
                "reason": "Publisher posted a newer official export.",
            },
        )
        public = await client.get("/api/v1/civiccode/sources/municode_persistent")

    second = SourceRegistryRepository(db_url=db_url)
    persisted = second.get("municode_persistent")

    assert created.status_code == 201
    assert transitioned.status_code == 200
    assert transitioned.json()["status"] == "stale"
    assert public.status_code == 200
    assert "staff_notes" not in public.json()
    assert persisted.status == "stale"
    assert persisted.staff_notes == "Internal source review note."


@pytest.mark.asyncio
async def test_api_popular_questions_use_configured_database(monkeypatch, tmp_path) -> None:
    import civiccode.main as app_module

    db_url = f"sqlite:///{tmp_path / 'api-discovery.db'}"
    monkeypatch.setenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", db_url)
    app_module.SOURCE_STORE.reset()
    app_module.SECTION_STORE.reset()
    app_module.POPULAR_QUESTION_STORE.reset()
    app_module._source_registry_repository = None
    app_module._popular_question_repository = None

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        assert (
            await client.post(
                "/api/v1/civiccode/sources",
                headers=STAFF_HEADERS,
                json=active_official_source("municode_discovery"),
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/titles",
                headers=STAFF_HEADERS,
                json={"title_id": "title_6", "title_number": "6", "title_name": "Animals"},
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/chapters",
                headers=STAFF_HEADERS,
                json={
                    "chapter_id": "chapter_6_12",
                    "title_id": "title_6",
                    "chapter_number": "6.12",
                    "chapter_name": "Urban Livestock",
                },
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/sections",
                headers=STAFF_HEADERS,
                json={
                    "section_id": "sec_chickens",
                    "chapter_id": "chapter_6_12",
                    "section_number": "6.12.040",
                    "section_heading": "Backyard chickens",
                },
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/sections/sec_chickens/versions",
                headers=STAFF_HEADERS,
                json={
                    "version_id": "v_chickens_current",
                    "section_id": "sec_chickens",
                    "source_id": "municode_discovery",
                    "version_label": "Current",
                    "body": "Residents may keep up to six backyard chickens with a city permit.",
                    "effective_start": "2026-01-01",
                    "status": "adopted",
                    "is_current": True,
                },
            )
        ).status_code == 201
        created = await client.post(
            "/api/v1/civiccode/staff/popular-questions",
            headers=STAFF_HEADERS,
            json={
                "question_id": "popular_chickens",
                "question_text": "Where do I read the backyard chicken permit rule?",
                "section_number": "6.12.040",
                "answer_excerpt": "Open Section 6.12.040 for adopted chicken-permit code text.",
            },
        )

    app_module._popular_question_repository = None
    persisted = PopularQuestionRepository(db_url=db_url).public_popular_questions()

    assert created.status_code == 201
    assert [question.question_id for question in persisted] == ["popular_chickens"]
    assert persisted[0].approved_by == "clerk@example.gov"


@pytest.mark.asyncio
async def test_api_section_lifecycle_uses_configured_database(monkeypatch, tmp_path) -> None:
    import civiccode.main as app_module

    db_url = f"sqlite:///{tmp_path / 'api-sections.db'}"
    monkeypatch.setenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", db_url)
    app_module.SOURCE_STORE.reset()
    app_module.SECTION_STORE.reset()
    app_module._source_registry_repository = None
    app_module._section_lifecycle_repository = None

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        assert (
            await client.post(
                "/api/v1/civiccode/sources",
                headers=STAFF_HEADERS,
                json=active_official_source("municode_sections"),
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/titles",
                headers=STAFF_HEADERS,
                json={"title_id": "title_6", "title_number": "6", "title_name": "Animals"},
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/chapters",
                headers=STAFF_HEADERS,
                json={
                    "chapter_id": "chapter_6_12",
                    "title_id": "title_6",
                    "chapter_number": "6.12",
                    "chapter_name": "Urban Livestock",
                },
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/sections",
                headers=STAFF_HEADERS,
                json={
                    "section_id": "sec_chickens",
                    "chapter_id": "chapter_6_12",
                    "section_number": "6.12.040",
                    "section_heading": "Backyard chickens",
                },
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/sections/sec_chickens/versions",
                headers=STAFF_HEADERS,
                json={
                    "version_id": "v_chickens_current",
                    "section_id": "sec_chickens",
                    "source_id": "municode_sections",
                    "version_label": "Current",
                    "body": "Residents may keep up to six backyard chickens with a city permit.",
                    "effective_start": "2026-01-01",
                    "status": "adopted",
                    "is_current": True,
                },
            )
        ).status_code == 201

    app_module._section_lifecycle_repository = None
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        persisted = await client.get(
            "/api/v1/civiccode/sections/lookup",
            params={"section_number": "6.12.040"},
        )

    assert persisted.status_code == 200
    assert persisted.json()["version"]["version_id"] == "v_chickens_current"
    assert "six backyard chickens" in persisted.json()["version"]["body"]


@pytest.mark.asyncio
async def test_api_staff_notes_use_configured_database(monkeypatch, tmp_path) -> None:
    import civiccode.main as app_module

    db_url = f"sqlite:///{tmp_path / 'api-staff-notes.db'}"
    monkeypatch.setenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", db_url)
    app_module.SOURCE_STORE.reset()
    app_module.SECTION_STORE.reset()
    app_module.STAFF_NOTE_STORE.reset()
    app_module._source_registry_repository = None
    app_module._section_lifecycle_repository = None
    app_module._staff_workbench_repository = None

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        assert (
            await client.post(
                "/api/v1/civiccode/sources",
                headers=STAFF_HEADERS,
                json=active_official_source("municode_staff_notes"),
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/titles",
                headers=STAFF_HEADERS,
                json={"title_id": "title_6", "title_number": "6", "title_name": "Animals"},
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/chapters",
                headers=STAFF_HEADERS,
                json={
                    "chapter_id": "chapter_6_12",
                    "title_id": "title_6",
                    "chapter_number": "6.12",
                    "chapter_name": "Urban Livestock",
                },
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/sections",
                headers=STAFF_HEADERS,
                json={
                    "section_id": "sec_chickens",
                    "chapter_id": "chapter_6_12",
                    "section_number": "6.12.040",
                    "section_heading": "Backyard chickens",
                },
            )
        ).status_code == 201
        created = await client.post(
            "/api/v1/civiccode/staff/sections/sec_chickens/notes",
            headers=STAFF_HEADERS,
            json={
                "note_id": "note_chicken_permits",
                "note_text": "Confirm permit routing with Community Development before advising residents.",
                "status": "approved",
            },
        )

    app_module._staff_workbench_repository = None
    persisted = StaffWorkbenchRepository(db_url=db_url)

    assert created.status_code == 201
    notes = persisted.list_notes("sec_chickens")
    assert [note.note_id for note in notes] == ["note_chicken_permits"]
    assert notes[0].created_by == "clerk@example.gov"
    assert persisted.audit_events()[0].event_type == "interpretation_note_created"


@pytest.mark.asyncio
async def test_api_plain_language_summaries_use_configured_database(monkeypatch, tmp_path) -> None:
    import civiccode.main as app_module

    db_url = f"sqlite:///{tmp_path / 'api-summaries.db'}"
    monkeypatch.setenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", db_url)
    app_module.SOURCE_STORE.reset()
    app_module.SECTION_STORE.reset()
    app_module.SUMMARY_STORE.reset()
    app_module._source_registry_repository = None
    app_module._section_lifecycle_repository = None
    app_module._plain_language_repository = None

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        assert (
            await client.post(
                "/api/v1/civiccode/sources",
                headers=STAFF_HEADERS,
                json=active_official_source("municode_summaries"),
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/titles",
                headers=STAFF_HEADERS,
                json={"title_id": "title_6", "title_number": "6", "title_name": "Animals"},
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/chapters",
                headers=STAFF_HEADERS,
                json={
                    "chapter_id": "chapter_6_12",
                    "title_id": "title_6",
                    "chapter_number": "6.12",
                    "chapter_name": "Urban Livestock",
                },
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/sections",
                headers=STAFF_HEADERS,
                json={
                    "section_id": "sec_chickens",
                    "chapter_id": "chapter_6_12",
                    "section_number": "6.12.040",
                    "section_heading": "Backyard chickens",
                },
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/sections/sec_chickens/versions",
                headers=STAFF_HEADERS,
                json={
                    "version_id": "v_chickens_current",
                    "section_id": "sec_chickens",
                    "source_id": "municode_summaries",
                    "version_label": "Current",
                    "body": "Residents may keep up to six backyard chickens with a city permit.",
                    "effective_start": "2026-01-01",
                    "status": "adopted",
                    "is_current": True,
                },
            )
        ).status_code == 201
        created = await client.post(
            "/api/v1/civiccode/staff/sections/sec_chickens/summaries",
            headers=STAFF_HEADERS,
            json={
                "summary_id": "summary_chicken_permits",
                "section_version_id": "v_chickens_current",
                "summary_text": "Residents can keep a small backyard flock after getting a permit.",
            },
        )
        approved = await client.post(
            "/api/v1/civiccode/staff/summaries/summary_chicken_permits/approve",
            headers=STAFF_HEADERS,
        )

    app_module._plain_language_repository = None
    persisted = PlainLanguageSummaryRepository(db_url=db_url)

    assert created.status_code == 201
    assert approved.status_code == 200
    summaries = persisted.list_for_section("sec_chickens")
    assert [summary.summary_id for summary in summaries] == ["summary_chicken_permits"]
    assert summaries[0].approved_by == "clerk@example.gov"
    assert [event.event_type for event in persisted.audit_events()] == [
        "plain_language_summary_created",
        "plain_language_summary_approved",
    ]


@pytest.mark.asyncio
async def test_api_civicclerk_handoffs_use_configured_database(monkeypatch, tmp_path) -> None:
    import civiccode.main as app_module

    db_url = f"sqlite:///{tmp_path / 'api-handoffs.db'}"
    monkeypatch.setenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", db_url)
    app_module.SOURCE_STORE.reset()
    app_module.SECTION_STORE.reset()
    app_module.HANDOFF_STORE.reset()
    app_module._source_registry_repository = None
    app_module._section_lifecycle_repository = None
    app_module._ordinance_handoff_repository = None

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        assert (
            await client.post(
                "/api/v1/civiccode/sources",
                headers=STAFF_HEADERS,
                json=active_official_source("municode_handoffs"),
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/titles",
                headers=STAFF_HEADERS,
                json={"title_id": "title_6", "title_number": "6", "title_name": "Animals"},
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/chapters",
                headers=STAFF_HEADERS,
                json={
                    "chapter_id": "chapter_6_12",
                    "title_id": "title_6",
                    "chapter_number": "6.12",
                    "chapter_name": "Urban Livestock",
                },
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/sections",
                headers=STAFF_HEADERS,
                json={
                    "section_id": "sec_chickens",
                    "chapter_id": "chapter_6_12",
                    "section_number": "6.12.040",
                    "section_heading": "Backyard chickens",
                },
            )
        ).status_code == 201
        assert (
            await client.post(
                "/api/v1/civiccode/sections/sec_chickens/versions",
                headers=STAFF_HEADERS,
                json={
                    "version_id": "v_chickens_current",
                    "section_id": "sec_chickens",
                    "source_id": "municode_handoffs",
                    "version_label": "Current",
                    "body": "Residents may keep up to six backyard chickens with a city permit.",
                    "effective_start": "2026-01-01",
                    "status": "adopted",
                    "is_current": True,
                },
            )
        ).status_code == 201
        created = await client.post(
            "/api/v1/civiccode/staff/civicclerk/ordinance-events",
            headers=STAFF_HEADERS,
            json={
                "event_id": "ord_2026_041",
                "external_event_id": "cc_event_2026_041",
                "civicclerk_meeting_id": "meeting_2026_04_27",
                "civicclerk_agenda_item_id": "agenda_14",
                "ordinance_number": "2026-041",
                "title": "Ordinance amending backyard chicken permits",
                "status": "adopted",
                "affected_sections": ["6.12.040"],
                "source_document_url": "https://example.gov/minutes/2026-041.pdf",
                "source_document_hash": "sha256:abc123",
                "ordinance_text": "An ordinance amending Section 6.12.040.",
            },
        )

    app_module._ordinance_handoff_repository = None
    persisted = OrdinanceHandoffRepository(db_url=db_url)

    assert created.status_code == 201
    events = persisted.list_events()
    assert [event.event_id for event in events] == ["ord_2026_041"]
    assert persisted.warnings_for_section("6.12.040")[0]["external_event_id"] == "cc_event_2026_041"
    assert persisted.audit_events()[0].event_type == "civicclerk_handoff_received"


@pytest.mark.asyncio
async def test_api_import_jobs_use_configured_database(monkeypatch, tmp_path) -> None:
    import civiccode.main as app_module

    db_url = f"sqlite:///{tmp_path / 'api-import-jobs.db'}"
    monkeypatch.setenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", db_url)
    app_module.SOURCE_STORE.reset()
    app_module.SECTION_STORE.reset()
    app_module.IMPORT_STORE.reset()
    app_module._source_registry_repository = None
    app_module._section_lifecycle_repository = None
    app_module._import_store = None
    payload = mock_city_import_payload(mock_city_codifier_contracts()[0])
    payload["job_id"] = "import_persistent_code_vendor"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        created = await client.post(
            "/api/v1/civiccode/staff/imports/local-bundle",
            headers=STAFF_HEADERS,
            json=payload,
        )

    app_module._import_store = None
    source_store = SourceRegistryRepository(db_url=db_url)
    section_store = app_module.SECTION_STORE
    persisted = ImportConnectorRepository(
        source_store=source_store,
        section_store=section_store,
        db_url=db_url,
    )

    assert created.status_code == 201
    assert created.json()["status"] == "completed"
    jobs = persisted.list_jobs()
    assert [job.job_id for job in jobs] == ["import_persistent_code_vendor"]
    assert jobs[0].counts["sources_created"] == 1
    assert jobs[0].provenance["fixture_checksum"]
    assert jobs[0].completed_at is not None


@pytest.mark.asyncio
async def test_api_imported_tree_uses_configured_database(monkeypatch, tmp_path) -> None:
    import civiccode.main as app_module

    db_url = f"sqlite:///{tmp_path / 'api-import-tree.db'}"
    monkeypatch.setenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", db_url)
    app_module.SOURCE_STORE.reset()
    app_module.SECTION_STORE.reset()
    app_module.IMPORT_STORE.reset()
    app_module._source_registry_repository = None
    app_module._section_lifecycle_repository = None
    app_module._import_store = None
    payload = mock_city_import_payload(mock_city_codifier_contracts()[0])
    payload["job_id"] = "import_tree_code_vendor"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        created = await client.post(
            "/api/v1/civiccode/staff/imports/local-bundle",
            headers=STAFF_HEADERS,
            json=payload,
        )
        tree = await client.get(
            "/api/v1/civiccode/staff/imports/import_tree_code_vendor/tree",
            headers=STAFF_HEADERS,
        )

    assert created.status_code == 201
    assert tree.status_code == 200
    assert tree.json()["source"]["source_id"] == payload["source"]["source_id"]
    assert tree.json()["sections"][0]["section_number"] == "6.12.040"
