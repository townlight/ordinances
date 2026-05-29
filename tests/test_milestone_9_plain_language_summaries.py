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
    return module


@pytest.fixture()
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


async def seed_summary_fixture(client: AsyncClient) -> None:
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
async def test_staff_can_create_draft_and_approve_plain_language_summary(
    client: AsyncClient,
) -> None:
    await seed_summary_fixture(client)

    create = await client.post(
        "/api/v1/civiccode/staff/sections/sec_chickens/summaries",
        headers=STAFF_HEADERS,
        json={
            "summary_id": "summary_chickens",
            "section_version_id": "v_chickens_current",
            "summary_text": "In plain language: residents may keep up to six chickens if they get a city permit.",
        },
    )
    assert create.status_code == 201
    draft = create.json()
    assert draft["status"] == "draft"
    assert draft["public_visible"] is False
    assert draft["authority"] == "non_authoritative_explanation"
    assert draft["section_version_id"] == "v_chickens_current"

    approve = await client.post(
        "/api/v1/civiccode/staff/summaries/summary_chickens/approve",
        headers=STAFF_HEADERS,
    )
    assert approve.status_code == 200
    approved = approve.json()
    assert approved["status"] == "approved"
    assert approved["public_visible"] is True
    assert approved["approved_by"] == "clerk@example.gov"


@pytest.mark.asyncio
async def test_public_only_sees_approved_summary_with_authoritative_text(
    client: AsyncClient,
) -> None:
    await seed_summary_fixture(client)
    await client.post(
        "/api/v1/civiccode/staff/sections/sec_chickens/summaries",
        headers=STAFF_HEADERS,
        json={
            "summary_id": "summary_chickens",
            "section_version_id": "v_chickens_current",
            "summary_text": "In plain language: residents may keep up to six chickens if they get a city permit.",
        },
    )

    hidden = await client.get("/api/v1/civiccode/sections/sec_chickens/summaries")
    assert hidden.status_code == 200
    assert hidden.json()["summaries"] == []

    await client.post(
        "/api/v1/civiccode/staff/summaries/summary_chickens/approve",
        headers=STAFF_HEADERS,
    )
    public = await client.get("/api/v1/civiccode/sections/sec_chickens/summaries")
    payload = public.json()
    assert public.status_code == 200
    assert payload["code_answer_behavior"] == "not_available"
    assert payload["summaries"][0]["authority"] == "non_authoritative_explanation"
    assert payload["summaries"][0]["warning"] == "Plain-language summaries are not law."
    assert payload["summaries"][0]["authoritative_section"]["section_number"] == "6.12.040"
    assert "Residents may keep up to six backyard chickens" in payload["summaries"][0][
        "authoritative_text"
    ]


@pytest.mark.asyncio
async def test_summary_requires_adopted_source_citation_before_approval(
    client: AsyncClient,
) -> None:
    await seed_summary_fixture(client)

    missing_version = await client.post(
        "/api/v1/civiccode/staff/sections/sec_chickens/summaries",
        headers=STAFF_HEADERS,
        json={
            "summary_id": "summary_missing",
            "section_version_id": "missing_version",
            "summary_text": "This cannot be approved because it has no source citation.",
        },
    )
    assert missing_version.status_code == 404
    assert "section version" in missing_version.json()["detail"]["message"].lower()

    pending_version = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json={
            "version_id": "v_chickens_pending",
            "section_id": "sec_chickens",
            "source_id": "municode_active",
            "version_label": "Pending",
            "body": "Pending language about backyard chickens.",
            "effective_start": "2026-06-01",
            "status": "pending",
            "is_current": False,
        },
    )
    assert pending_version.status_code == 201
    create_pending_summary = await client.post(
        "/api/v1/civiccode/staff/sections/sec_chickens/summaries",
        headers=STAFF_HEADERS,
        json={
            "summary_id": "summary_pending",
            "section_version_id": "v_chickens_pending",
            "summary_text": "This pending text should not publish as a public explanation.",
        },
    )
    assert create_pending_summary.status_code == 422
    detail = create_pending_summary.json()["detail"]
    assert "adopted section version" in detail["message"].lower()
    assert "adopted law" in detail["fix"].lower()


@pytest.mark.asyncio
async def test_summary_endpoints_require_staff_role(client: AsyncClient) -> None:
    await seed_summary_fixture(client)

    response = await client.post(
        "/api/v1/civiccode/staff/sections/sec_chickens/summaries",
        json={
            "section_version_id": "v_chickens_current",
            "summary_text": "Unauthenticated users cannot draft summaries.",
        },
    )

    assert response.status_code == 403
    assert "Staff role required" in response.json()["detail"]["message"]


@pytest.mark.asyncio
async def test_summary_approval_appends_audit_event(client: AsyncClient) -> None:
    await seed_summary_fixture(client)
    await client.post(
        "/api/v1/civiccode/staff/sections/sec_chickens/summaries",
        headers=STAFF_HEADERS,
        json={
            "summary_id": "summary_chickens",
            "section_version_id": "v_chickens_current",
            "summary_text": "In plain language: residents may keep chickens with a permit.",
        },
    )

    await client.post(
        "/api/v1/civiccode/staff/summaries/summary_chickens/approve",
        headers=STAFF_HEADERS,
    )
    audit = await client.get("/api/v1/civiccode/staff/audit-events", headers=STAFF_HEADERS)

    event_types = [event["event_type"] for event in audit.json()["events"]]
    assert "plain_language_summary_created" in event_types
    assert "plain_language_summary_approved" in event_types


def test_docs_record_plain_language_without_claiming_legal_advice() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lower()
    manual = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8").lower()
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8").lower()

    for document_text in [changelog, manual, landing]:
        assert "plain-language summaries" in document_text
        assert "non-authoritative" in document_text
        assert "legal advice is available" not in document_text
        assert "plain-language summaries are law" not in document_text
