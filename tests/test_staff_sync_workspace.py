from __future__ import annotations

import importlib

import pytest
from httpx import ASGITransport, AsyncClient

from civiccode.mock_city_environment import (
    mock_city_codifier_contracts,
    mock_city_import_payload,
)


from conftest import build_suite_staff_headers

STAFF_HEADERS = build_suite_staff_headers()


@pytest.fixture()
def app_module(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", raising=False)
    module = importlib.import_module("civiccode.main")
    module.SOURCE_STORE.reset()
    module.SECTION_STORE.reset()
    module.IMPORT_STORE.reset()
    module.CODIFIER_SYNC_STORE.reset()
    module._source_registry_repository = None
    module._section_lifecycle_repository = None
    module._import_store = None
    module._codifier_sync_store = None
    return module


@pytest.fixture()
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_staff_sync_workspace_requires_staff_access(client: AsyncClient) -> None:
    response = await client.get("/staff/sync")

    assert response.status_code == 403
    assert "Staff sync health requires staff access" in response.text
    assert "X-CivicCode-Role: staff" in response.text
    assert "Fix: sign in through the staff shell" in response.text
    assert '<a class="skip-link" href="#content">Skip to staff sync health</a>' in response.text
    assert '<main id="content">' in response.text


@pytest.mark.asyncio
async def test_staff_sync_workspace_empty_state_is_actionable(client: AsyncClient) -> None:
    response = await client.get("/staff/sync", headers=STAFF_HEADERS)

    assert response.status_code == 200
    html = response.text
    assert "No codifier sync source is configured yet" in html
    assert "no sync readiness, circuit-breaker, cursor, or local payload run state" in html
    assert "Fix: register an active official Municode" in html
    assert "codifier sync readiness" in html
    assert "Codifier sync health" in html
    assert '<a class="skip-link" href="#content">Skip to staff sync health</a>' in html
    assert '<main id="content">' in html
    assert ".skip-link:focus" in html


@pytest.mark.asyncio
async def test_staff_sync_workspace_shows_health_and_local_payload_state(
    client: AsyncClient,
    app_module,
) -> None:
    payload = mock_city_import_payload(mock_city_codifier_contracts()[0])
    app_module.SOURCE_STORE.create(payload["source"])

    configured = await client.post(
        "/api/v1/civiccode/staff/sync/codifier-sources",
        headers=STAFF_HEADERS,
        json={
            "source_id": payload["source"]["source_id"],
            "sync_schedule": "*/15 * * * *",
        },
    )
    assert configured.status_code == 201

    ready_response = await client.get("/staff/sync", headers=STAFF_HEADERS)

    assert ready_response.status_code == 200
    ready_html = ready_response.text
    assert payload["source"]["name"] in ready_html
    assert "healthy" in ready_html
    assert "No local payload run recorded" in ready_html
    assert "Fix: run the configured codifier source with an already fetched" in ready_html
    assert "Source URL host passed CivicCore SSRF-safe validation" in ready_html

    run = await client.post(
        f"/api/v1/civiccode/staff/sync/codifier-sources/{payload['source']['source_id']}/run",
        headers=STAFF_HEADERS,
        json={
            "payload": payload,
            "changed_since": "2026-05-01T12:00:00Z",
        },
    )
    assert run.status_code == 201

    populated_response = await client.get("/staff/sync", headers=STAFF_HEADERS)

    assert populated_response.status_code == 200
    html = populated_response.text
    assert "with local payload runs" in html
    assert payload["job_id"] in html
    assert "Latest local payload run" in html
    assert "delta request planned" in html
    assert "updatedSince" in html
    assert "No action needed" in html
    assert "automatically codify ordinances" in html
    assert '<a class="skip-link" href="#content">Skip to staff sync health</a>' in html
    assert '<main id="content">' in html
