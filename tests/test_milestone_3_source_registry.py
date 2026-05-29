from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from conftest import build_suite_staff_headers
from httpx import ASGITransport, AsyncClient

from civiccode.source_registry import SOURCE_STATES, SOURCE_TRANSITIONS, validate_transition


ROOT = Path(__file__).resolve().parents[1]
LEGACY_STAFF_HEADERS = {
    "X-CivicCode-Role": "staff",
    "X-CivicCode-Actor": "clerk@example.gov",
}

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


def active_official_source(source_id: str = "municode_active") -> dict[str, object]:
    return {
        "source_id": source_id,
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
        "staff_notes": "Internal source review note.",
    }


def test_source_transition_matrix_is_explicit_and_forward_only() -> None:
    for from_status in SOURCE_STATES:
        for to_status in SOURCE_STATES:
            should_allow = to_status in SOURCE_TRANSITIONS[from_status]
            if should_allow:
                validate_transition(from_status, to_status)
            else:
                with pytest.raises(ValueError):
                    validate_transition(from_status, to_status)


@pytest.mark.asyncio
async def test_catalog_lists_required_codifiers_categories_and_states(client: AsyncClient) -> None:
    response = await client.get("/api/v1/civiccode/sources/catalog")

    assert response.status_code == 200
    payload = response.json()
    assert {
        "municode",
        "american_legal",
        "code_publishing",
        "general_code",
        "official_xml_export",
        "official_docx_export",
        "official_file_drop",
        "official_web_scrape",
        "official_web_export",
    } <= set(payload["source_types"])
    assert {
        "municipal_code",
        "administrative_regulations",
        "resolutions",
        "policies",
        "adopted_ordinances",
        "historical_versions",
        "approved_summaries",
        "internal_staff_notes",
    } <= set(payload["source_categories"])
    assert set(payload["source_states"]) == SOURCE_STATES


@pytest.mark.asyncio
async def test_create_active_official_source_and_read_public_sanitized_copy(
    client: AsyncClient,
    suite_staff_headers,
) -> None:
    unauthenticated = await client.post(
        "/api/v1/civiccode/sources",
        json=active_official_source("blocked_without_session"),
    )
    assert unauthenticated.status_code == 401
    assert "suite session" in unauthenticated.json()["detail"]["message"].lower()
    assert "Authorization: Bearer" in unauthenticated.json()["detail"]["fix"]

    forged_legacy = await client.post(
        "/api/v1/civiccode/sources",
        headers=LEGACY_STAFF_HEADERS,
        json=active_official_source("blocked_legacy_headers"),
    )
    assert forged_legacy.status_code == 401
    assert "suite session" in forged_legacy.json()["detail"]["message"].lower()
    assert "legacy X-CivicCode-Role/X-CivicCode-Actor headers alone cannot create sources" in (
        forged_legacy.json()["detail"]["fix"]
    )

    staff_headers = suite_staff_headers(subject="clerk@example.gov", session_id="source-create")

    response = await client.post(
        "/api/v1/civiccode/sources",
        headers=staff_headers,
        json=active_official_source(),
    )

    assert response.status_code == 201
    staff_payload = response.json()
    assert staff_payload["status"] == "active"
    assert staff_payload["search_eligible"] is True
    assert staff_payload["staff_notes"] == "Internal source review note."

    public_response = await client.get("/api/v1/civiccode/sources/municode_active")
    assert public_response.status_code == 200
    public_payload = public_response.json()
    assert public_payload["status"] == "active"
    assert public_payload["search_eligible"] is True
    assert "staff_notes" not in public_payload


@pytest.mark.asyncio
async def test_active_official_source_requires_complete_provenance(
    client: AsyncClient,
    suite_staff_headers,
) -> None:
    payload = active_official_source()
    payload.pop("source_owner")
    staff_headers = suite_staff_headers(subject="clerk@example.gov", session_id="source-provenance")

    response = await client.post("/api/v1/civiccode/sources", headers=staff_headers, json=payload)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "official-source metadata" in detail["message"]
    assert "source_owner" in detail["fix"]


@pytest.mark.asyncio
async def test_active_non_official_source_requires_explicit_label(
    client: AsyncClient,
    suite_staff_headers,
) -> None:
    payload = active_official_source()
    payload["source_id"] = "non_official"
    payload["is_official"] = False
    payload["source_owner"] = None
    staff_headers = suite_staff_headers(subject="clerk@example.gov", session_id="source-non-official")

    response = await client.post("/api/v1/civiccode/sources", headers=staff_headers, json=payload)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "non-official" in detail["message"]
    assert "official_status_note" in detail["fix"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value", "expected_fix"),
    [
        ("source_url", "ftp://example.gov/code", "https://library.municode.com/example"),
        ("file_reference", "../outside-drop.docx", "municipal file-drop"),
    ],
)
async def test_invalid_url_or_file_reference_returns_actionable_422(
    client: AsyncClient,
    field: str,
    value: str,
    expected_fix: str,
    suite_staff_headers,
) -> None:
    payload = {
        "source_id": f"bad_{field}",
        "name": "Bad source",
        "publisher": "Official file drop",
        "source_type": "official_file_drop",
        "source_category": "adopted_ordinances",
        "retrieved_at": "2026-04-27T12:00:00Z",
        "retrieval_method": "official_file_drop",
        "source_owner": "City Clerk",
        "status": "draft",
        field: value,
    }

    staff_headers = suite_staff_headers(
        subject="clerk@example.gov",
        session_id=f"source-invalid-{field}",
    )
    response = await client.post("/api/v1/civiccode/sources", headers=staff_headers, json=payload)

    assert response.status_code == 422
    assert expected_fix in response.json()["detail"]["fix"]


@pytest.mark.asyncio
async def test_missing_source_returns_actionable_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/civiccode/sources/not_found")

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "not_found" in detail["message"]
    assert "Create the source first" in detail["fix"]


@pytest.mark.asyncio
async def test_staff_only_sources_do_not_appear_on_public_endpoints(
    client: AsyncClient,
    suite_staff_headers,
) -> None:
    payload = active_official_source("staff_notes_source")
    payload["source_category"] = "internal_staff_notes"
    payload["source_type"] = "official_docx_export"
    payload["file_reference"] = "staff/source-review.docx"
    payload["source_url"] = None
    staff_headers = suite_staff_headers(subject="clerk@example.gov", session_id="source-staff-notes")

    create_response = await client.post("/api/v1/civiccode/sources", headers=staff_headers, json=payload)
    assert create_response.status_code == 201
    assert create_response.json()["public_visible"] is False
    assert create_response.json()["search_eligible"] is False

    public_list = await client.get("/api/v1/civiccode/sources")
    assert public_list.status_code == 200
    assert public_list.json()["sources"] == []

    public_get = await client.get("/api/v1/civiccode/sources/staff_notes_source")
    assert public_get.status_code == 404
    assert "staff source endpoint" in public_get.json()["detail"]["fix"]

    unauthenticated_staff_list = await client.get("/api/v1/civiccode/staff/sources")
    assert unauthenticated_staff_list.status_code == 403
    assert "Staff role required" in unauthenticated_staff_list.json()["detail"]["message"]

    unauthenticated_staff_get = await client.get("/api/v1/civiccode/staff/sources/staff_notes_source")
    assert unauthenticated_staff_get.status_code == 403
    assert "Staff role required" in unauthenticated_staff_get.json()["detail"]["message"]

    staff_get = await client.get(
        "/api/v1/civiccode/staff/sources/staff_notes_source",
        headers=staff_headers,
    )
    assert staff_get.status_code == 200
    assert staff_get.json()["staff_notes"] == "Internal source review note."


@pytest.mark.asyncio
async def test_stale_and_failed_sources_return_actionable_messages(
    client: AsyncClient,
    suite_staff_headers,
) -> None:
    payload = active_official_source("needs_refresh")
    staff_headers = suite_staff_headers(subject="clerk@example.gov", session_id="source-state")
    create_response = await client.post("/api/v1/civiccode/sources", headers=staff_headers, json=payload)
    assert create_response.status_code == 201

    blocked_transition = await client.post(
        "/api/v1/civiccode/sources/needs_refresh/transitions",
        json={
            "to_status": "stale",
            "actor": "clerk@example.gov",
            "reason": "Publisher posted a newer code snapshot.",
        },
    )
    assert blocked_transition.status_code == 403
    assert "Staff role required" in blocked_transition.json()["detail"]["message"]

    stale_response = await client.post(
        "/api/v1/civiccode/sources/needs_refresh/transitions",
        headers=staff_headers,
        json={
            "to_status": "stale",
            "actor": "clerk@example.gov",
            "reason": "Publisher posted a newer code snapshot.",
        },
    )
    assert stale_response.status_code == 200
    assert "Refresh the source" in stale_response.json()["fix"]

    failed_response = await client.post(
        "/api/v1/civiccode/sources/needs_refresh/transitions",
        headers=staff_headers,
        json={
            "to_status": "failed",
            "actor": "clerk@example.gov",
            "reason": "Checksum validation failed.",
        },
    )
    assert failed_response.status_code == 200
    assert "Review the failure note" in failed_response.json()["fix"]


@pytest.mark.asyncio
async def test_invalid_source_transition_returns_409_with_fix_path(
    client: AsyncClient,
    suite_staff_headers,
) -> None:
    payload = active_official_source("terminal_source")
    staff_headers = suite_staff_headers(subject="clerk@example.gov", session_id="source-transition")
    create_response = await client.post("/api/v1/civiccode/sources", headers=staff_headers, json=payload)
    assert create_response.status_code == 201

    superseded_response = await client.post(
        "/api/v1/civiccode/sources/terminal_source/transitions",
        headers=staff_headers,
        json={
            "to_status": "superseded",
            "actor": "clerk@example.gov",
            "reason": "Replaced by a newer source.",
        },
    )
    assert superseded_response.status_code == 200

    invalid_response = await client.post(
        "/api/v1/civiccode/sources/terminal_source/transitions",
        headers=staff_headers,
        json={
            "to_status": "active",
            "actor": "clerk@example.gov",
            "reason": "Trying to reactivate terminal source.",
        },
    )
    assert invalid_response.status_code == 409
    assert "Allowed target states from superseded: none" in invalid_response.json()["detail"]["fix"]


def test_docs_and_changelog_record_source_registry_without_claiming_answers() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lower()
    manual = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8").lower()
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8").lower()

    for document_text in [changelog, manual, landing]:
        assert "source registry" in document_text
        assert "code answers are available" not in document_text
        assert "public lookup ui is available" not in document_text
