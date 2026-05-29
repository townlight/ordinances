from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from conftest import build_suite_staff_headers
from httpx import ASGITransport, AsyncClient


ROOT = Path(__file__).resolve().parents[1]

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


async def seed_public_lookup_fixture(client: AsyncClient) -> None:
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
                "policy_refs": ["policy-chicken-permits"],
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
async def test_public_lookup_home_is_accessible_and_honest(client: AsyncClient) -> None:
    response = await client.get("/civiccode")

    assert response.status_code == 200
    html = response.text
    assert '<main id="content"' in html
    assert 'action="/civiccode/search"' in html
    assert '<label for="q">' in html
    assert "Ready for a search" in html
    assert "No live LLM" in html
    assert "legal advice" in html.lower()
    assert ":focus-visible" in html


@pytest.mark.asyncio
async def test_public_search_success_links_to_section_and_citation(
    client: AsyncClient,
) -> None:
    await seed_public_lookup_fixture(client)

    response = await client.get("/civiccode/search", params={"q": "backyard chickens"})

    assert response.status_code == 200
    html = response.text
    assert "Backyard chickens" in html
    assert "6.12.040" in html
    assert "/civiccode/sections/6.12.040" in html
    assert "Citation-ready" in html
    assert "authoritative code text" in html


@pytest.mark.asyncio
async def test_public_search_related_material_result_links_to_source_section(
    client: AsyncClient,
) -> None:
    await seed_public_lookup_fixture(client)

    response = await client.get("/civiccode/search", params={"q": "policy chicken"})

    assert response.status_code == 200
    html = response.text
    assert "policy-chicken-permits" in html
    assert "/civiccode/sections/6.12.040" in html
    assert "navigation aid, not a legal determination" in html


@pytest.mark.asyncio
async def test_public_question_answer_page_renders_cited_answer(client: AsyncClient) -> None:
    await seed_public_lookup_fixture(client)

    response = await client.get(
        "/civiccode/answer",
        params={
            "q": "What does section 6.12.040 say about backyard chickens?",
            "section_number": "6.12.040",
        },
    )

    assert response.status_code == 200
    html = response.text
    assert "Cited code answer" in html


@pytest.mark.asyncio
async def test_react_frontend_build_is_served_by_fastapi(client: AsyncClient) -> None:
    response = await client.get("/civiccode/app")

    assert response.status_code == 200
    html = response.text
    assert '<div id="root"></div>' in html
    assert "/civiccode/app/assets/" in html


@pytest.mark.asyncio
async def test_public_section_detail_separates_code_summary_and_warning(
    client: AsyncClient,
) -> None:
    await seed_public_lookup_fixture(client)
    summary = await client.post(
        "/api/v1/civiccode/staff/sections/sec_chickens/summaries",
        headers=STAFF_HEADERS,
        json={
            "summary_id": "summary_chickens",
            "section_version_id": "v_chickens_current",
            "summary_text": "Residents can keep chickens if they obtain a city permit.",
            "status": "draft",
        },
    )
    assert summary.status_code == 201
    approve = await client.post(
        "/api/v1/civiccode/staff/summaries/summary_chickens/approve",
        headers=STAFF_HEADERS,
    )
    assert approve.status_code == 200
    handoff = await client.post(
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
    assert handoff.status_code == 201

    response = await client.get("/civiccode/sections/6.12.040")

    assert response.status_code == 200
    html = response.text
    assert "Authoritative code text" in html
    assert "Residents may keep up to six backyard chickens" in html
    assert "Plain-language summary" in html
    assert "not a legal determination" in html
    assert "pending codification" in html
    assert "CivicClerk ordinance 2026-041" in html
    assert "Title 6 (Animals)" in html
    assert "Contact the City Clerk" in html


@pytest.mark.asyncio
async def test_public_search_empty_state_is_actionable(client: AsyncClient) -> None:
    await seed_public_lookup_fixture(client)

    response = await client.get("/civiccode/search", params={"q": "beekeeping"})

    assert response.status_code == 200
    html = response.text
    assert "No matching code sections yet" in html
    assert "Try a section number" in html
    assert "contact the City Clerk" in html


@pytest.mark.asyncio
async def test_public_legal_advice_query_gets_refusal_with_route_to_staff(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/civiccode/search",
        params={"q": "should I sue my neighbor over chickens"},
    )

    assert response.status_code == 200
    html = response.text
    assert "CivicCode cannot provide legal advice" in html
    assert "Ask for the code section or contact the City Attorney" in html
    assert "not_available" in html


@pytest.mark.asyncio
async def test_public_property_specific_determination_query_gets_refusal(
    client: AsyncClient,
) -> None:
    await seed_public_lookup_fixture(client)

    response = await client.get(
        "/civiccode/search",
        params={"q": "Can I keep chickens at 123 Main Street?"},
    )

    assert response.status_code == 200
    html = response.text
    assert "CivicCode cannot provide legal advice" in html
    assert "Search results for" not in html
    assert "not_available" in html


@pytest.mark.asyncio
async def test_public_section_detail_shows_stale_source_warning(
    client: AsyncClient,
) -> None:
    await seed_public_lookup_fixture(client)
    assert (
        await client.post(
            "/api/v1/civiccode/sources/municode_active/transitions",
            headers=STAFF_HEADERS,
            json={
                "to_status": "stale",
                "actor": "clerk@example.gov",
                "reason": "new supplement arrived",
            },
        )
    ).status_code == 200

    response = await client.get("/civiccode/sections/6.12.040")

    assert response.status_code == 200
    html = response.text
    assert "Citation unavailable" in html
    assert "Refresh or reactivate the source" in html
    assert "stale" in html


def test_docs_record_public_lookup_without_claiming_live_llm() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lower()
    manual = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8").lower()
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8").lower()

    for document_text in [changelog, manual, landing]:
        assert "public code lookup surface" in document_text
        assert "read code" in document_text
        assert "live llm calls are enabled" not in document_text
        assert "legal advice is available" not in document_text
