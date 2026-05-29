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
    return module


@pytest.fixture()
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


def source_payload(source_id: str, *, status: str = "active") -> dict[str, object]:
    return {
        "source_id": source_id,
        "name": f"{source_id} municipal code",
        "publisher": "Municode",
        "source_type": "municode",
        "source_category": "municipal_code",
        "source_url": f"https://library.municode.com/{source_id}/codes/code_of_ordinances",
        "retrieved_at": "2026-05-02T12:00:00Z",
        "retrieval_method": "official_web_export",
        "source_owner": "City Clerk",
        "is_official": True,
        "status": status,
        "staff_notes": f"Internal note for {source_id}.",
    }


@pytest.mark.asyncio
async def test_staff_source_workspace_requires_staff_access(client: AsyncClient) -> None:
    response = await client.get("/staff/sources")

    assert response.status_code == 403
    assert "Staff source workspace requires staff access" in response.text
    assert "Open this page through the trusted staff shell" in response.text
    assert "X-CivicCode-Role: staff" in response.text
    assert '<a class="skip-link" href="#content">Skip to staff source registry</a>' in response.text
    assert '<main id="content">' in response.text


@pytest.mark.asyncio
async def test_staff_source_workspace_empty_state_is_actionable(client: AsyncClient) -> None:
    response = await client.get("/staff/sources", headers=STAFF_HEADERS)

    assert response.status_code == 200
    html = response.text
    assert "No code sources registered yet" in html
    assert "Register an official Municode, American Legal, Code Publishing, General Code" in html
    assert "Staff-only notes stay off public endpoints" in html
    assert "Source of truth gate" in html
    assert '<a class="skip-link" href="#content">Skip to staff source registry</a>' in html
    assert '<main id="content">' in html
    assert ".skip-link:focus" in html


@pytest.mark.asyncio
async def test_staff_source_workspace_renders_warnings_and_fix_paths(
    client: AsyncClient,
) -> None:
    active = await client.post(
        "/api/v1/civiccode/sources",
        headers=STAFF_HEADERS,
        json=source_payload("active_source"),
    )
    assert active.status_code == 201
    stale = await client.post(
        "/api/v1/civiccode/sources",
        headers=STAFF_HEADERS,
        json=source_payload("stale_source", status="stale"),
    )
    assert stale.status_code == 201
    failed = await client.post(
        "/api/v1/civiccode/sources",
        headers=STAFF_HEADERS,
        json=source_payload("failed_source", status="failed"),
    )
    assert failed.status_code == 201

    response = await client.get("/staff/sources", headers=STAFF_HEADERS)

    assert response.status_code == 200
    html = response.text
    assert "active_source municipal code" in html
    assert "stale_source municipal code" in html
    assert "failed_source municipal code" in html
    assert "Internal note for active_source." in html
    assert "This source is stale and should not be used for new code answers" in html
    assert "Refresh the source from the official publisher" in html
    assert "This source failed ingestion or verification" in html
    assert "Review the failure note" in html
    assert "Public-visible" in html
    assert "Search eligible" in html
    assert '<a class="skip-link" href="#content">Skip to staff source registry</a>' in html
    assert '<main id="content">' in html
