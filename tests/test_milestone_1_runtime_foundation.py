from __future__ import annotations

import importlib
import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


ROOT = Path(__file__).resolve().parents[1]


def load_pyproject() -> dict:
    pyproject = ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist for Townlight Code runtime foundation."
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))


def load_app_module():
    try:
        spec = importlib.util.find_spec("townlight_code.main")
    except ModuleNotFoundError:
        spec = None
    assert spec is not None, "townlight_code.main must be importable."
    return importlib.import_module("townlight_code.main")


def test_pyproject_declares_runtime_package_and_release_version() -> None:
    data = load_pyproject()

    assert data["project"]["name"] == "townlight-code"
    assert data["project"]["version"] == "1.0.9"
    assert "Townlight Code" in data["project"]["description"]


def test_pyproject_consumes_published_townlight_core_shared_ingestion_release() -> None:
    data = load_pyproject()
    dependencies = data["project"]["dependencies"]

    assert "townlight-core==1.3.0.dev2" in dependencies
    assert not any("townlight_core>=" in dep or "townlight_core~=" in dep for dep in dependencies)


def test_pyproject_declares_foundation_runtime_and_test_dependencies() -> None:
    data = load_pyproject()
    dependencies = "\n".join(data["project"]["dependencies"])
    dev_dependencies = "\n".join(data["project"]["optional-dependencies"]["dev"])

    assert "fastapi" in dependencies
    assert "sqlalchemy" in dependencies
    assert "alembic" in dependencies
    assert "psycopg2-binary" in dependencies
    assert "uvicorn" in dependencies
    assert "pytest" in dev_dependencies
    assert "httpx" in dev_dependencies
    assert "ruff" in dev_dependencies


def test_runtime_package_layout_exists() -> None:
    expected_paths = [
        ROOT / "townlight_code" / "__init__.py",
        ROOT / "townlight_code" / "main.py",
    ]

    for path in expected_paths:
        assert path.exists(), f"Missing runtime foundation file: {path.relative_to(ROOT)}"


def test_public_fastapi_app_import_path_exists() -> None:
    module = load_app_module()
    assert isinstance(module.app, FastAPI)
    assert module.app.title == "TownlightCode"


@pytest.mark.asyncio
async def test_root_endpoint_explains_current_user_experience() -> None:
    module = load_app_module()
    async with AsyncClient(
        transport=ASGITransport(app=module.app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "TownlightCode"
    assert payload["status"] == "docker demo codifier runtime"
    assert payload["code_answer_behavior"] == "citation_grounded"
    assert payload["api_base"] == "/api/v1/townlight_code"
    assert payload["future_public_path"] == "/townlight_code"
    assert payload["next_step"] == (
        "TownlightCode v1.0.9 persists section/version lifecycle records, "
        "popular-question discovery aids, staff notes, plain-language "
        "summaries, TownlightMeetings handoff records, handoff audit events, and "
        "local import job ledgers, codifier sync source state, and "
        "operational retry, replay, and cursor state "
        "in the configured database; next work follows the Townlight roadmap."
    )
    assert "not implemented" in payload["message"].lower()
    assert "source registry" in payload["message"]
    assert "citations" in payload["message"]
    assert "Q&A" in payload["message"]
    assert "Staff" in payload["message"]
    assert "plain-language summaries" in payload["message"]
    assert "TownlightMeetings" in payload["message"]
    assert "handoff" in payload["message"]
    assert "live llm" in payload["message"].lower()
    assert "public lookup" in payload["message"].lower()
    assert "local file-drop" in payload["message"].lower()
    assert "provenance" in payload["message"].lower()
    assert "records-ready" in payload["message"].lower()
    assert "source metadata" in payload["message"].lower()
    assert "codifier sync readiness" in payload["message"].lower()
    assert "circuit-breaker health" in payload["message"].lower()


@pytest.mark.asyncio
async def test_health_endpoint_is_actionable_for_it_staff() -> None:
    module = load_app_module()
    async with AsyncClient(
        transport=ASGITransport(app=module.app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "status": "ok",
        "service": "townlight_code",
        "version": "1.0.9",
        "townlight_core": "1.3.0.dev2",
    }


def test_ci_runs_pytest_docs_and_placeholder_gates() -> None:
    workflow = ROOT / ".github" / "workflows" / "verify.yml"
    text = workflow.read_text(encoding="utf-8")

    pin = json.loads((ROOT / 'config/core-source.json').read_text(encoding='utf-8'))
    assert pin['distribution'] == 'townlight-core'
    assert pin['version'] == '1.3.0.dev2'
    assert len(pin['commit']) == 40 and all(character in '0123456789abcdef' for character in pin['commit'])
    assert "python scripts/install-core-candidate.py" in text
    assert "python scripts/install-core-candidate.py --verify-installed" in text
    assert "core/releases/download" not in text
    assert "townlight_core-1.1.0-py3-none-any.whl" not in text
    assert "python -m pytest" in text
    assert "bash scripts/verify-docs.sh" in text
    assert "python scripts/check-townlight_core-placeholder-imports.py" in text
    assert "Run staff browser QA" in text
    assert "Run public browser QA" in text
    assert "Verify release packaging gate" in text
    assert "python -m ruff check ." in text
    assert "npm run typecheck" in text
    assert "npm run build" in text
    assert "python -m build" in text
    assert "VERIFY-RELEASE: PASSED" in text


def test_release_gate_prefers_native_unix_python_and_isolates_provenance_install() -> None:
    script = ROOT / "scripts" / "verify-release.sh"
    text = script.read_text(encoding="utf-8")

    python3_probe = "command -v python3"
    python_probe = "command -v python)"
    assert python3_probe in text
    assert python_probe in text
    assert text.index(python3_probe) < text.index(python_probe)
    assert "venv.EnvBuilder(with_pip=True)" in text
    assert 'tempfile.mkdtemp(prefix="townlight_code-release-provenance-")' in text
    assert "pip install --force-reinstall" not in text


def test_documentation_gate_blocks_stale_product_ready_marketing_claims() -> None:
    script = ROOT / "scripts" / "verify-docs.sh"
    text = script.read_text(encoding="utf-8")

    assert "current product line" in text
    assert "current durable operational-state product release" in text
    assert "current durable operational-state product line" in text


def test_placeholder_import_gate_passes_for_runtime_source() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check-townlight_core-placeholder-imports.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PLACEHOLDER-IMPORT-CHECK: PASSED" in result.stdout


def test_current_facing_docs_describe_runtime_foundation_honestly() -> None:
    for relative in ("README.md", "README.txt", "USER-MANUAL.md", "docs/index.html"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "Townlight Beta 1" in text
        assert "AGPL-3.0-only" in text
        assert "1.0.9" in text
        for claim in ("scaffold only", "not installable yet", "legal advice is available", "automatic ordinance codification is available"):
            assert claim not in text.lower()
