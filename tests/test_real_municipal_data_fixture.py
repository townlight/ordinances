from __future__ import annotations

from importlib.resources import files

import pytest
from httpx import ASGITransport, AsyncClient

from civiccode.real_municipal_fixtures import (
    PORTLAND_BACKYARD_LIVESTOCK_SOURCE_URL,
    PORTLAND_SECTIONS,
    portland_backyard_livestock_payload,
)


from conftest import build_suite_staff_headers

STAFF_HEADERS = build_suite_staff_headers()


@pytest.mark.asyncio
async def test_real_portland_code_fixture_imports_searches_and_answers(app_module) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as client:
        imported = await client.post(
            "/api/v1/civiccode/staff/imports/local-bundle",
            headers=STAFF_HEADERS,
            json=portland_backyard_livestock_payload(),
        )
        assert imported.status_code == 201
        job = imported.json()
        assert job["status"] == "completed"
        assert job["connector_type"] == "official_html_extract"
        assert job["counts"]["sources_created"] == 2
        assert job["counts"]["versions_created"] == len(PORTLAND_SECTIONS)
        assert job["provenance"]["fixture_name"] == "fixtures/portland/code"

        for section in PORTLAND_SECTIONS:
            assert files("civiccode").joinpath(section.file_reference).is_file()

        source = await client.get("/api/v1/civiccode/sources/src_portland_code_13_40")
        assert source.status_code == 200
        assert source.json()["source_url"] == PORTLAND_BACKYARD_LIVESTOCK_SOURCE_URL
        assert source.json()["is_official"] is True
        assert source.json()["file_reference"] == "fixtures/portland/code/13.40-keeping-livestock.txt"

        search = await client.get(
            "/api/v1/civiccode/search",
            params={"q": "roosters"},
        )
        assert search.status_code == 200
        search_payload = search.json()
        assert search_payload["count"] >= 1
        assert search_payload["results"][0]["section_number"] == "13.40.020"
        assert search_payload["semantic_search"]["enabled"] is False

        answer = await client.post(
            "/api/v1/civiccode/questions/answer",
            json={
                "question": "What does section 13.40.020 say about domestic fowl?",
                "section_number": "13.40.020",
            },
        )
        assert answer.status_code == 200
        answer_payload = answer.json()
        assert answer_payload["status"] == "ok"
        assert answer_payload["matched_section_number"] == "13.40.020"
        assert answer_payload["citations"][0]["source_url"] == PORTLAND_BACKYARD_LIVESTOCK_SOURCE_URL
        assert "domestic fowl" in answer_payload["answer"]
        assert "This is not a legal determination" in answer_payload["answer"]


@pytest.fixture()
def app_module():
    import importlib

    module = importlib.import_module("civiccode.main")
    module.SOURCE_STORE.reset()
    module.SECTION_STORE.reset()
    module.STAFF_NOTE_STORE.reset()
    module.SUMMARY_STORE.reset()
    module.HANDOFF_STORE.reset()
    module.IMPORT_STORE.reset()
    module.CODIFIER_SYNC_STORE.reset()
    module._demo_seed_key = None
    return module
