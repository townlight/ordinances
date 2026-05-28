from __future__ import annotations

import importlib
from datetime import UTC, datetime
from pathlib import Path

import pytest
from conftest import build_suite_staff_headers
from httpx import ASGITransport, AsyncClient

from civiccode.codifier_sync import (
    CodifierSyncError,
    CodifierSyncRepository,
    CodifierSyncStore,
    plan_codifier_delta_request,
    sync_source_to_dict,
)
from civiccode.import_connectors import ImportConnectorStore
from civiccode.mock_city_environment import (
    mock_city_codifier_contracts,
    mock_city_import_payload,
)
from civiccode.section_lifecycle import SectionLifecycleStore
from civiccode.source_registry import SourceRegistryStore


ROOT = Path(__file__).resolve().parents[1]

STAFF_HEADERS = build_suite_staff_headers()


def _stores() -> tuple[SourceRegistryStore, SectionLifecycleStore, ImportConnectorStore, CodifierSyncStore]:
    source_store = SourceRegistryStore()
    section_store = SectionLifecycleStore()
    import_store = ImportConnectorStore(source_store=source_store, section_store=section_store)
    sync_store = CodifierSyncStore(source_store=source_store, import_store=import_store)
    return source_store, section_store, import_store, sync_store


def test_codifier_sync_configuration_validates_schedule_host_and_source() -> None:
    source_store, _, _, sync_store = _stores()
    payload = mock_city_import_payload(mock_city_codifier_contracts()[0])
    source_store.create(payload["source"])

    configured = sync_store.configure_source(
        source_id=payload["source"]["source_id"],
        sync_schedule="*/15 * * * *",
    )
    public = sync_source_to_dict(configured)

    assert public["source_id"] == payload["source"]["source_id"]
    assert public["next_sync_at"] is not None
    assert public["source_status"]["health_status"] == "healthy"
    assert public["source_status"]["next_sync_at"] is not None
    assert public["source_status"]["message"] == public["operator_status"]["message"]
    assert public["operator_status"]["health_status"] == "healthy"
    assert "No action needed" in public["operator_status"]["fix"]
    assert public["host_validation"]["status"] == "passed"
    assert public["delta_plan_history"] == []

    with pytest.raises(CodifierSyncError) as schedule_error:
        sync_store.configure_source(
            source_id=payload["source"]["source_id"],
            sync_schedule="*/5 * * * *",
        )
    assert "too frequent" in schedule_error.value.message
    assert "15 minutes" in schedule_error.value.fix

    localhost_payload = mock_city_import_payload(mock_city_codifier_contracts()[1])
    localhost_payload["source"]["source_id"] = "src_localhost_codifier"
    localhost_payload["source"]["source_url"] = "https://127.0.0.1/mock-code"
    source_store.create(localhost_payload["source"])
    with pytest.raises(CodifierSyncError) as host_error:
        sync_store.configure_source(
            source_id="src_localhost_codifier",
            sync_schedule="*/15 * * * *",
        )
    assert "host validation" in host_error.value.message
    assert "allowlist" in host_error.value.fix


def test_codifier_sync_run_imports_local_payload_and_plans_delta() -> None:
    source_store, _, _, sync_store = _stores()
    payload = mock_city_import_payload(mock_city_codifier_contracts()[0])
    source_store.create(payload["source"])
    sync_store.configure_source(
        source_id=payload["source"]["source_id"],
        sync_schedule="*/15 * * * *",
    )

    run = sync_store.run_local_payload(
        source_id=payload["source"]["source_id"],
        payload=payload,
        actor="clerk@example.gov",
        changed_since=datetime(2026, 5, 1, 12, tzinfo=UTC),
        now=datetime(2026, 5, 2, 12, tzinfo=UTC),
    )
    public = run.public_dict()

    assert public["import_job"]["status"] == "completed"
    assert public["delta_plan"]["delta_enabled"] is True
    assert "updatedSince=2026-05-01T12%3A00%3A00Z" in public["delta_plan"]["request_url"]
    assert public["source"]["operator_status"]["health_status"] == "healthy"
    assert "does not automatically codify ordinances" in public["legal_boundary"]


def test_codifier_sync_circuit_breaker_opens_after_repeated_failed_imports() -> None:
    source_store, _, _, sync_store = _stores()
    payload = mock_city_import_payload(mock_city_codifier_contracts()[2])
    source_store.create(payload["source"])
    sync_store.configure_source(
        source_id=payload["source"]["source_id"],
        sync_schedule="*/15 * * * *",
    )
    broken_payload = payload | {
        "job_id": "job_code_publishing_broken",
        "connector_type": "unknown_connector",
    }

    for index in range(5):
        run = sync_store.run_local_payload(
            source_id=payload["source"]["source_id"],
            payload=broken_payload | {"job_id": f"job_code_publishing_broken_{index}"},
            actor="clerk@example.gov",
            now=datetime(2026, 5, 2, 12, index, tzinfo=UTC),
        )
        assert run.public_dict()["import_job"]["status"] == "failed"

    paused_source = sync_store.get_source(payload["source"]["source_id"])
    paused = sync_source_to_dict(paused_source)
    assert paused["operator_status"]["health_status"] == "circuit_open"
    assert paused["source_status"]["health_status"] == "circuit_open"
    assert paused["source_status"]["next_sync_at"] is None
    assert paused["operator_status"]["sync_paused"] is True
    assert "correct the vendor credentials or endpoint" in paused["operator_status"]["fix"]

    with pytest.raises(CodifierSyncError) as paused_error:
        sync_store.run_local_payload(
            source_id=payload["source"]["source_id"],
            payload=payload,
            actor="clerk@example.gov",
        )
    assert paused_error.value.status_code == 409
    assert "paused by the circuit breaker" in paused_error.value.message


def test_codifier_delta_planner_preserves_existing_query_params() -> None:
    plan = plan_codifier_delta_request(
        connector="general_code",
        source_url="https://ecode360.com/mock/BR0000?client=brookfield",
        changed_since=datetime(2026, 5, 1, 12, tzinfo=UTC),
    )

    assert plan.delta_enabled is True
    assert "client=brookfield" in plan.request_url
    assert "lastModified=2026-05-01T12%3A00%3A00Z" in plan.request_url


@pytest.mark.asyncio
async def test_codifier_sync_api_requires_staff_and_runs_local_payload() -> None:
    module = importlib.import_module("civiccode.main")
    module.SOURCE_STORE.reset()
    module.SECTION_STORE.reset()
    module.STAFF_NOTE_STORE.reset()
    module.SUMMARY_STORE.reset()
    module.HANDOFF_STORE.reset()
    module.IMPORT_STORE.reset()
    module.CODIFIER_SYNC_STORE.reset()
    payload = mock_city_import_payload(mock_city_codifier_contracts()[3])
    module.SOURCE_STORE.create(payload["source"])

    async with AsyncClient(
        transport=ASGITransport(app=module.app),
        base_url="http://testserver",
    ) as client:
        forbidden = await client.get("/api/v1/civiccode/staff/sync/codifier-sources")
        assert forbidden.status_code == 403
        assert "Staff role required" in forbidden.json()["detail"]["message"]

        configured = await client.post(
            "/api/v1/civiccode/staff/sync/codifier-sources",
            headers=STAFF_HEADERS,
            json={
                "source_id": payload["source"]["source_id"],
                "sync_schedule": "*/15 * * * *",
            },
        )
        assert configured.status_code == 201
        assert configured.json()["operator_status"]["health_status"] == "healthy"

        run = await client.post(
            f"/api/v1/civiccode/staff/sync/codifier-sources/{payload['source']['source_id']}/run",
            headers=STAFF_HEADERS,
            json={
                "payload": payload,
                "changed_since": "2026-05-01T12:00:00Z",
            },
        )
        assert run.status_code == 201
        assert run.json()["import_job"]["status"] == "completed"
        assert run.json()["source"]["delta_plan_history"][0]["import_job_id"] == payload["job_id"]
        assert run.json()["delta_plan"]["cursor_param"] == "lastModified"

        listed = await client.get(
            "/api/v1/civiccode/staff/sync/codifier-sources",
            headers=STAFF_HEADERS,
        )
        assert listed.status_code == 200
        assert listed.json()["sources"][0]["last_import_job_id"] == payload["job_id"]


@pytest.mark.asyncio
async def test_codifier_sync_api_uses_configured_source_registry_database(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    db_url = f"sqlite:///{tmp_path / 'codifier-sync-sources.db'}"
    monkeypatch.setenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", db_url)
    module = importlib.import_module("civiccode.main")
    module.SOURCE_STORE.reset()
    module.SECTION_STORE.reset()
    module.IMPORT_STORE.reset()
    module.CODIFIER_SYNC_STORE.reset()
    module._source_registry_repository = None
    module._section_lifecycle_repository = None
    module._import_store = None
    module._codifier_sync_store = None
    payload = mock_city_import_payload(mock_city_codifier_contracts()[0])

    async with AsyncClient(
        transport=ASGITransport(app=module.app),
        base_url="http://testserver",
    ) as client:
        created = await client.post(
            "/api/v1/civiccode/sources",
            headers=STAFF_HEADERS,
            json=payload["source"],
        )
        assert created.status_code == 201

        configured = await client.post(
            "/api/v1/civiccode/staff/sync/codifier-sources",
            headers=STAFF_HEADERS,
            json={
                "source_id": payload["source"]["source_id"],
                "sync_schedule": "*/15 * * * *",
            },
        )
        assert configured.status_code == 201
        assert configured.json()["source_id"] == payload["source"]["source_id"]

        run = await client.post(
            f"/api/v1/civiccode/staff/sync/codifier-sources/{payload['source']['source_id']}/run",
            headers=STAFF_HEADERS,
            json={"payload": payload},
        )
        assert run.status_code == 201
        assert run.json()["import_job"]["status"] == "completed"

    module._codifier_sync_store = None
    persisted = CodifierSyncRepository(
        source_store=module._get_source_store(),
        import_store=module._get_import_store(),
        db_url=db_url,
    )
    sources = persisted.list_sources()
    assert [source.source_id for source in sources] == [payload["source"]["source_id"]]
    assert sources[0].last_import_job_id == payload["job_id"]
    assert sources[0].last_attempted_sync_at is not None
    assert sources[0].last_successful_sync_at is not None
    assert sources[0].next_sync_at_recorded is not None
    assert sources[0].host_validation["status"] == "passed"
    assert sources[0].state.last_sync_status == "success"
    assert sources[0].delta_plan_history[0]["import_job_id"] == payload["job_id"]


def test_docs_describe_codifier_sync_foundation_without_overclaiming() -> None:
    documents = [
        (ROOT / "README.md").read_text(encoding="utf-8"),
        (ROOT / "README.txt").read_text(encoding="utf-8"),
        (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8"),
        (ROOT / "USER-MANUAL.txt").read_text(encoding="utf-8"),
        (ROOT / "docs" / "index.html").read_text(encoding="utf-8"),
        (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
    ]
    combined = "\n".join(documents).lower()

    assert "codifier live-sync foundation" in combined
    assert "circuit-breaker health" in combined
    assert "source-list health projection" in combined
    assert "vendor credentials" in combined
    assert "automatically codify ordinances" in combined
    assert "live codifier sync is available" not in combined
    assert "replace the official codifier" in combined
