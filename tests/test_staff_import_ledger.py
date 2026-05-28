from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
from conftest import build_suite_staff_headers
from httpx import ASGITransport, AsyncClient


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "milestone_12"

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


def fixture_payload(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_staff_import_ledger_requires_staff_access(client: AsyncClient) -> None:
    response = await client.get("/staff/imports")

    assert response.status_code == 403
    assert "Staff import ledger requires staff access" in response.text
    assert "X-CivicCode-Role: staff" in response.text
    assert "Fix: sign in through the staff shell" in response.text
    assert '<a class="skip-link" href="#content">Skip to staff import ledger</a>' in response.text
    assert '<main id="content">' in response.text


@pytest.mark.asyncio
async def test_staff_import_ledger_empty_state_is_actionable(client: AsyncClient) -> None:
    response = await client.get("/staff/imports", headers=STAFF_HEADERS)

    assert response.status_code == 200
    html = response.text
    assert "Import provenance ledger" in html
    assert "No local import jobs have run yet" in html
    assert "post a vetted local bundle" in html
    assert "/api/v1/civiccode/staff/imports/local-bundle" in html
    assert "csv_bundle, official_html_extract" in html
    assert '<a class="skip-link" href="#content">Skip to staff import ledger</a>' in html
    assert '<main id="content">' in html
    assert ".skip-link:focus" in html


@pytest.mark.asyncio
async def test_staff_import_ledger_shows_jobs_provenance_and_failure_fix(
    client: AsyncClient,
) -> None:
    completed = await client.post(
        "/api/v1/civiccode/staff/imports/local-bundle",
        headers=STAFF_HEADERS,
        json=fixture_payload("csv_bundle.json"),
    )
    failed = await client.post(
        "/api/v1/civiccode/staff/imports/local-bundle",
        headers=STAFF_HEADERS,
        json=fixture_payload("broken_missing_section.json"),
    )
    assert completed.status_code == 201
    assert failed.status_code == 201

    response = await client.get("/staff/imports", headers=STAFF_HEADERS)

    assert response.status_code == 200
    html = response.text
    assert "import_csv_animals" in html
    assert "import_broken_missing_section" in html
    assert "Example City Code CSV Export" in html
    assert "Broken Local Export" in html
    assert "official_file_drop" in html
    assert "fixture_checksum" not in html
    assert "Checksum" in html
    assert "sources created" in html
    assert "sections created" in html
    assert "Import failure" in html
    assert "Version &#x27;version_orphan&#x27; references missing section" in html
    assert "Fix: Include the section in the same bundle or import it before this version" in html
    assert "/api/v1/civiccode/staff/imports/import_csv_animals/provenance" in html
    assert '<a class="skip-link" href="#content">Skip to staff import ledger</a>' in html
    assert '<main id="content">' in html
