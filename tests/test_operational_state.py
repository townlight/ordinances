from __future__ import annotations

from datetime import date
from pathlib import Path

from townlight_code.codifier_sync import CodifierSyncRepository
from townlight_code.import_connectors import ImportConnectorRepository
from townlight_code.mock_city_environment import mock_city_codifier_contracts, mock_city_import_payload
from townlight_code.operational_state import OperationalStateRepository, OperationalStateStore
from townlight_code.ordinance_handoff import OrdinanceHandoffRepository
from townlight_code.section_lifecycle import SectionLifecycleRepository
from townlight_code.source_registry import SourceRegistryRepository


def test_import_retry_and_replay_operational_state_persists(tmp_path: Path) -> None:
    db_url = f"sqlite:///{tmp_path / 'operational-import.db'}"
    source_store = SourceRegistryRepository(db_url=db_url)
    section_store = SectionLifecycleRepository(db_url=db_url)
    operational_store = OperationalStateRepository(db_url=db_url)
    import_store = ImportConnectorRepository(
        source_store=source_store,
        section_store=section_store,
        operational_store=operational_store,
        db_url=db_url,
    )
    payload = mock_city_import_payload(mock_city_codifier_contracts()[0])
    broken = payload | {"job_id": "job_operational_broken", "connector_type": "unknown_connector"}

    failed = import_store.run_import(broken, actor="clerk@example.gov")
    assert failed.status == "failed"

    reloaded = OperationalStateRepository(db_url=db_url)
    records = reloaded.list_records(lane="import")
    assert {record.record_type for record in records} == {"retry_queue", "replay_record"}
    retry = next(record for record in records if record.record_type == "retry_queue")
    replay = next(record for record in records if record.record_type == "replay_record")
    assert retry.subject_id == "job_operational_broken"
    assert retry.failure["message"].startswith("Unknown connector_type")
    assert replay.payload_hash == failed.provenance["fixture_checksum"]


def test_codifier_sync_delta_cursor_and_replay_operational_state_persist(tmp_path: Path) -> None:
    db_url = f"sqlite:///{tmp_path / 'operational-sync.db'}"
    source_store = SourceRegistryRepository(db_url=db_url)
    section_store = SectionLifecycleRepository(db_url=db_url)
    operational_store = OperationalStateRepository(db_url=db_url)
    import_store = ImportConnectorRepository(
        source_store=source_store,
        section_store=section_store,
        operational_store=operational_store,
        db_url=db_url,
    )
    sync_store = CodifierSyncRepository(
        source_store=source_store,
        import_store=import_store,
        operational_store=operational_store,
        db_url=db_url,
    )
    payload = mock_city_import_payload(mock_city_codifier_contracts()[0])
    _coerce_version_dates(payload)
    source_store.create(payload["source"])
    sync_store.configure_source(source_id=payload["source"]["source_id"], sync_schedule="*/15 * * * *")

    run = sync_store.run_local_payload(
        source_id=payload["source"]["source_id"],
        payload=payload,
        actor="clerk@example.gov",
    )
    assert run.job_payload["status"] == "completed"

    reloaded = OperationalStateRepository(db_url=db_url)
    cursor = reloaded.list_records(lane="sync", record_type="delta_cursor")[0]
    replay = reloaded.list_records(lane="sync", record_type="replay_record")[0]
    assert cursor.subject_id == payload["source"]["source_id"]
    assert cursor.cursor_key == "updatedSince"
    assert cursor.cursor_value.endswith("Z")
    assert replay.details["import_job_id"] == payload["job_id"]


def test_handoff_failed_state_records_retry_and_replay(tmp_path: Path) -> None:
    db_url = f"sqlite:///{tmp_path / 'operational-handoff.db'}"
    operational_store = OperationalStateRepository(db_url=db_url)
    handoff_store = OrdinanceHandoffRepository(operational_store=operational_store, db_url=db_url)

    event = handoff_store.create_event(
        {
            "event_id": "ord_failed_operational",
            "external_event_id": "cc_event_failed_operational",
            "townlight_meetings_meeting_id": "meeting_2026_05_04",
            "townlight_meetings_agenda_item_id": "agenda_9",
            "ordinance_number": "2026-099",
            "title": "Failed codification handoff",
            "status": "failed",
            "affected_sections": ["6.12.040"],
            "source_document_url": "https://example.gov/ordinances/2026-099.pdf",
            "source_document_hash": "sha256:failed",
            "failure_reason": "Missing signed ordinance packet.",
        },
        actor="clerk@example.gov",
    )
    assert event.handoff_state == "failed"

    reloaded = OperationalStateRepository(db_url=db_url)
    records = reloaded.list_records(lane="handoff", subject_id="ord_failed_operational")
    assert {record.record_type for record in records} == {"retry_queue", "replay_record"}
    assert any(record.failure["message"] == "Missing signed ordinance packet." for record in records)


def test_memory_mode_keeps_operational_state_local() -> None:
    store = OperationalStateStore()
    store.record_retry(lane="import", subject_id="job_local", actor="clerk@example.gov", reason="Fixture missing.")

    assert store.list_records()[0].subject_id == "job_local"
    assert OperationalStateStore().list_records() == ()


def _coerce_version_dates(payload: dict[str, object]) -> None:
    for version in payload.get("versions", []):
        if isinstance(version.get("effective_start"), str):
            version["effective_start"] = date.fromisoformat(version["effective_start"])
        if isinstance(version.get("effective_end"), str):
            version["effective_end"] = date.fromisoformat(version["effective_end"])
