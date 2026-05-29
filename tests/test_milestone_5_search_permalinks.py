from __future__ import annotations

import importlib
import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from datetime import date
from pathlib import Path

import pytest
from conftest import build_suite_staff_headers
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text

from civiccode.semantic_search import embed_texts, embedding_config_from_env
from civiccode.section_lifecycle import SectionLifecycleRepository


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


async def seed_search_fixture(client: AsyncClient) -> None:
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
    section = await client.post(
        "/api/v1/civiccode/sections",
        headers=STAFF_HEADERS,
        json={
            "section_id": "sec_chickens",
            "chapter_id": "chapter_6_12",
            "section_number": "6.12.040",
            "section_heading": "Backyard chickens",
            "administrative_regulation_refs": ["admin-reg-chicken-coops"],
            "resolution_refs": ["resolution-2026-animals"],
            "policy_refs": ["policy-chicken-permits"],
            "approved_summary_refs": ["approved-summary-chicken-permits"],
        },
    )
    assert section.status_code == 201, section.text
    version = await client.post(
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
    assert version.status_code == 201, version.text


@pytest.mark.asyncio
async def test_search_by_exact_section_number_returns_stable_permalink(
    client: AsyncClient,
) -> None:
    await seed_search_fixture(client)

    response = await client.get("/api/v1/civiccode/search", params={"q": "6.12.040"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    result = payload["results"][0]
    assert result["result_type"] == "code_section"
    assert result["section_number"] == "6.12.040"
    assert result["permalink"] == "/civiccode/sections/sec_chickens"
    assert result["code_answer_behavior"] == "not_available"
    assert payload["semantic_search"]["enabled"] is False


@pytest.mark.asyncio
async def test_search_by_resident_phrase_finds_matching_adopted_text(
    client: AsyncClient,
) -> None:
    await seed_search_fixture(client)

    response = await client.get("/api/v1/civiccode/search", params={"q": "backyard chickens"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["results"][0]["version_id"] == "v_chickens_current"
    assert payload["results"][0]["label"] == "6.12.040 - Backyard chickens"


@pytest.mark.asyncio
async def test_semantic_search_is_not_claimed_without_configured_embedding_model(
    client: AsyncClient,
) -> None:
    await seed_search_fixture(client)

    response = await client.get("/api/v1/civiccode/search", params={"q": "permit animals"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["semantic_search"]["enabled"] is False
    assert payload["semantic_search"]["embedding_provider"] is None
    assert all(result.get("match_type") != "semantic" for result in payload["results"])


def _ollama_embedding_available() -> bool:
    body = json.dumps({"model": "nomic-embed-text", "input": ["health check"]}).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/embed",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return False
    embeddings = payload.get("embeddings")
    return isinstance(embeddings, list) and len(embeddings) == 1 and len(embeddings[0]) == 768


@pytest.mark.skipif(
    not _ollama_embedding_available(),
    reason="nomic-embed-text is not available from local Ollama",
)
@pytest.mark.asyncio
async def test_sqlite_runtime_does_not_claim_semantic_search_without_shared_pgvector(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVICCODE_EMBEDDING_MODE", "ollama")
    monkeypatch.setenv("CIVICCODE_OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    monkeypatch.setenv("CIVICCODE_OLLAMA_EMBEDDING_URL", "http://127.0.0.1:11434")
    await seed_search_fixture(client)
    noise_section = await client.post(
        "/api/v1/civiccode/sections",
        headers=STAFF_HEADERS,
        json={
            "section_id": "sec_noise",
            "chapter_id": "chapter_6_12",
            "section_number": "6.12.080",
            "section_heading": "Noise limits",
        },
    )
    assert noise_section.status_code == 201, noise_section.text
    noise_version = await client.post(
        "/api/v1/civiccode/sections/sec_noise/versions",
        headers=STAFF_HEADERS,
        json={
            "version_id": "v_noise_current",
            "section_id": "sec_noise",
            "source_id": "municode_active",
            "version_label": "Current",
            "body": "Amplified music may not exceed the city nighttime decibel limit.",
            "effective_start": "2026-01-01",
            "status": "adopted",
            "is_current": True,
        },
    )
    assert noise_version.status_code == 201, noise_version.text

    response = await client.get("/api/v1/civiccode/search", params={"q": "poultry coops"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["semantic_search"]["enabled"] is False
    assert payload["semantic_search"]["embedding_provider"] == "ollama:nomic-embed-text"
    assert payload["semantic_search"]["pgvector_runtime"] == "not_available_without_civiccore_pgvector"
    assert payload["results"] == []
    assert payload["empty_state"]["message"] == "No public CivicCode results matched that search."


@pytest.mark.skipif(
    shutil.which("docker") is None or not _ollama_embedding_available(),
    reason="Docker and local nomic-embed-text are required for pgvector runtime proof",
)
def test_postgres_pgvector_runtime_search_retrieves_zero_literal_overlap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    daemon = subprocess.run(["docker", "info"], check=False, capture_output=True, text=True)
    if daemon.returncode != 0:
        pytest.skip("Docker daemon is not available for the pgvector runtime proof.")

    name = f"civiccode-pgvector-search-{uuid.uuid4().hex[:12]}"
    db_user = "postgres"
    db_name = "civiccode_test"
    db_secret = "post" + "gres"
    subprocess.run(
        [
            "docker",
            "run",
            "--name",
            name,
            "-e",
            "POSTGRES_" + f"PASSWORD={db_secret}",
            "-e",
            f"POSTGRES_USER={db_user}",
            "-e",
            f"POSTGRES_DB={db_name}",
            "-p",
            "5432",
            "-d",
            "pgvector/pgvector:pg17",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        mapped = subprocess.run(
            ["docker", "port", name, "5432/tcp"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        port = mapped.rsplit(":", maxsplit=1)[-1]
        engine = create_engine(
            f"postgresql+psycopg2://{db_user}:{db_secret}@localhost:{port}/{db_name}"
        )
        deadline = time.monotonic() + 30
        while True:
            try:
                with engine.connect() as connection:
                    connection.exec_driver_sql("select 1")
                break
            except Exception:
                if time.monotonic() > deadline:
                    raise
                time.sleep(1)

        monkeypatch.setenv("CIVICCODE_EMBEDDING_MODE", "ollama")
        monkeypatch.setenv("CIVICCODE_OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        monkeypatch.setenv("CIVICCODE_OLLAMA_EMBEDDING_URL", "http://127.0.0.1:11434")
        store = SectionLifecycleRepository(engine=engine)
        store.create_title({"title_id": "title_6", "title_number": "6", "title_name": "Animals"})
        store.create_chapter(
            {
                "chapter_id": "chapter_6_12",
                "title_id": "title_6",
                "chapter_number": "6.12",
                "chapter_name": "Urban Livestock",
            }
        )
        store.create_section(
            {
                "section_id": "sec_chickens",
                "chapter_id": "chapter_6_12",
                "section_number": "6.12.040",
                "section_heading": "Backyard chickens",
            }
        )
        store.create_version(
            {
                "version_id": "v_chickens_current",
                "section_id": "sec_chickens",
                "source_id": "municode_active",
                "version_label": "Current",
                "body": "Residents may keep up to six backyard chickens with a city permit.",
                "effective_start": date(2026, 1, 1),
                "status": "adopted",
                "is_current": True,
            }
        )
        store.create_section(
            {
                "section_id": "sec_noise",
                "chapter_id": "chapter_6_12",
                "section_number": "6.12.080",
                "section_heading": "Noise limits",
            }
        )
        store.create_version(
            {
                "version_id": "v_noise_current",
                "section_id": "sec_noise",
                "source_id": "municode_active",
                "version_label": "Current",
                "body": "Amplified music may not exceed the city nighttime decibel limit.",
                "effective_start": date(2026, 1, 1),
                "status": "adopted",
                "is_current": True,
            }
        )
        config = embedding_config_from_env()
        assert config is not None
        chicken_embedding, noise_embedding = embed_texts(
            [
                "6.12.040 Backyard chickens. Residents may keep hens with city permits.",
                "6.12.080 Noise limits. Amplified music must obey nighttime decibel limits.",
            ],
            config=config,
        )
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS public.document_chunks (
                        content_text text NOT NULL,
                        embedding vector(768) NOT NULL
                    )
                    """
                )
            )
            connection.execute(text("DELETE FROM public.document_chunks"))
            connection.execute(
                text(
                    """
                    INSERT INTO public.document_chunks (content_text, embedding)
                    VALUES (:chicken_text, CAST(:chicken_embedding AS vector)),
                           (:noise_text, CAST(:noise_embedding AS vector))
                    """
                ),
                {
                    "chicken_text": (
                        "6.12.040 Backyard chickens. Residents may keep up to six backyard "
                        "chickens with a city permit."
                    ),
                    "chicken_embedding": _pgvector_literal(chicken_embedding),
                    "noise_text": (
                        "6.12.080 Noise limits. Amplified music may not exceed the city "
                        "nighttime decibel limit."
                    ),
                    "noise_embedding": _pgvector_literal(noise_embedding),
                },
            )

        payload = store.search("poultry coops")

        assert payload["semantic_search"]["enabled"] is True
        assert payload["semantic_search"]["pgvector_runtime"] == "postgresql_pgvector"
        assert payload["results"][0]["section_number"] == "6.12.040"
        assert payload["results"][0]["match_type"] == "semantic"
        assert payload["results"][0]["semantic_score"] >= 0.58

        low_relevance = store.search("astronomy telescope nebula")

        assert low_relevance["results"] == []
        assert low_relevance["empty_state"]["message"] == "No public CivicCode results matched that search."
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=False, capture_output=True, text=True)


def _pgvector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{value:.9f}" for value in embedding) + "]"


@pytest.mark.asyncio
async def test_search_covers_title_and_chapter_names(client: AsyncClient) -> None:
    await seed_search_fixture(client)

    title_response = await client.get("/api/v1/civiccode/search", params={"q": "animals"})
    chapter_response = await client.get(
        "/api/v1/civiccode/search",
        params={"q": "urban livestock"},
    )

    assert title_response.status_code == 200
    assert chapter_response.status_code == 200
    assert title_response.json()["results"][0]["section_number"] == "6.12.040"
    assert chapter_response.json()["results"][0]["section_number"] == "6.12.040"


@pytest.mark.asyncio
async def test_search_no_results_is_actionable(client: AsyncClient) -> None:
    await seed_search_fixture(client)

    response = await client.get("/api/v1/civiccode/search", params={"q": "beekeeping"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"] == []
    assert payload["empty_state"]["message"] == "No public CivicCode results matched that search."
    assert "Try an exact section number" in payload["empty_state"]["fix"]


@pytest.mark.asyncio
async def test_section_permalink_is_stable_across_text_revisions(client: AsyncClient) -> None:
    await seed_search_fixture(client)
    before = await client.get("/api/v1/civiccode/sections/sec_chickens/permalink")

    update = await client.post(
        "/api/v1/civiccode/sections/sec_chickens/versions",
        headers=STAFF_HEADERS,
        json={
            "version_id": "v_chickens_future",
            "section_id": "sec_chickens",
            "source_id": "municode_active",
            "version_label": "Future",
            "body": "Residents may keep up to four backyard chickens with a city permit.",
            "effective_start": "2027-01-01",
            "status": "adopted",
            "is_current": True,
            "prior_version_id": "v_chickens_current",
        },
    )
    assert update.status_code == 201, update.text
    after = await client.get("/api/v1/civiccode/sections/sec_chickens/permalink")

    assert before.status_code == 200
    assert after.status_code == 200
    assert before.json()["permalink"] == after.json()["permalink"]
    assert after.json()["stable"] is True


@pytest.mark.asyncio
async def test_public_search_distinguishes_related_material_result_types(
    client: AsyncClient,
) -> None:
    await seed_search_fixture(client)

    policy = await client.get("/api/v1/civiccode/search", params={"q": "policy chicken"})
    resolution = await client.get("/api/v1/civiccode/search", params={"q": "resolution"})
    regulation = await client.get("/api/v1/civiccode/search", params={"q": "admin reg"})
    summary = await client.get("/api/v1/civiccode/search", params={"q": "approved summary"})

    assert policy.status_code == 200
    assert resolution.status_code == 200
    assert regulation.status_code == 200
    assert summary.status_code == 200
    assert {result["result_type"] for result in policy.json()["results"]} == {"policy"}
    assert {result["result_type"] for result in resolution.json()["results"]} == {"resolution"}
    assert {result["result_type"] for result in regulation.json()["results"]} == {
        "administrative_regulation"
    }
    assert {result["result_type"] for result in summary.json()["results"]} == {"approved_summary"}


@pytest.mark.asyncio
async def test_public_search_does_not_expose_internal_fields(client: AsyncClient) -> None:
    await seed_search_fixture(client)

    response = await client.get("/api/v1/civiccode/search", params={"q": "chickens"})

    assert response.status_code == 200
    serialized = str(response.json()).lower()
    assert "staff_notes" not in serialized
    assert "internal" not in serialized
    assert "source_owner" not in serialized


@pytest.mark.asyncio
async def test_empty_search_query_returns_actionable_422(client: AsyncClient) -> None:
    response = await client.get("/api/v1/civiccode/search", params={"q": "   "})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "cannot be empty" in detail["message"]
    assert "section number or plain-language phrase" in detail["fix"]


def test_docs_and_changelog_record_search_without_claiming_answers_or_public_ui() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lower()
    manual = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8").lower()
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8").lower()

    for document_text in [changelog, manual, landing]:
        assert "search" in document_text
        assert "permalink" in document_text
        assert "code answers are available" not in document_text
        assert "public lookup ui is available" not in document_text
