from __future__ import annotations

import importlib
import json
from pathlib import Path
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.error
import urllib.request

import pytest
from conftest import build_suite_staff_headers
from httpx import ASGITransport, AsyncClient

from civiccode.ai_answer import load_local_llm_config


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


async def seed_qa_fixture(client: AsyncClient) -> None:
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
async def test_question_answer_returns_cited_extract_for_explicit_section(
    client: AsyncClient,
) -> None:
    await seed_qa_fixture(client)

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
    assert payload["classification"] == "information_not_determination"
    assert payload["code_answer_behavior"] == "citation_grounded"
    assert payload["llm_provider"] == "not_configured"
    assert payload["ai_authority"] == "deterministic_citation_extract"
    assert "Residents may keep up to six backyard chickens" in payload["answer"]
    assert "This is not a legal determination" in payload["answer"]
    assert len(payload["citations"]) == 1
    citation = payload["citations"][0]
    assert citation["section_id"] == "sec_chickens"
    assert citation["version_id"] == "v_chickens_current"
    assert citation["source_id"] == "municode_active"
    assert citation["effective_start"] == "2026-01-01"


@pytest.mark.asyncio
async def test_question_answer_uses_local_ollama_when_configured(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await seed_qa_fixture(client)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers["Content-Length"])
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            assert body["model"] == "civiccode-test-model"
            assert "6.12.040" in body["prompt"]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "response": (
                            "Section 6.12.040 says residents may keep backyard "
                            "chickens with the cited permit conditions."
                        )
                    }
                ).encode("utf-8")
            )

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("CIVICCODE_AI_MODE", "ollama")
    monkeypatch.setenv("CIVICCODE_OLLAMA_MODEL", "civiccode-test-model")
    monkeypatch.setenv("CIVICCODE_OLLAMA_URL", f"http://127.0.0.1:{server.server_port}")
    try:
        response = await client.post(
            "/api/v1/civiccode/questions/answer",
            json={
                "question": "What does section 6.12.040 say about backyard chickens?",
                "section_number": "6.12.040",
            },
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["llm_provider"] == "ollama"
    assert payload["llm_model"] == "civiccode-test-model"
    assert payload["ai_review_required"] is True
    assert payload["ai_authority"] == "non_authoritative_staff_review_required"
    assert "Source:" in payload["answer"]


def test_local_ollama_default_model_matches_city_core_pull(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIVICCODE_AI_MODE", "ollama")
    monkeypatch.delenv("CIVICCODE_OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("CIVICCODE_OLLAMA_URL", raising=False)

    config = load_local_llm_config()

    assert config is not None
    assert config.model == "gemma4:e4b"


def _ollama_generate_available() -> bool:
    body = json.dumps(
        {
            "model": "gemma3:12b",
            "prompt": "Reply with exactly: ok",
            "stream": False,
            "options": {"temperature": 0},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return False
    return bool(str(payload.get("response", "")).strip())


@pytest.mark.skipif(
    not _ollama_generate_available(),
    reason="gemma3:12b is not available from local Ollama",
)
@pytest.mark.asyncio
async def test_question_answer_exercises_real_local_ollama_model(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CIVICCODE_AI_MODE", "ollama")
    monkeypatch.setenv("CIVICCODE_OLLAMA_MODEL", "gemma3:12b")
    monkeypatch.setenv("CIVICCODE_OLLAMA_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("CIVICCODE_OLLAMA_TIMEOUT_SECONDS", "120")
    await seed_qa_fixture(client)

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
    assert payload["llm_provider"] == "ollama"
    assert payload["llm_model"] == "gemma3:12b"
    assert payload["ai_review_required"] is True
    assert payload["ai_authority"] == "non_authoritative_staff_review_required"
    assert payload["matched_section_number"] == "6.12.040"
    assert "Source:" in payload["answer"]
    assert "This is not a legal determination" in payload["answer"]


@pytest.mark.asyncio
async def test_question_answer_can_resolve_single_search_result(client: AsyncClient) -> None:
    await seed_qa_fixture(client)

    response = await client.post(
        "/api/v1/civiccode/questions/answer",
        json={"question": "What does the code say about backyard chickens?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["matched_section_number"] == "6.12.040"
    assert payload["citations"][0]["canonical_url"] == "/civiccode/sections/sec_chickens"


@pytest.mark.asyncio
async def test_question_answer_refuses_legal_determinations(client: AsyncClient) -> None:
    await seed_qa_fixture(client)

    response = await client.post(
        "/api/v1/civiccode/questions/answer",
        json={"question": "Am I allowed to keep chickens at 123 Main Street?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "refused"
    assert payload["refusal_type"] == "legal_determination"
    assert "cannot decide" in payload["reason"]
    assert "Ask staff" in payload["fix"]
    assert payload["code_answer_behavior"] == "not_available"


@pytest.mark.asyncio
async def test_question_answer_refuses_uncited_questions(client: AsyncClient) -> None:
    await seed_qa_fixture(client)

    response = await client.post(
        "/api/v1/civiccode/questions/answer",
        json={"question": "What does the code say about apiaries?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "refused"
    assert payload["refusal_type"] == "no_citation"
    assert payload["citation"] is None
    assert "No single adopted code section" in payload["reason"]


@pytest.mark.asyncio
async def test_question_answer_refuses_stale_source(client: AsyncClient) -> None:
    await seed_qa_fixture(client)
    assert (
        await client.post(
            "/api/v1/civiccode/sources/municode_active/transitions",
            headers=STAFF_HEADERS,
            json={
                "to_status": "stale",
                "actor": "clerk@example.gov",
                "reason": "Publisher updated the code.",
            },
        )
    ).status_code == 200

    response = await client.post(
        "/api/v1/civiccode/questions/answer",
        json={
            "question": "What does section 6.12.040 say about backyard chickens?",
            "section_number": "6.12.040",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "refused"
    assert payload["refusal_type"] == "stale_source"
    assert "not active" in payload["reason"]


def test_docs_and_changelog_record_qa_harness_without_claiming_legal_advice() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lower()
    manual = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8").lower()
    landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8").lower()

    for document_text in [changelog, manual, landing]:
        assert "citation-grounded q&a" in document_text
        assert "legal advice is available" not in document_text
        assert "uncited answers are available" not in document_text
        assert "live llm calls are enabled" not in document_text
