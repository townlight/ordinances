from __future__ import annotations

import importlib
import socket

import pytest
from conftest import build_suite_staff_headers
from httpx import ASGITransport, AsyncClient

from civiccode.mock_city_environment import mock_city_codifier_contracts, mock_city_import_payload
from civiccode.operational_state import OperationalStateRepository


STAFF_HEADERS = build_suite_staff_headers()
LEGACY_STAFF_HEADERS = {
    "X-CivicCode-Role": "staff",
    "X-CivicCode-Actor": "operator@example.gov",
}


@pytest.fixture()
def app_module(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", raising=False)
    monkeypatch.delenv("CIVICCODE_DEMO_SEED", raising=False)
    module = importlib.import_module("civiccode.main")
    module.SOURCE_STORE.reset()
    module.SECTION_STORE.reset()
    module.STAFF_NOTE_STORE.reset()
    module.SUMMARY_STORE.reset()
    module.HANDOFF_STORE.reset()
    module.IMPORT_STORE.reset()
    module.CODIFIER_SYNC_STORE.reset()
    module._source_registry_repository = None
    module._section_lifecycle_repository = None
    module._import_store = None
    module._codifier_sync_store = None
    module._demo_seed_key = None
    return module


@pytest.fixture()
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_staff_operational_state_empty_state_is_actionable(client: AsyncClient) -> None:
    response = await client.get("/api/v1/civiccode/staff/operational-state", headers=STAFF_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "missing_state"
    assert payload["counts"] == {
        "records": 0,
        "retry_queue": 0,
        "replay_record": 0,
        "delta_cursor": 0,
        "lanes_with_state": 0,
    }
    assert payload["data_source"]["external_deployment_required"] is False
    assert payload["data_source"]["network_required"] is False
    assert payload["fixes"] == [
        "Run at least one local import, codifier sync, or CivicClerk handoff operation so staff can inspect operational readiness."
    ]
    assert payload["lanes"]["import"]["fixes"][0].startswith("Run a local import bundle")
    assert payload["lanes"]["sync"]["fixes"][0].startswith("Configure a codifier sync source")
    assert payload["lanes"]["handoff"]["fixes"][0].startswith("Create a CivicClerk handoff event")


@pytest.mark.asyncio
async def test_staff_operational_state_returns_populated_mock_city_state(
    client: AsyncClient,
    app_module,
) -> None:
    payload = mock_city_import_payload(mock_city_codifier_contracts()[0])
    app_module.SOURCE_STORE.create(payload["source"])

    configured = await client.post(
        "/api/v1/civiccode/staff/sync/codifier-sources",
        headers=STAFF_HEADERS,
        json={"source_id": payload["source"]["source_id"], "sync_schedule": "*/15 * * * *"},
    )
    assert configured.status_code == 201

    run = await client.post(
        f"/api/v1/civiccode/staff/sync/codifier-sources/{payload['source']['source_id']}/run",
        headers=STAFF_HEADERS,
        json={"payload": payload, "changed_since": "2026-05-01T12:00:00Z"},
    )
    assert run.status_code == 201

    handoff = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json={
            "event_id": "ord_operational_ready",
            "external_event_id": "cc_event_operational_ready",
            "civicclerk_meeting_id": "meeting_2026_05_06",
            "civicclerk_agenda_item_id": "agenda_8",
            "ordinance_number": "2026-108",
            "title": "Operational readiness handoff proof",
            "status": "adopted",
            "affected_sections": ["6.12.040"],
            "source_document_url": "https://brookfield.example.gov/ordinances/2026-108.pdf",
            "source_document_hash": "sha256:operational-ready",
            "ordinance_text": "An ordinance proving operational readiness state.",
        },
    )
    assert handoff.status_code == 201

    response = await client.get("/api/v1/civiccode/staff/operational-state", headers=STAFF_HEADERS)

    assert response.status_code == 200
    readiness = response.json()
    assert readiness["status"] == "ready"
    assert readiness["counts"]["lanes_with_state"] == 3
    assert readiness["counts"]["replay_record"] >= 3
    assert readiness["counts"]["delta_cursor"] == 1
    assert readiness["fixes"] == []
    assert readiness["lanes"]["handoff"]["status"] == "ready"
    assert readiness["lanes"]["import"]["status"] == "ready"
    assert readiness["lanes"]["sync"]["status"] == "ready"
    assert any(record["lane"] == "sync" for record in readiness["records"])
    assert any(record["subject_id"] == payload["source"]["source_id"] for record in readiness["records"])


@pytest.mark.asyncio
async def test_staff_operational_state_does_not_require_external_deployment(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("operational-state endpoint attempted outbound network")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    response = await client.get("/api/v1/civiccode/staff/operational-state", headers=STAFF_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_source"]["external_deployment_required"] is False
    assert payload["data_source"]["network_required"] is False


@pytest.mark.asyncio
async def test_staff_operational_state_requires_staff_headers(client: AsyncClient) -> None:
    response = await client.get("/api/v1/civiccode/staff/operational-state")

    assert response.status_code == 403
    assert response.json()["detail"]["fix"].startswith("Send X-CivicCode-Role: staff")


@pytest.mark.asyncio
async def test_staff_headers_must_come_from_trusted_proxy(app_module) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app, client=("203.0.113.22", 12345)),
        base_url="http://testserver",
    ) as remote_client:
        response = await remote_client.get(
            "/api/v1/civiccode/staff/operational-state",
            headers=LEGACY_STAFF_HEADERS,
        )

    assert response.status_code == 403
    assert response.json()["detail"]["message"] == (
        "Trusted staff headers were not received from an approved proxy."
    )
    assert "CIVICCODE_STAFF_TRUSTED_PROXY_CIDRS" in response.json()["detail"]["fix"]


@pytest.mark.asyncio
async def test_staff_headers_honor_configured_trusted_header_names(
    app_module,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVICCODE_STAFF_PRINCIPAL_HEADER", "X-Staff-Email")
    monkeypatch.setenv("CIVICCODE_STAFF_ROLES_HEADER", "X-Staff-Roles")

    response = await client_response_for_custom_headers(app_module)

    assert response.status_code == 200
    assert response.json()["status"] == "missing_state"


async def client_response_for_custom_headers(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as custom_client:
        return await custom_client.get(
            "/api/v1/civiccode/staff/operational-state",
            headers={
                "X-Staff-Email": "operator@example.gov",
                "X-Staff-Roles": "staff",
            },
        )


def test_operational_state_repository_reloads_sqlite_datetimes_as_utc(tmp_path) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'operational-state.db'}"
    store = OperationalStateRepository(db_url=db_url)
    store.record_replay(
        lane="handoff",
        subject_id="ord_2026_108",
        actor="operator@example.gov",
        status="pending_codification",
        payload_hash="sha256:operational-ready",
    )

    reloaded = OperationalStateRepository(db_url=db_url)
    records = reloaded.list_records()

    assert len(records) == 1
    assert records[0].created_at.tzinfo is not None
    assert records[0].created_at.isoformat().endswith("+00:00")
