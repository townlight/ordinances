from __future__ import annotations

import importlib

import pytest
from httpx import ASGITransport, AsyncClient


from conftest import build_suite_staff_headers

STAFF_HEADERS = build_suite_staff_headers()


@pytest.fixture()
def app_module():
    module = importlib.import_module("civiccode.main")
    module.SOURCE_STORE.reset()
    module.SECTION_STORE.reset()
    module.STAFF_NOTE_STORE.reset()
    module.SUMMARY_STORE.reset()
    module.HANDOFF_STORE.reset()
    return module


@pytest.fixture()
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


async def seed_code_workspace(client: AsyncClient) -> None:
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
                "retrieved_at": "2026-05-02T12:00:00Z",
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
async def test_staff_code_workspace_requires_staff_access(client: AsyncClient) -> None:
    response = await client.get("/staff/code")

    assert response.status_code == 403
    assert "Staff code workspace requires staff access" in response.text
    assert "X-CivicCode-Role: staff" in response.text
    assert "Fix: sign in through the staff shell" in response.text
    assert '<a class="skip-link" href="#content">Skip to staff code workspace</a>' in response.text
    assert '<main id="content">' in response.text


@pytest.mark.asyncio
async def test_staff_code_workspace_empty_state_is_actionable(client: AsyncClient) -> None:
    response = await client.get("/staff/code", headers=STAFF_HEADERS)

    assert response.status_code == 200
    html = response.text
    assert "No code sections are ready for staff review yet" in html
    assert "register an active official source" in html
    assert "local code bundle" in html
    assert "Code lifecycle command center" in html
    assert '<a class="skip-link" href="#content">Skip to staff code workspace</a>' in html
    assert '<main id="content">' in html
    assert ".skip-link:focus" in html


@pytest.mark.asyncio
async def test_staff_code_workspace_shows_lifecycle_blockers(client: AsyncClient) -> None:
    await seed_code_workspace(client)
    assert (
        await client.post(
            "/api/v1/civiccode/staff/sections/sec_chickens/summaries",
            headers=STAFF_HEADERS,
            json={
                "summary_id": "summary_draft",
                "section_version_id": "v_chickens_current",
                "summary_text": "Residents can keep chickens if they obtain a city permit.",
                "status": "draft",
            },
        )
    ).status_code == 201
    assert (
        await client.post(
            "/api/v1/civiccode/staff/civicclerk/ordinance-events",
            headers=STAFF_HEADERS,
            json={
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
    ).status_code == 201

    response = await client.get("/staff/code", headers=STAFF_HEADERS)

    assert response.status_code == 200
    html = response.text
    assert "Backyard chickens" in html
    assert "Current effective 2026-01-01" in html
    assert "Example Municipal Code" in html
    assert "draft summaries" in html
    assert "Pending CivicClerk handoffs require codification review" in html
    assert "pending codification review" in html.lower()
    assert "2026-041" in html
    assert "Fix: review the CivicClerk handoff" in html
    assert "/civiccode/sections/6.12.040" in html
    assert '<a class="skip-link" href="#content">Skip to staff code workspace</a>' in html
    assert '<main id="content">' in html
