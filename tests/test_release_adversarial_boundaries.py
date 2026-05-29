from __future__ import annotations

import importlib

import pytest
from httpx import ASGITransport, AsyncClient


LEGACY_STAFF_HEADERS = {
    "X-CivicCode-Role": "staff",
    "X-CivicCode-Actor": "release-gate@example.gov",
}


@pytest.fixture()
def app_module(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", raising=False)
    monkeypatch.delenv("CIVICCODE_DEMO_SEED", raising=False)
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


@pytest.fixture()
async def client(app_module):
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client


async def seed_section(client: AsyncClient, suite_staff_headers) -> None:
    staff_headers = suite_staff_headers(
        subject="release-gate@example.gov",
        session_id="release-gate-seed",
    )
    assert (
        await client.post(
            "/api/v1/civiccode/sources",
            headers=staff_headers,
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
            headers=staff_headers,
            json={"title_id": "title_6", "title_number": "6", "title_name": "Animals"},
        )
    ).status_code == 201
    assert (
        await client.post(
            "/api/v1/civiccode/chapters",
            headers=staff_headers,
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
            headers=staff_headers,
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
            headers=staff_headers,
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
async def test_bad_question_body_fails_closed_with_validation_error(client: AsyncClient) -> None:
    response = await client.post("/api/v1/civiccode/questions/answer", json={"question": ""})

    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_missing_section_returns_actionable_refusal_not_fabricated_answer(
    client: AsyncClient,
    suite_staff_headers,
) -> None:
    await seed_section(client, suite_staff_headers)

    response = await client.post(
        "/api/v1/civiccode/questions/answer",
        json={
            "question": "What does section 99.99.999 say?",
            "section_number": "99.99.999",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "refused"
    assert payload["citation"] is None
    assert payload["code_answer_behavior"] == "not_available"
    assert "fix" in payload


@pytest.mark.asyncio
async def test_stale_source_refuses_answer_until_staff_refreshes_source(
    client: AsyncClient,
    suite_staff_headers,
) -> None:
    await seed_section(client, suite_staff_headers)
    staff_headers = suite_staff_headers(
        subject="release-gate@example.gov",
        session_id="release-gate-transition",
    )
    assert (
        await client.post(
            "/api/v1/civiccode/sources/municode_active/transitions",
            headers=staff_headers,
            json={
                "to_status": "stale",
                "actor": "release-gate@example.gov",
                "reason": "Publisher updated the source.",
            },
        )
    ).status_code == 200

    response = await client.post(
        "/api/v1/civiccode/questions/answer",
        json={
            "question": "What does section 6.12.040 say?",
            "section_number": "6.12.040",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "refused"
    assert payload["refusal_type"] == "stale_source"
    assert payload["fix"] == "Refresh or reactivate the source before using it for citations."


@pytest.mark.asyncio
async def test_public_cannot_reach_staff_api_or_staff_browser_surfaces(
    client: AsyncClient,
) -> None:
    staff_paths = [
        "/staff/code",
        "/staff/sources",
        "/staff/imports",
        "/staff/sync",
        "/api/v1/civiccode/staff/operational-state",
        "/api/v1/civiccode/staff/sources",
        "/api/v1/civiccode/staff/audit-events",
        "/api/v1/civiccode/staff/imports",
    ]

    for path in staff_paths:
        response = await client.get(path)
        assert response.status_code == 403, path
        if path.startswith("/api/"):
            assert "fix" in response.json()["detail"]
        else:
            assert "Fix:" in response.text


@pytest.mark.asyncio
async def test_spoofed_staff_headers_from_untrusted_remote_are_rejected(app_module) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app, client=("203.0.113.45", 45678)),
        base_url="http://testserver",
    ) as remote_client:
        response = await remote_client.get(
            "/api/v1/civiccode/staff/audit-events",
            headers=LEGACY_STAFF_HEADERS,
        )

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert "approved proxy" in detail["message"]
    assert "CIVICCODE_STAFF_TRUSTED_PROXY_CIDRS" in detail["fix"]


@pytest.mark.asyncio
async def test_shipped_compose_trust_rejects_docker_bridge_staff_header_spoof(
    app_module,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVICCODE_STAFF_TRUSTED_PROXY_CIDRS", "127.0.0.1/32,::1/128")
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app, client=("172.18.0.1", 45678)),
        base_url="http://testserver",
    ) as remote_client:
        response = await remote_client.get(
            "/api/v1/civiccode/staff/audit-events",
            headers=LEGACY_STAFF_HEADERS,
        )

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert "approved proxy" in detail["message"]
    assert "CIVICCODE_STAFF_TRUSTED_PROXY_CIDRS" in detail["fix"]


@pytest.mark.asyncio
async def test_unavailable_ollama_returns_cited_deterministic_fallback_with_fix_path(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    suite_staff_headers,
) -> None:
    await seed_section(client, suite_staff_headers)
    monkeypatch.setenv("CIVICCODE_AI_MODE", "ollama")
    monkeypatch.setenv("CIVICCODE_OLLAMA_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("CIVICCODE_OLLAMA_TIMEOUT_SECONDS", "0.25")

    response = await client.post(
        "/api/v1/civiccode/questions/answer",
        json={
            "question": "What does section 6.12.040 say about backyard chickens?",
            "section_number": "6.12.040",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["llm_provider"] == "not_configured"
    assert payload["ai_authority"] == "deterministic_citation_extract"
    assert payload["citations"][0]["section_number"] == "6.12.040"
    assert payload["llm_error"]["fix"].startswith("Start the local Ollama runtime")
