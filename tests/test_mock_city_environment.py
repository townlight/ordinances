from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from townlight_code.mock_city_environment import (
    MOCK_CITY_CODE_CHANGED_SINCE,
    MOCK_CITY_NAME,
    mock_city_code_report,
    mock_city_codifier_contracts,
    mock_city_import_payload,
    run_mock_city_code_contract_suite,
)


ROOT = Path(__file__).resolve().parents[1]


def test_mock_city_contracts_cover_supported_codifier_interfaces() -> None:
    contracts = {contract.connector: contract for contract in mock_city_codifier_contracts()}

    assert MOCK_CITY_NAME == "City of Brookfield"
    assert set(contracts) == {"municode", "american_legal", "code_publishing", "general_code"}
    assert contracts["municode"].source_type == "municode"
    assert contracts["american_legal"].publisher == "American Legal Publishing"
    assert contracts["code_publishing"].delta_query_param == "changed_since"
    assert contracts["general_code"].source_url.startswith("https://ecode360.com/")
    assert all(contract.auth_method == "public_export" for contract in contracts.values())


def test_mock_city_payloads_are_valid_local_import_bundles() -> None:
    for contract in mock_city_codifier_contracts():
        payload = mock_city_import_payload(contract)

        assert payload["connector_type"] == "official_html_extract"
        assert payload["source"]["source_type"] == contract.source_type
        assert payload["source"]["status"] == "active"
        assert payload["source"]["is_official"] is True
        assert payload["source"]["retrieved_at"] == MOCK_CITY_CODE_CHANGED_SINCE
        assert payload["versions"][0]["source_id"] == payload["source"]["source_id"]
        assert payload["versions"][0]["is_current"] is True


def test_mock_city_suite_imports_codifier_sources_without_network() -> None:
    checks = run_mock_city_code_contract_suite(base_url="https://mock-city.example.gov")

    assert len(checks) == 4
    assert all(check.ok for check in checks)
    by_connector = {check.connector: check for check in checks}
    assert by_connector["municode"].checked_sections == ("6.12.040",)
    assert "updatedSince=2026-05-01T12%3A00%3A00Z" in by_connector["municode"].delta_request_url
    assert "modifiedAfter=2026-05-01T12%3A00%3A00Z" in by_connector["american_legal"].delta_request_url
    assert "changed_since=2026-05-01T12%3A00%3A00Z" in by_connector["code_publishing"].delta_request_url
    assert "lastModified=2026-05-01T12%3A00%3A00Z" in by_connector["general_code"].delta_request_url
    assert "network" not in " ".join(check.message.lower() for check in checks)


def test_mock_city_report_reuses_townlight_core_idp_and_backup_contracts() -> None:
    report = mock_city_code_report()

    assert report["ready"] is True
    assert report["network_calls"] is False
    assert report["idp_contract"]["provider"] == "Brookfield Entra ID"
    assert report["backup_retention_contract"]["city"] == MOCK_CITY_NAME
    assert report["backup_retention_checks"][0]["ok"] is True
    assert "dump.sha256" in report["backup_retention_checks"][0]["checked_fields"]


def test_mock_city_report_is_secret_free() -> None:
    serialized = json.dumps(mock_city_code_report()).lower()

    assert "password" not in serialized
    assert "secret" not in serialized
    assert "token_value" not in serialized
    assert "api_key_value" not in serialized
    assert "mock-client-secret" not in serialized


def test_mock_city_environment_cli_writes_reusable_report(tmp_path: Path) -> None:
    output = tmp_path / "mock-city-code-report.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_mock_city_environment_suite.py",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "network_calls=false" in result.stdout
    assert "MOCK-CITY-CODE-ENVIRONMENT-SUITE: PASSED" in result.stdout
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["mock_city"] == MOCK_CITY_NAME
    assert report["ready"] is True
    assert {contract["connector"] for contract in report["contracts"]} == {
        "municode",
        "american_legal",
        "code_publishing",
        "general_code",
    }
    assert {check["connector"] for check in report["checks"]} == {
        "municode",
        "american_legal",
        "code_publishing",
        "general_code",
    }
