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


async def seed_handoff_fixture(client: AsyncClient) -> None:
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


def handoff_payload(**overrides):
    payload = {
        "external_event_id": "cc_event_2026_041",
        "civicclerk_meeting_id": "meeting_2026_04_27",
        "civicclerk_agenda_item_id": "agenda_14",
        "ordinance_number": "2026-041",
        "title": "Ordinance amending backyard chicken permits",
        "status": "adopted",
        "affected_sections": ["6.12.040"],
        "source_document_url": "https://example.gov/minutes/2026-041.pdf",
        "source_document_hash": "sha256:abc123",
        "ordinance_text": "An ordinance amending Section 6.12.040 to change backyard chicken permit rules.",
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_valid_civicclerk_handoff_is_accepted_with_provenance(
    client: AsyncClient,
) -> None:
    await seed_handoff_fixture(client)

    response = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["external_event_id"] == "cc_event_2026_041"
    assert payload["handoff_state"] == "pending_codification"
    assert payload["provenance"]["civicclerk_meeting_id"] == "meeting_2026_04_27"
    assert payload["provenance"]["civicclerk_agenda_item_id"] == "agenda_14"
    assert payload["source_document_hash"] == "sha256:abc123"
    assert payload["likely_conflicts"][0]["section_number"] == "6.12.040"


@pytest.mark.asyncio
async def test_configured_civicclerk_handoff_requires_matching_intake_auth(
    client: AsyncClient,
    app_module,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await seed_handoff_fixture(client)
    monkeypatch.setenv(app_module.CIVICCODE_INTAKE_AUTH_ENV_VAR, "shared-test-value")

    missing = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(),
    )
    accepted = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers={**STAFF_HEADERS, app_module.CIVICCODE_INTAKE_AUTH_HEADER: "shared-test-value"},
        json=handoff_payload(event_id="auth_event", external_event_id="auth_external"),
    )

    assert missing.status_code == 403
    assert "authorization failed" in missing.json()["detail"]["message"]
    assert accepted.status_code == 201
    assert accepted.json()["external_event_id"] == "auth_external"


@pytest.mark.asyncio
async def test_matching_intake_auth_allows_service_to_service_without_trusted_proxy_headers(
    client: AsyncClient,
    app_module,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await seed_handoff_fixture(client)
    monkeypatch.setenv(app_module.CIVICCODE_INTAKE_AUTH_ENV_VAR, "shared-test-value")

    accepted = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers={app_module.CIVICCODE_INTAKE_AUTH_HEADER: "shared-test-value"},
        json=handoff_payload(event_id="service_event", external_event_id="service_external"),
    )

    assert accepted.status_code == 201
    assert accepted.json()["external_event_id"] == "service_external"


@pytest.mark.asyncio
async def test_matching_suite_bearer_allows_civicclerk_handoff(
    client: AsyncClient,
    app_module,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await seed_handoff_fixture(client)
    monkeypatch.setenv(app_module.CIVICCODE_INTAKE_AUTH_ENV_VAR, "shared-test-value")

    accepted = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers={"Authorization": "Bearer shared-test-value"},
        json=handoff_payload(event_id="bearer_event", external_event_id="bearer_external"),
    )

    assert accepted.status_code == 201
    assert accepted.json()["external_event_id"] == "bearer_external"


@pytest.mark.asyncio
async def test_replayed_civicclerk_handoff_returns_existing_event(
    client: AsyncClient,
) -> None:
    await seed_handoff_fixture(client)

    first = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(),
    )
    replay = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers={**STAFF_HEADERS, "X-CivicCode-Actor": "deputy@example.gov"},
        json=handoff_payload(event_id="ord_replayed_client_id"),
    )
    audit_events = await client.get(
        "/api/v1/civiccode/staff/audit-events",
        headers=STAFF_HEADERS,
    )

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json()["event_id"] == first.json()["event_id"]
    assert replay.json()["source_document_hash"] == "sha256:abc123"
    handoff_audits = [
        event
        for event in audit_events.json()["events"]
        if event["event_type"] == "civicclerk_handoff_received"
    ]
    assert len(handoff_audits) == 1


@pytest.mark.asyncio
async def test_divergent_civicclerk_handoff_replay_gets_actionable_conflict(
    client: AsyncClient,
) -> None:
    await seed_handoff_fixture(client)
    created = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(),
    )

    replay = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(source_document_hash="sha256:corrected"),
    )

    assert created.status_code == 201
    assert replay.status_code == 409
    detail = replay.json()["detail"]
    assert "already been accepted" in detail["message"]
    assert "Read the existing handoff" in detail["fix"]


@pytest.mark.asyncio
async def test_duplicate_internal_event_id_still_rejected(
    client: AsyncClient,
) -> None:
    await seed_handoff_fixture(client)
    created = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(event_id="ord_2026_041"),
    )

    duplicate = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(
            event_id="ord_2026_041",
            external_event_id="cc_event_2026_042",
            ordinance_number="2026-042",
            source_document_hash="sha256:def456",
        ),
    )

    assert created.status_code == 201
    assert duplicate.status_code == 409
    detail = duplicate.json()["detail"]
    assert "ord_2026_041" in detail["message"]
    assert "unique event_id" in detail["fix"]


@pytest.mark.asyncio
async def test_invalid_handoff_rejected_with_fix_path(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(affected_sections=[]),
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "affected section" in detail["message"].lower()
    assert "affected_sections" in detail["fix"]


@pytest.mark.asyncio
async def test_unknown_affected_section_is_rejected_before_invisible_handoff(
    client: AsyncClient,
) -> None:
    await seed_handoff_fixture(client)

    response = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(affected_sections=["99.99.999"]),
    )

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "99.99.999" in detail["message"]
    assert "Create the section first" in detail["fix"]


@pytest.mark.asyncio
async def test_pending_ordinance_text_never_replaces_adopted_code(
    client: AsyncClient,
) -> None:
    await seed_handoff_fixture(client)
    await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(
            status="pending",
            ordinance_text="Pending text: residents may keep twelve chickens without a permit.",
        ),
    )

    lookup = await client.get(
        "/api/v1/civiccode/sections/lookup",
        params={"section_number": "6.12.040"},
    )
    assert lookup.status_code == 200
    body = lookup.json()["version"]["body"]
    assert "six backyard chickens" in body
    assert "twelve chickens" not in body
    assert lookup.json()["handoff_warnings"][0]["handoff_state"] == "pending_codification"


@pytest.mark.asyncio
async def test_affected_lookup_includes_stale_code_warning(client: AsyncClient) -> None:
    await seed_handoff_fixture(client)
    await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(),
    )

    lookup = await client.get(
        "/api/v1/civiccode/sections/lookup",
        params={"section_number": "6.12.040"},
    )

    warning = lookup.json()["handoff_warnings"][0]
    assert warning["message"].startswith("CivicClerk ordinance 2026-041 may affect")
    assert warning["fix"].startswith("Ask municipal staff")
    assert warning["source"] == "CivicClerk"
    assert "external_event_id" not in warning
    assert "failure_reason" not in warning


@pytest.mark.asyncio
async def test_staff_can_resolve_handoff_after_codified_version_is_current(
    client: AsyncClient,
) -> None:
    await seed_handoff_fixture(client)
    handoff = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(),
    )
    await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json={
            "version_id": "v_codified_2026_041",
            "section_id": "sec_chickens",
            "source_id": "municode_active",
            "version_label": "Codified ordinance 2026-041",
            "body": "Residents may keep up to eight backyard chickens with a city permit.",
            "effective_start": "2026-05-07",
            "status": "adopted",
            "is_current": True,
            "adoption_event_id": handoff.json()["event_id"],
            "prior_version_id": "v_chickens_current",
            "amendment_event_id": handoff.json()["event_id"],
            "amendment_summary": "Codifies ordinance 2026-041 after CivicClerk adoption.",
        },
    )

    resolved = await client.post(
        f"/api/v1/civiccode/staff/civicclerk/ordinance-events/{handoff.json()['event_id']}/resolve",
        headers=STAFF_HEADERS,
        json={"section_version_id": "v_codified_2026_041"},
    )
    lookup = await client.get(
        "/api/v1/civiccode/sections/lookup",
        params={"section_number": "6.12.040"},
    )

    assert resolved.status_code == 200
    assert resolved.json()["handoff_state"] == "codified"
    assert resolved.json()["resolution"]["section_version_id"] == "v_codified_2026_041"
    assert lookup.json()["handoff_warnings"] == []


@pytest.mark.asyncio
async def test_failed_handoff_is_visible_and_does_not_mutate_code_state(
    client: AsyncClient,
) -> None:
    await seed_handoff_fixture(client)
    failed = await client.post(
        "/api/v1/civiccode/staff/civicclerk/ordinance-events",
        headers=STAFF_HEADERS,
        json=handoff_payload(status="failed", failure_reason="Missing signed ordinance PDF."),
    )
    lookup = await client.get(
        "/api/v1/civiccode/sections/lookup",
        params={"section_number": "6.12.040"},
    )

    assert failed.status_code == 201
    assert failed.json()["handoff_state"] == "failed"
    assert failed.json()["failure_reason"] == "Missing signed ordinance PDF."
    assert "six backyard chickens" in lookup.json()["version"]["body"]
    warning = lookup.json()["handoff_warnings"][0]
    assert warning["handoff_state"] == "failed"
    assert "failure_reason" not in warning


def test_docs_record_civicclerk_handoff_without_claiming_codification() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lower()
    manual = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8").lower()
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8").lower()

    for document_text in [changelog, manual, landing]:
        assert "civicclerk handoff" in document_text
        assert "pending codification" in document_text
        assert "automatic ordinance codification is available" not in document_text
        assert "automatic ordinance codification ships" not in document_text
        assert "pending ordinance language is adopted law" not in document_text
