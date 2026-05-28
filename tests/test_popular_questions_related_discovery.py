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
    module.POPULAR_QUESTION_STORE.reset()
    return module


@pytest.fixture()
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


async def seed_discovery_fixture(client: AsyncClient) -> None:
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
                "administrative_regulation_refs": ["Animal permit application rule A-6.12"],
                "resolution_refs": ["Resolution 2026-014 fee schedule"],
                "policy_refs": ["Planning counter permit intake policy"],
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
async def test_staff_can_publish_cited_popular_question_navigation_aid(
    client: AsyncClient,
) -> None:
    await seed_discovery_fixture(client)

    response = await client.post(
        "/api/v1/civiccode/staff/popular-questions",
        headers=STAFF_HEADERS,
        json={
            "question_id": "popular_chickens",
            "question_text": "Where do I read the backyard chicken permit rule?",
            "section_number": "6.12.040",
            "answer_excerpt": "Open Section 6.12.040 for adopted chicken-permit code text.",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["section_url"] == "/civiccode/sections/6.12.040"
    assert payload["citation"]["section_number"] == "6.12.040"
    assert payload["classification"] == "navigation_aid_not_legal_determination"
    assert payload["legal_determination"] == "not_provided"

    public = await client.get("/api/v1/civiccode/popular-questions")
    assert public.status_code == 200
    assert public.json()["count"] == 1


@pytest.mark.asyncio
async def test_popular_questions_reject_legal_determinations_with_fix_path(
    client: AsyncClient,
) -> None:
    await seed_discovery_fixture(client)

    response = await client.post(
        "/api/v1/civiccode/staff/popular-questions",
        headers=STAFF_HEADERS,
        json={
            "question_text": "Can I keep chickens at my address?",
            "section_number": "6.12.040",
            "answer_excerpt": "Open the adopted chicken-permit section.",
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "legal determination" in detail["message"]
    assert "Rewrite the question" in detail["fix"]


@pytest.mark.asyncio
async def test_public_popular_questions_filter_draft_staff_and_nonpopular_items(
    client: AsyncClient,
) -> None:
    await seed_discovery_fixture(client)
    base = {
        "section_number": "6.12.040",
        "answer_excerpt": "Open Section 6.12.040 for adopted code text.",
    }
    for question_id, status, audience, is_popular in [
        ("draft_question", "draft", "public", True),
        ("staff_question", "approved", "staff", True),
        ("not_popular_question", "approved", "public", False),
        ("public_question", "approved", "public", True),
    ]:
        response = await client.post(
            "/api/v1/civiccode/staff/popular-questions",
            headers=STAFF_HEADERS,
            json={
                **base,
                "question_id": question_id,
                "question_text": f"Where do I read Section 6.12.040 item {question_id}?",
                "status": status,
                "audience": audience,
                "is_popular": is_popular,
            },
        )
        assert response.status_code == 201

    public = await client.get("/api/v1/civiccode/popular-questions")

    assert public.status_code == 200
    payload = public.json()
    assert payload["count"] == 1
    assert payload["questions"][0]["question_id"] == "public_question"


@pytest.mark.asyncio
async def test_related_materials_use_explicit_public_refs_without_staff_notes(
    client: AsyncClient,
) -> None:
    await seed_discovery_fixture(client)
    note = await client.post(
        "/api/v1/civiccode/staff/sections/sec_chickens/notes",
        headers=STAFF_HEADERS,
        json={
            "note_id": "staff_routing_note",
            "note_text": "Internal staff interpretation route.",
            "status": "approved",
        },
    )
    assert note.status_code == 201

    response = await client.get("/api/v1/civiccode/sections/6.12.040/related")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 3
    labels = {item["label"] for item in payload["items"]}
    assert "Animal permit application rule A-6.12" in labels
    assert "Internal staff interpretation route." not in str(payload)
    assert all(item["legal_determination"] == "not_provided" for item in payload["items"])


@pytest.mark.asyncio
async def test_public_pages_render_popular_questions_and_related_navigation(
    client: AsyncClient,
) -> None:
    await seed_discovery_fixture(client)
    create = await client.post(
        "/api/v1/civiccode/staff/popular-questions",
        headers=STAFF_HEADERS,
        json={
            "question_text": "Where do I read the backyard chicken permit rule?",
            "section_number": "6.12.040",
            "answer_excerpt": "Open Section 6.12.040 for adopted chicken-permit code text.",
        },
    )
    assert create.status_code == 201

    home = await client.get("/civiccode")
    section = await client.get("/civiccode/sections/6.12.040")

    assert home.status_code == 200
    assert "Popular questions" in home.text
    assert "Where do I read the backyard chicken permit rule?" in home.text
    assert "not legal determinations" in home.text
    assert section.status_code == 200
    assert "Related materials" in section.text
    assert "Planning counter permit intake policy" in section.text
    assert "not legal determinations" in section.text


@pytest.mark.asyncio
async def test_empty_discovery_states_are_actionable(client: AsyncClient) -> None:
    await seed_discovery_fixture(client)

    questions = await client.get("/api/v1/civiccode/popular-questions")
    section = await client.get("/civiccode/sections/sec_chickens")

    assert questions.status_code == 200
    assert "ask the City Clerk to approve public questions" in questions.json()["empty_state"]["fix"]
    assert section.status_code == 200
    assert "No approved related materials" not in section.text


def test_docs_record_popular_questions_and_related_sections_without_legal_advice() -> None:
    combined = "\n".join(
        [
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8"),
            (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "index.html").read_text(encoding="utf-8"),
        ]
    ).lower()

    assert "popular questions" in combined
    assert "related materials" in combined
    assert "navigation aid" in combined
    assert "legal advice is available" not in combined
