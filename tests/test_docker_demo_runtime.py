from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from conftest import build_suite_staff_headers
from httpx import ASGITransport, AsyncClient


ROOT = Path(__file__).resolve().parents[1]

STAFF_HEADERS = build_suite_staff_headers()


@pytest.fixture()
def app_module(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CIVICCODE_DEMO_SEED", "1")
    monkeypatch.delenv("CIVICCODE_SOURCE_REGISTRY_DB_URL", raising=False)
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


@pytest.mark.asyncio
async def test_demo_seed_populates_public_and_staff_workspaces(client: AsyncClient) -> None:
    health = await client.get("/health")
    assert health.status_code == 200

    search = await client.get("/civiccode/search", params={"q": "13.40.020"})
    assert search.status_code == 200
    assert "Backyard Livestock" in search.text
    assert "Citation-ready" in search.text

    detail = await client.get("/civiccode/sections/13.40.020")
    assert detail.status_code == 200
    assert "Plain-language summary" in detail.text
    assert "pending codification" in detail.text
    assert "not a legal determination" in detail.text

    staff = await client.get("/staff/code", headers=STAFF_HEADERS)
    assert staff.status_code == 200
    assert "Backyard Livestock" in staff.text
    assert "Pending CivicClerk handoffs require codification review" in staff.text


def test_docker_product_artifacts_document_seeded_compose_runtime() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    env_example = (ROOT / "docker.env.example").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    smoke = (ROOT / "scripts" / "docker-demo-smoke.sh").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8")
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

    assert "pgvector/pgvector:pg17" in compose
    assert "CIVICCODE_DEMO_SEED" in compose
    assert "CIVICCODE_STAFF_TRUSTED_PROXY_CIDRS" in compose
    assert "127.0.0.1:${CIVICCODE_PORT:-8000}:8000" in compose
    assert "172.16.0.0/12" not in compose
    assert "172.16.0.0/12" not in env_example
    assert "alembic -c civiccode/migrations/alembic.ini upgrade head" in dockerfile
    assert "POSTGRES_PASSWORD=civiccode-local-only" in env_example
    assert ".tmp-*" in dockerignore
    assert "docs/*.png" in dockerignore
    assert "DOCKER-DEMO-SMOKE: PASSED" in smoke
    assert "rejects forged staff headers" in smoke
    assert "/api/v1/civiccode/staff/audit-events" in smoke
    assert 'staff_status" != "403"' in smoke
    for text in [readme, manual, landing]:
        assert "Docker Compose" in text
        assert "CIVICCODE_DEMO_SEED=1" in text
        assert "Portland Title 13" in text
