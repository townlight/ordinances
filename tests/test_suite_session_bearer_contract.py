"""Contract tests for CivicCode accepting CivicCore suite bearer sessions."""

from __future__ import annotations

import importlib

import pytest
from httpx import ASGITransport, AsyncClient


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


@pytest.mark.asyncio
async def test_civiccode_staff_endpoint_accepts_civiccore_suite_bearer(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from civiccore.auth.suite_session import issue_suite_session_token

    monkeypatch.setenv("CIVICCORE_SUITE_SESSION_SECRET", "code-suite-session-secret")
    token = issue_suite_session_token(
        subject="code-operator@example.gov",
        roles=frozenset({"code_admin"}),
        session_id="code-suite-session",
    )

    response = await client.get(
        "/api/v1/civiccode/staff/operational-state",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["staff_session"]["subject"] == "code-operator@example.gov"


@pytest.mark.asyncio
async def test_civiccode_source_creation_accepts_civiccore_suite_bearer(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from civiccore.auth.suite_session import issue_suite_session_token

    monkeypatch.setenv("CIVICCORE_SUITE_SESSION_SECRET", "code-suite-session-secret")
    token = issue_suite_session_token(
        subject="code-operator@example.gov",
        roles=frozenset({"code_admin"}),
        session_id="code-source-session",
    )

    response = await client.post(
        "/api/v1/civiccode/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source_id": "suite_bearer_source",
            "name": "Suite Bearer Source",
            "publisher": "Municode",
            "source_type": "municode",
            "source_category": "municipal_code",
            "source_url": "https://example.gov/code",
            "retrieved_at": "2026-05-28T00:00:00Z",
            "retrieval_method": "official_web_export",
            "source_owner": "City Clerk",
            "is_official": True,
            "status": "active",
        },
    )

    assert response.status_code == 201
    assert response.json()["source_id"] == "suite_bearer_source"
