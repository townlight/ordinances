"""Contract tests for CivicCode accepting only CivicCore suite staff sessions."""

from __future__ import annotations

import importlib

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture()
def app_module():
    module = importlib.import_module("civiccode.main")
    module.SOURCE_STORE.reset()
    return module


@pytest.fixture()
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_forged_staff_headers_do_not_create_civiccode_sources(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/civiccode/sources",
        headers={
            "X-CivicCode-Role": "staff",
            "X-CivicCode-Actor": "spoof@example.gov",
        },
        json={
            "source_id": "forged_header_source",
            "name": "Forged Header Source",
            "publisher": "Spoof",
            "source_type": "municode",
            "source_category": "municipal_code",
            "source_url": "https://example.gov/code",
            "retrieved_at": "2026-05-28T00:00:00Z",
            "retrieval_method": "official_web_export",
            "source_owner": "City Clerk",
            "is_official": True,
            "status": "active",
        },
    )

    assert response.status_code in {401, 403}
    assert "suite session" in response.text.lower()
