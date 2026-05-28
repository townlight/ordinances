from __future__ import annotations

from datetime import date
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


async def seed_resolution_fixture(client: AsyncClient) -> None:
    assert (
        await client.post(
            "/api/v1/civiccode/sources",
            headers=STAFF_HEADERS,
            json={
                "source_id": "municode_current",
                "name": "Brookfield Municipal Code",
                "publisher": "Municode",
                "source_type": "municode",
                "source_category": "municipal_code",
                "source_url": "https://library.municode.com/brookfield/codes/code_of_ordinances",
                "retrieved_at": "2026-05-01T12:00:00Z",
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
                "version_id": "version_current",
                "section_id": "sec_chickens",
                "source_id": "municode_current",
                "version_label": "Current",
                "body": "Residents may keep up to six backyard chickens with a city permit.",
                "effective_start": str(date(2026, 1, 1)),
                "status": "adopted",
                "is_current": True,
            },
        )
    ).status_code == 201


@pytest.mark.asyncio
@pytest.mark.parametrize("consumer_module", ["CivicZone", "CivicLegal", "CivicAccess", "CivicComms"])
async def test_section_resolution_contract_serves_downstream_modules(
    client: AsyncClient,
    consumer_module: str,
) -> None:
    await seed_resolution_fixture(client)

    response = await client.post(
        "/api/v1/civiccode/sections/resolve",
        json={
            "consumer_module": consumer_module,
            "section_number": "6.12.040",
            "as_of": "2026-05-07",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["consumer_module"] == consumer_module
    assert payload["resolution_mode"] == "exact_section"
    assert payload["section"]["section_number"] == "6.12.040"
    assert payload["citation"]["section_number"] == "6.12.040"
    assert payload["legal_boundary"]["legal_determination"] == "not_provided"
    assert payload["version_context"]["as_of"] == "2026-05-07"
    assert payload["stable_contract"]["contract_name"] == "civiccode.section_resolution.v1"
    assert payload["code_answer_behavior"] == "section_resolution"


@pytest.mark.asyncio
async def test_section_resolution_refuses_legal_determination_queries(client: AsyncClient) -> None:
    await seed_resolution_fixture(client)

    response = await client.post(
        "/api/v1/civiccode/sections/resolve",
        json={
            "consumer_module": "CivicZone",
            "query": "Can I keep chickens at 123 Main Street?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "refused"
    assert payload["refusal_type"] == "legal_determination"
    assert payload["consumer_module"] == "CivicZone"
