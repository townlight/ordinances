from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from conftest import build_suite_staff_headers
from httpx import ASGITransport, AsyncClient


ROOT = Path(__file__).resolve().parents[1]

STAFF_HEADERS = build_suite_staff_headers(subject="planner@example.gov")


@pytest.fixture()
def app_module():
    module = importlib.import_module("civiccode.main")
    module.SOURCE_STORE.reset()
    module.SECTION_STORE.reset()
    module.STAFF_NOTE_STORE.reset()
    return module


@pytest.fixture()
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


async def seed_staff_fixture(client: AsyncClient) -> None:
    assert (
        await client.post(
            "/api/v1/civiccode/sources",
            headers=STAFF_HEADERS,
            json={
                "source_id": "municode_active",
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
            },
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
                "source_id": "municode_active",
                "version_label": "Current",
                "body": "Residents may keep up to six backyard chickens with a city permit.",
                "effective_start": "2026-01-01",
                "status": "adopted",
                "is_current": True,
            },
        )
    ).status_code == 201


@pytest.mark.asyncio
async def test_staff_can_create_and_read_interpretation_note(client: AsyncClient) -> None:
    await seed_staff_fixture(client)

    create = await client.post(
        "/api/v1/civiccode/staff/sections/sec_chickens/notes",
        headers=STAFF_HEADERS,
        json={
            "note_text": "Planning staff generally treats coop setbacks as measured from the property line.",
            "status": "approved",
        },
    )
    assert create.status_code == 201
    created = create.json()
    assert created["section_id"] == "sec_chickens"
    assert created["visibility"] == "staff_only"
    assert created["note_text"].startswith("Planning staff")
    assert created["created_by"] == "planner@example.gov"

    read = await client.get(
        "/api/v1/civiccode/staff/sections/sec_chickens/notes",
        headers=STAFF_HEADERS,
    )
    assert read.status_code == 200
    assert read.json()["notes"][0]["note_id"] == created["note_id"]


@pytest.mark.asyncio
async def test_staff_note_endpoints_require_staff_role(client: AsyncClient) -> None:
    await seed_staff_fixture(client)

    response = await client.post(
        "/api/v1/civiccode/staff/sections/sec_chickens/notes",
        json={"note_text": "Internal note", "status": "draft"},
    )

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert "Staff role required" in detail["message"]
    assert "X-CivicCode-Role" in detail["fix"]


@pytest.mark.asyncio
async def test_public_surfaces_never_leak_staff_note_text_or_counts(
    client: AsyncClient,
) -> None:
    await seed_staff_fixture(client)
    private_note_marker = "property-line interpretation marker"
    assert (
        await client.post(
            "/api/v1/civiccode/staff/sections/sec_chickens/notes",
            headers=STAFF_HEADERS,
            json={"note_text": private_note_marker, "status": "approved"},
        )
    ).status_code == 201

    public_lookup = await client.get(
        "/api/v1/civiccode/sections/lookup",
        params={"section_number": "6.12.040"},
    )
    public_search = await client.get(
        "/api/v1/civiccode/search",
        params={"q": "chickens"},
    )
    public_answer = await client.post(
        "/api/v1/civiccode/questions/answer",
        json={"question": "What does section 6.12.040 say?", "section_number": "6.12.040"},
    )

    serialized = "\n".join(
        [str(public_lookup.json()), str(public_search.json()), str(public_answer.json())]
    )
    assert private_note_marker not in serialized
    assert "staff_notes" not in serialized
    assert "note_count" not in serialized


@pytest.mark.asyncio
async def test_staff_qa_can_include_staff_notes_without_changing_public_contract(
    client: AsyncClient,
) -> None:
    await seed_staff_fixture(client)
    assert (
        await client.post(
            "/api/v1/civiccode/staff/sections/sec_chickens/notes",
            headers=STAFF_HEADERS,
            json={
                "note_text": "Prior approved interpretation: chicken coop setbacks are measured from the property line.",
                "status": "approved",
            },
        )
    ).status_code == 201

    staff_answer = await client.post(
        "/api/v1/civiccode/staff/questions/answer",
        headers=STAFF_HEADERS,
        json={
            "question": "What does section 6.12.040 say about backyard chickens?",
            "section_number": "6.12.040",
        },
    )
    public_answer = await client.post(
        "/api/v1/civiccode/questions/answer",
        json={
            "question": "What does section 6.12.040 say about backyard chickens?",
            "section_number": "6.12.040",
        },
    )

    assert staff_answer.status_code == 200
    staff_payload = staff_answer.json()
    assert staff_payload["audience"] == "staff"
    assert staff_payload["staff_context"]["notes"][0]["note_text"].startswith(
        "Prior approved interpretation"
    )
    assert staff_payload["staff_context"]["warning"] == "staff_only_do_not_publish"

    assert "Prior approved interpretation" not in str(public_answer.json())
    assert public_answer.json()["audience"] == "public"


@pytest.mark.asyncio
async def test_staff_note_writes_append_audit_events(client: AsyncClient) -> None:
    await seed_staff_fixture(client)

    create = await client.post(
        "/api/v1/civiccode/staff/sections/sec_chickens/notes",
        headers=STAFF_HEADERS,
        json={"note_text": "Audit me", "status": "draft"},
    )
    assert create.status_code == 201

    audit = await client.get(
        "/api/v1/civiccode/staff/audit-events",
        headers=STAFF_HEADERS,
    )
    assert audit.status_code == 200
    events = audit.json()["events"]
    assert events[-1]["event_type"] == "interpretation_note_created"
    assert events[-1]["actor"] == "planner@example.gov"
    assert events[-1]["section_id"] == "sec_chickens"


def test_docs_record_staff_workbench_without_claiming_public_ui() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lower()
    manual = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8").lower()
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8").lower()

    for document_text in [changelog, manual, landing]:
        assert "staff workbench foundation" in document_text
        assert "public lookup ui is available" not in document_text
        assert "staff notes are public" not in document_text
