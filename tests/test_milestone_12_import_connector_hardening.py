from __future__ import annotations

import importlib
import json
from pathlib import Path
import socket

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
async def test_csv_bundle_import_creates_expected_section_tree(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/civiccode/staff/imports/local-bundle",
        headers=STAFF_HEADERS,
        json=fixture_payload("csv_bundle.json"),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["connector_type"] == "csv_bundle"
    assert payload["counts"]["sources_created"] == 1
    assert payload["counts"]["sections_created"] == 1
    assert payload["background"]["worker"] == "not_required_for_milestone_12"

    lookup = await client.get(
        "/api/v1/civiccode/sections/lookup",
        params={"section_number": "6.12.040"},
    )
    assert lookup.status_code == 200
    assert lookup.json()["section"]["section_heading"] == "Backyard chickens"
    assert "six backyard chickens" in lookup.json()["version"]["body"]

    tree = await client.get(
        "/api/v1/civiccode/staff/imports/import_csv_animals/tree",
        headers=STAFF_HEADERS,
    )
    assert tree.status_code == 200
    assert tree.json()["source"]["source_id"] == "csv_active"
    assert tree.json()["titles"][0]["title_name"] == "Animals"


@pytest.mark.asyncio
async def test_official_html_extract_import_creates_expected_section_tree(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/civiccode/staff/imports/local-bundle",
        headers=STAFF_HEADERS,
        json=fixture_payload("official_html_extract.json"),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["connector_type"] == "official_html_extract"
    assert payload["provenance"]["source_url"] == "https://example.gov/code/title-10"

    search = await client.get("/api/v1/civiccode/search", params={"q": "overnight parking"})
    assert search.status_code == 200
    assert search.json()["results"][0]["section_number"] == "10.08.020"


@pytest.mark.asyncio
async def test_reimport_is_idempotent_and_reuses_existing_records(client: AsyncClient) -> None:
    payload = fixture_payload("csv_bundle.json")
    first = await client.post(
        "/api/v1/civiccode/staff/imports/local-bundle",
        headers=STAFF_HEADERS,
        json=payload,
    )
    second_payload = dict(payload)
    second_payload["job_id"] = "import_csv_animals_second_run"
    second = await client.post(
        "/api/v1/civiccode/staff/imports/local-bundle",
        headers=STAFF_HEADERS,
        json=second_payload,
    )

    assert first.status_code == 201
    assert second.status_code == 201
    counts = second.json()["counts"]
    assert counts["sources_reused"] == 1
    assert counts["titles_reused"] == 1
    assert counts["chapters_reused"] == 1
    assert counts["sections_reused"] == 1
    assert counts["versions_reused"] == 1

    lookup = await client.get(
        "/api/v1/civiccode/sections/lookup",
        params={"section_number": "6.12.040"},
    )
    assert lookup.status_code == 200
    assert lookup.json()["version"]["version_id"] == "version_6_12_040_current"


@pytest.mark.asyncio
async def test_failed_import_records_actionable_error_and_can_be_retried(
    client: AsyncClient,
) -> None:
    broken = await client.post(
        "/api/v1/civiccode/staff/imports/local-bundle",
        headers=STAFF_HEADERS,
        json=fixture_payload("broken_missing_section.json"),
    )
    assert broken.status_code == 201
    assert broken.json()["status"] == "failed"
    assert "missing section" in broken.json()["failure"]["message"]
    assert "Include the section" in broken.json()["failure"]["fix"]

    job = await client.get(
        "/api/v1/civiccode/staff/imports/import_broken_missing_section",
        headers=STAFF_HEADERS,
    )
    assert job.status_code == 200
    assert job.json()["failure"]["fix"].startswith("Include the section")

    fixed = await client.post(
        "/api/v1/civiccode/staff/imports/import_broken_missing_section/retry",
        headers=STAFF_HEADERS,
        json=fixture_payload("csv_bundle.json") | {"job_id": "retry_fixed_csv"},
    )
    assert fixed.status_code == 201
    assert fixed.json()["status"] == "completed"
    assert fixed.json()["retry_of"] == "import_broken_missing_section"


@pytest.mark.asyncio
async def test_local_import_requires_staff_headers(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/civiccode/staff/imports/local-bundle",
        json=fixture_payload("csv_bundle.json"),
    )

    assert response.status_code == 403
    assert "Staff role required" in response.json()["detail"]["message"]


@pytest.mark.asyncio
async def test_local_import_does_not_require_outbound_network(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("local fixture import attempted outbound network")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    response = await client.post(
        "/api/v1/civiccode/staff/imports/local-bundle",
        headers=STAFF_HEADERS,
        json=fixture_payload("official_html_extract.json"),
    )

    assert response.status_code == 201
    assert response.json()["status"] == "completed"
    assert response.json()["provenance"]["no_outbound_dependency"] is True


@pytest.mark.asyncio
async def test_provenance_report_exposes_source_checksum_and_failure_visibility(
    client: AsyncClient,
) -> None:
    create = await client.post(
        "/api/v1/civiccode/staff/imports/local-bundle",
        headers=STAFF_HEADERS,
        json=fixture_payload("csv_bundle.json"),
    )
    assert create.status_code == 201

    provenance = await client.get(
        "/api/v1/civiccode/staff/imports/import_csv_animals/provenance",
        headers=STAFF_HEADERS,
    )
    assert provenance.status_code == 200
    payload = provenance.json()
    assert payload["report"]["no_outbound_dependency"] is True
    assert payload["report"]["fixture_checksum"]
    assert payload["source"]["checksum"]
    assert payload["job"]["background"]["failure_visibility"].endswith("{job_id}")


@pytest.mark.asyncio
async def test_imported_tree_is_scoped_to_the_job_source(client: AsyncClient) -> None:
    csv_import = await client.post(
        "/api/v1/civiccode/staff/imports/local-bundle",
        headers=STAFF_HEADERS,
        json=fixture_payload("csv_bundle.json"),
    )
    html_import = await client.post(
        "/api/v1/civiccode/staff/imports/local-bundle",
        headers=STAFF_HEADERS,
        json=fixture_payload("official_html_extract.json"),
    )
    assert csv_import.status_code == 201
    assert html_import.status_code == 201

    tree = await client.get(
        "/api/v1/civiccode/staff/imports/import_csv_animals/tree",
        headers=STAFF_HEADERS,
    )

    assert tree.status_code == 200
    section_ids = {section["section_id"] for section in tree.json()["sections"]}
    version_ids = {version["version_id"] for version in tree.json()["versions"]}
    assert section_ids == {"sec_6_12_040"}
    assert version_ids == {"version_6_12_040_current"}


def test_docs_record_import_foundation_without_claiming_live_sync() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lower()
    manual = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8").lower()
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8").lower()

    for document_text in [changelog, manual, landing]:
        assert "local import" in document_text
        assert "provenance report" in document_text
        assert "live codifier sync is available" not in document_text
        assert "redis/celery worker is required" not in document_text
