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
    return module


@pytest.fixture()
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


async def create_section_tree(client: AsyncClient, section_id: str = "sec_chickens") -> None:
    source = await client.post(
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
    assert source.status_code == 201, source.text

    title = await client.post(
        "/api/v1/civiccode/titles",
        headers=STAFF_HEADERS,
        json={
            "title_id": "title_6",
            "title_number": "6",
            "title_name": "Animals",
        },
    )
    assert title.status_code == 201, title.text

    chapter = await client.post(
        "/api/v1/civiccode/chapters",
        headers=STAFF_HEADERS,
        json={
            "chapter_id": "chapter_6_12",
            "title_id": "title_6",
            "chapter_number": "6.12",
            "chapter_name": "Urban Livestock",
        },
    )
    assert chapter.status_code == 201, chapter.text

    section = await client.post(
        "/api/v1/civiccode/sections",
        headers=STAFF_HEADERS,
        json={
            "section_id": section_id,
            "chapter_id": "chapter_6_12",
            "section_number": "6.12.040",
            "section_heading": "Backyard chickens",
            "administrative_regulation_refs": ["admin-reg-animals-1"],
            "resolution_refs": ["resolution-2025-04"],
            "policy_refs": ["policy-animal-control-faq"],
            "approved_summary_refs": ["approved-summary-chickens"],
        },
    )
    assert section.status_code == 201, section.text


@pytest.mark.asyncio
async def test_section_lifecycle_writes_require_staff_headers(client: AsyncClient) -> None:
    title = await client.post(
        "/api/v1/civiccode/titles",
        json={"title_id": "title_6", "title_number": "6", "title_name": "Animals"},
    )
    chapter = await client.post(
        "/api/v1/civiccode/chapters",
        json={
            "chapter_id": "chapter_6_12",
            "title_id": "title_6",
            "chapter_number": "6.12",
            "chapter_name": "Urban Livestock",
        },
    )
    section = await client.post(
        "/api/v1/civiccode/sections",
        json={
            "section_id": "sec_chickens",
            "chapter_id": "chapter_6_12",
            "section_number": "6.12.040",
            "section_heading": "Backyard chickens",
        },
    )
    version = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        json=adopted_version(version_id="v_current"),
    )

    for response in (title, chapter, section, version):
        assert response.status_code == 403
        assert response.json()["detail"]["fix"].startswith("Send X-CivicCode-Role: staff")


def adopted_version(
    *,
    version_id: str,
    section_id: str = "sec_chickens",
    body: str = "Up to six hens are allowed with a permit.",
    effective_start: str = "2026-01-01",
    effective_end: str | None = None,
    is_current: bool = True,
    prior_version_id: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "version_id": version_id,
        "section_id": section_id,
        "source_id": "municode_active",
        "version_label": version_id,
        "body": body,
        "effective_start": effective_start,
        "status": "adopted",
        "is_current": is_current,
        "adoption_event_id": "ord-2026-01",
        "amendment_event_id": "ord-2026-01",
        "amendment_summary": "Adopted chicken permit limit.",
    }
    if effective_end:
        payload["effective_end"] = effective_end
    if prior_version_id:
        payload["prior_version_id"] = prior_version_id
    return payload


@pytest.mark.asyncio
async def test_create_section_tree_with_related_non_code_materials(client: AsyncClient) -> None:
    await create_section_tree(client)

    history = await client.get("/api/v1/civiccode/sections/sec_chickens/history")

    assert history.status_code == 200
    section = history.json()["section"]
    assert section["section_number"] == "6.12.040"
    assert section["administrative_regulation_refs"] == ["admin-reg-animals-1"]
    assert section["resolution_refs"] == ["resolution-2025-04"]
    assert section["policy_refs"] == ["policy-animal-control-faq"]
    assert section["approved_summary_refs"] == ["approved-summary-chickens"]


@pytest.mark.asyncio
async def test_lookup_current_section_by_number(client: AsyncClient) -> None:
    await create_section_tree(client)
    version = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json=adopted_version(version_id="v_current"),
    )
    assert version.status_code == 201, version.text

    lookup = await client.get(
        "/api/v1/civiccode/sections/lookup",
        params={"section_number": "6.12.040"},
    )

    assert lookup.status_code == 200
    payload = lookup.json()
    assert payload["section"]["section_heading"] == "Backyard chickens"
    assert payload["version"]["version_id"] == "v_current"
    assert payload["legal_effect"] == "adopted_law"
    assert payload["code_answer_behavior"] == "not_available"


@pytest.mark.asyncio
async def test_lookup_historical_section_by_effective_date(client: AsyncClient) -> None:
    await create_section_tree(client)
    old_version = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json=adopted_version(
            version_id="v_2024",
            body="Up to four hens are allowed with a permit.",
            effective_start="2024-01-01",
            effective_end="2025-12-31",
            is_current=False,
        ),
    )
    assert old_version.status_code == 201, old_version.text
    current_version = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json=adopted_version(
            version_id="v_2026",
            effective_start="2026-01-01",
            prior_version_id="v_2024",
        ),
    )
    assert current_version.status_code == 201, current_version.text

    historical = await client.get(
        "/api/v1/civiccode/sections/lookup",
        params={"section_number": "6.12.040", "as_of": "2025-06-01"},
    )

    assert historical.status_code == 200
    assert historical.json()["version"]["version_id"] == "v_2024"
    assert "four hens" in historical.json()["version"]["body"]


@pytest.mark.asyncio
async def test_overlapping_effective_dates_fail_actionably(client: AsyncClient) -> None:
    await create_section_tree(client)
    first = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json=adopted_version(
            version_id="v_overlap_a",
            effective_start="2025-01-01",
            effective_end="2025-12-31",
            is_current=False,
        ),
    )
    assert first.status_code == 201, first.text
    second = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json=adopted_version(
            version_id="v_overlap_b",
            body="Overlapping adopted text.",
            effective_start="2025-06-01",
            effective_end="2026-01-31",
            is_current=False,
        ),
    )
    assert second.status_code == 201, second.text

    lookup = await client.get(
        "/api/v1/civiccode/sections/lookup",
        params={"section_number": "6.12.040", "as_of": "2025-07-01"},
    )

    assert lookup.status_code == 409
    detail = lookup.json()["detail"]
    assert "overlapping adopted versions" in detail["message"]
    assert "Fix the effective date ranges" in detail["fix"]


@pytest.mark.asyncio
async def test_pending_ordinance_language_is_not_treated_as_adopted_law(
    client: AsyncClient,
) -> None:
    await create_section_tree(client)
    source = await client.post(
        "/api/v1/civiccode/sources",
        headers=STAFF_HEADERS,
        json={
            "source_id": "clerk_ord_2026_20",
            "name": "Pending Ordinance 2026-20",
            "publisher": "City Clerk",
            "source_type": "official_file_drop",
            "source_category": "adopted_ordinances",
            "file_reference": "ordinances/pending-2026-20.docx",
            "retrieval_method": "official_file_drop",
            "source_owner": "City Clerk",
            "is_official": True,
            "status": "draft",
        },
    )
    assert source.status_code == 201, source.text
    pending = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json={
            "version_id": "pending_ord",
            "section_id": "sec_chickens",
            "source_id": "clerk_ord_2026_20",
            "version_label": "Pending Ordinance 2026-20",
            "body": "Pending language would allow eight hens.",
            "effective_start": "2026-05-01",
            "status": "pending",
            "is_current": False,
            "adoption_event_id": "pending-ord-2026-20",
        },
    )
    assert pending.status_code == 201, pending.text

    lookup = await client.get(
        "/api/v1/civiccode/sections/lookup",
        params={"section_number": "6.12.040", "as_of": "2026-05-10"},
    )

    assert lookup.status_code == 409
    detail = lookup.json()["detail"]
    assert "only has pending language" in detail["message"]
    assert "adoption/codification" in detail["fix"]


@pytest.mark.asyncio
async def test_amendment_history_preserves_prior_and_current_text(client: AsyncClient) -> None:
    await create_section_tree(client)
    prior = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json=adopted_version(
            version_id="prior_text",
            body="Up to four hens are allowed.",
            effective_start="2024-01-01",
            effective_end="2025-12-31",
            is_current=False,
        ),
    )
    assert prior.status_code == 201, prior.text
    current = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json=adopted_version(
            version_id="current_text",
            body="Up to six hens are allowed with a permit.",
            effective_start="2026-01-01",
            prior_version_id="prior_text",
        ),
    )
    assert current.status_code == 201, current.text

    history = await client.get("/api/v1/civiccode/sections/sec_chickens/history")

    assert history.status_code == 200
    versions = history.json()["versions"]
    assert [version["version_id"] for version in versions] == ["prior_text", "current_text"]
    assert versions[0]["body"] == "Up to four hens are allowed."
    assert versions[1]["body"] == "Up to six hens are allowed with a permit."
    assert versions[1]["prior_version_id"] == "prior_text"


@pytest.mark.asyncio
async def test_current_lookup_without_deterministic_current_version_fails(client: AsyncClient) -> None:
    await create_section_tree(client)
    draft = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json={
            "version_id": "draft_only",
            "section_id": "sec_chickens",
            "source_id": "municode_active",
            "version_label": "Draft import",
            "body": "Draft text.",
            "effective_start": "2026-01-01",
            "status": "draft",
            "is_current": False,
        },
    )
    assert draft.status_code == 201, draft.text

    lookup = await client.get(
        "/api/v1/civiccode/sections/lookup",
        params={"section_number": "6.12.040"},
    )

    assert lookup.status_code == 409
    detail = lookup.json()["detail"]
    assert "does not have one deterministic current version" in detail["message"]
    assert "Provide as_of" in detail["fix"]


@pytest.mark.asyncio
async def test_current_flag_rejects_non_adopted_version(client: AsyncClient) -> None:
    await create_section_tree(client)
    response = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json={
            "version_id": "bad_current",
            "section_id": "sec_chickens",
            "source_id": "municode_active",
            "version_label": "Pending current",
            "body": "Pending text.",
            "effective_start": "2026-01-01",
            "status": "pending",
            "is_current": True,
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "Only adopted section versions can be current law" in detail["message"]
    assert "status to adopted" in detail["fix"]


@pytest.mark.asyncio
async def test_section_version_requires_registered_source(client: AsyncClient) -> None:
    await create_section_tree(client)
    response = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json={
            "version_id": "missing_source_version",
            "section_id": "sec_chickens",
            "source_id": "not_registered",
            "version_label": "No source",
            "body": "Text without source.",
            "effective_start": "2026-01-01",
            "status": "adopted",
            "is_current": True,
        },
    )

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "not_registered" in detail["message"]
    assert "Register the source" in detail["fix"]


@pytest.mark.asyncio
async def test_adopted_version_requires_active_public_source(client: AsyncClient) -> None:
    await create_section_tree(client)
    source = await client.post(
        "/api/v1/civiccode/sources",
        headers=STAFF_HEADERS,
        json={
            "source_id": "draft_source",
            "name": "Draft source",
            "publisher": "City Clerk",
            "source_type": "official_docx_export",
            "source_category": "municipal_code",
            "file_reference": "draft/source.docx",
            "retrieval_method": "official_file_drop",
            "source_owner": "City Clerk",
            "is_official": True,
            "status": "draft",
        },
    )
    assert source.status_code == 201, source.text

    response = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json={
            "version_id": "draft_backed_adopted",
            "section_id": "sec_chickens",
            "source_id": "draft_source",
            "version_label": "Draft-backed adopted text",
            "body": "Text from draft source.",
            "effective_start": "2026-01-01",
            "status": "adopted",
            "is_current": True,
        },
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "active public-visible source" in detail["message"]
    assert "Activate an official source" in detail["fix"]


def test_docs_and_changelog_record_section_version_without_claiming_search_or_answers() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lower()
    manual = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8").lower()
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8").lower()

    for document_text in [changelog, manual, landing]:
        assert "section/version" in document_text or "section and version" in document_text
        assert "code answers are available" not in document_text
        assert "search is available" not in document_text
