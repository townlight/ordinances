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
    return module


@pytest.fixture()
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


async def seed_citation_fixture(client: AsyncClient) -> None:
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
async def test_citation_includes_required_ids_source_and_effective_date(
    client: AsyncClient,
) -> None:
    await seed_citation_fixture(client)

    response = await client.get(
        "/api/v1/civiccode/citations/build",
        params={"section_number": "6.12.040"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["classification"] == "information_not_determination"
    assert payload["code_answer_behavior"] == "not_available"
    citation = payload["citation"]
    assert citation["section_id"] == "sec_chickens"
    assert citation["version_id"] == "v_chickens_current"
    assert citation["source_id"] == "municode_active"
    assert citation["effective_start"] == "2026-01-01"
    assert citation["canonical_url"] == "/civiccode/sections/sec_chickens"
    assert "Title 6" in citation["citation_text"]
    assert "Chapter 6.12" in citation["citation_text"]
    assert "Section 6.12.040" in citation["citation_text"]


@pytest.mark.asyncio
async def test_citation_refuses_missing_section_with_fix_path(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/civiccode/citations/build",
        params={"section_number": "99.99.999"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "refused"
    assert payload["refusal_type"] == "section_lookup"
    assert "not found" in payload["reason"]
    assert "Create the section first" in payload["fix"]


@pytest.mark.asyncio
async def test_citation_refuses_stale_source(client: AsyncClient) -> None:
    await seed_citation_fixture(client)
    stale = await client.post(
        "/api/v1/civiccode/sources/municode_active/transitions",
        headers=STAFF_HEADERS,
        json={
            "to_status": "stale",
            "actor": "clerk@example.gov",
            "reason": "Publisher updated the code.",
        },
    )
    assert stale.status_code == 200

    response = await client.get(
        "/api/v1/civiccode/citations/build",
        params={"section_number": "6.12.040"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "refused"
    assert payload["refusal_type"] == "stale_source"
    assert "not active" in payload["reason"]
    assert "Refresh or reactivate" in payload["fix"]


@pytest.mark.asyncio
async def test_citation_refuses_overlapping_effective_dates(client: AsyncClient) -> None:
    await seed_citation_fixture(client)
    overlap = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json={
            "version_id": "v_overlap",
            "section_id": "sec_chickens",
            "source_id": "municode_active",
            "version_label": "Overlap",
            "body": "Overlapping adopted text.",
            "effective_start": "2026-01-01",
            "effective_end": "2026-12-31",
            "status": "adopted",
            "is_current": False,
        },
    )
    assert overlap.status_code == 201

    response = await client.get(
        "/api/v1/civiccode/citations/build",
        params={"section_number": "6.12.040", "as_of": "2026-06-01"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "refused"
    assert payload["refusal_type"] == "section_lookup"
    assert "overlapping adopted versions" in payload["reason"]
    assert "Fix the effective date ranges" in payload["fix"]


@pytest.mark.asyncio
async def test_citation_endpoint_never_returns_uncited_prose(client: AsyncClient) -> None:
    await seed_citation_fixture(client)

    response = await client.get(
        "/api/v1/civiccode/citations/build",
        params={"section_number": "6.12.040"},
    )

    payload = response.json()
    assert "answer" not in payload
    assert "summary" not in payload
    assert payload["citation"]["citation_text"]
    assert payload["code_answer_behavior"] == "not_available"


def test_docs_and_changelog_record_citation_contract_without_claiming_qa() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lower()
    manual = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8").lower()
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8").lower()

    for document_text in [changelog, manual, landing]:
        assert "citation contract" in document_text
        assert "q&a is available" not in document_text
        assert "code answers are available" not in document_text
