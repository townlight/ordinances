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
    module.IMPORT_STORE.reset()
    return module


@pytest.fixture()
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


async def seed_export_fixture(client: AsyncClient) -> None:
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
                "checksum": "sha256:example",
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
async def test_records_ready_export_includes_source_version_citation_and_retrieval_metadata(
    client: AsyncClient,
) -> None:
    await seed_export_fixture(client)

    response = await client.get("/api/v1/civiccode/sections/6.12.040/export")

    assert response.status_code == 200
    payload = response.json()
    assert payload["export_version"] == "civiccode.records_ready.v1"
    assert payload["document_type"] == "municipal_code_section"
    assert payload["section"]["section_number"] == "6.12.040"
    assert payload["version"]["version_id"] == "v_chickens_current"
    assert payload["citation"]["section_id"] == "sec_chickens"
    assert payload["source_provenance"]["source_id"] == "municode_active"
    assert payload["source_provenance"]["retrieval_method"] == "official_web_export"
    assert payload["source_provenance"]["checksum"] == "sha256:example"
    assert payload["legal_boundary"]["classification"] == "information_not_determination"
    assert payload["accessibility"]["civicaccess_runtime_dependency"] == "not_shipped"


@pytest.mark.asyncio
async def test_accessible_html_export_has_semantic_headings_labels_and_focus(
    client: AsyncClient,
) -> None:
    await seed_export_fixture(client)

    response = await client.get("/civiccode/sections/6.12.040/export")

    assert response.status_code == 200
    html = response.text
    assert '<main id="content"' in html
    assert "Skip to export content" in html
    assert '<h1>6.12.040 - Backyard chickens</h1>' in html
    assert '<h2 id="code-text-heading">Authoritative code text</h2>' in html
    assert '<h2 id="citation-heading">Citation</h2>' in html
    assert '<h2 id="source-heading">Source provenance</h2>' in html
    assert '<h2 id="boundary-heading">Legal boundary</h2>' in html
    assert 'aria-label="Section metadata"' in html
    assert 'aria-label="Source provenance"' in html
    assert ":focus-visible" in html
    assert "overflow-wrap: anywhere" in html
    assert "@media print" in html
    assert "not legal advice" in html


@pytest.mark.asyncio
async def test_public_section_detail_links_to_accessible_export(client: AsyncClient) -> None:
    await seed_export_fixture(client)

    response = await client.get("/civiccode/sections/6.12.040")

    assert response.status_code == 200
    html = response.text
    assert "Records-ready export" in html
    assert "/civiccode/sections/6.12.040/export" in html
    assert "citation and source provenance" in html


@pytest.mark.asyncio
async def test_export_refuses_stale_source_with_actionable_page(client: AsyncClient) -> None:
    await seed_export_fixture(client)
    stale = await client.post(
        "/api/v1/civiccode/sources/municode_active/transitions",
        headers=STAFF_HEADERS,
        json={
            "to_status": "stale",
            "actor": "clerk@example.gov",
            "reason": "publisher posted a newer supplement",
        },
    )
    assert stale.status_code == 200

    api = await client.get("/api/v1/civiccode/sections/6.12.040/export")
    html = await client.get("/civiccode/sections/6.12.040/export")

    assert api.status_code == 409
    assert "stale" in api.json()["detail"]["message"]
    assert "Refresh or reactivate" in api.json()["detail"]["fix"]
    assert html.status_code == 200
    assert "Export problem" in html.text
    assert "Refresh or reactivate" in html.text


def test_docs_record_accessibility_export_without_claiming_civicaccess_runtime() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lower()
    manual = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8").lower()
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8").lower()

    for document_text in [changelog, manual, landing]:
        assert "records-ready export" in document_text
        assert "civicaccess" in document_text
        assert "civicaccess runtime is shipped" not in document_text
        assert "civicaccess dependency is required" not in document_text
