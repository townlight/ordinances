"""Reusable mock-city codifier contracts for CivicCode.

These contracts model the external municipal-code source interfaces a city is
likely to use without making vendor calls or embedding secrets.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from urllib.parse import quote

from civiccore.testing import (
    MOCK_CITY_NAME,
    mock_city_backup_retention_contract,
    mock_city_idp_contract,
    run_mock_city_backup_retention_suite,
    run_mock_city_idp_contract_suite,
)

from civiccode.import_connectors import ImportConnectorStore, provenance_report
from civiccode.section_lifecycle import SectionLifecycleStore
from civiccode.source_registry import SourceRegistryStore


MOCK_CITY_CODE_CHANGED_SINCE = "2026-05-01T12:00:00Z"


@dataclass(frozen=True, slots=True)
class MockCityCodifierContract:
    """A public, secret-free contract for one municipal-code source interface."""

    connector: str
    publisher: str
    source_type: str
    interface_status: str
    source_url: str
    retrieval_method: str
    auth_method: str
    delta_query_param: str
    sample_file: str
    source_owner: str = "City Clerk"

    def delta_request_url(self, *, changed_since: str = MOCK_CITY_CODE_CHANGED_SINCE) -> str:
        separator = "&" if "?" in self.source_url else "?"
        return f"{self.source_url}{separator}{self.delta_query_param}={quote(changed_since, safe='')}"

    def public_dict(self) -> dict[str, str]:
        return {
            "connector": self.connector,
            "publisher": self.publisher,
            "source_type": self.source_type,
            "interface_status": self.interface_status,
            "source_url": self.source_url,
            "retrieval_method": self.retrieval_method,
            "auth_method": self.auth_method,
            "delta_query_param": self.delta_query_param,
            "sample_file": self.sample_file,
            "source_owner": self.source_owner,
            "delta_request_url": self.delta_request_url(),
        }


@dataclass(frozen=True, slots=True)
class MockCityCodeCheck:
    """Result for one mock-city codifier contract check."""

    connector: str
    ok: bool
    message: str
    fix: str
    source_id: str | None = None
    import_job_id: str | None = None
    delta_request_url: str | None = None
    checked_sections: tuple[str, ...] = ()

    def public_dict(self) -> dict[str, Any]:
        return {
            "connector": self.connector,
            "ok": self.ok,
            "message": self.message,
            "fix": self.fix,
            "source_id": self.source_id,
            "import_job_id": self.import_job_id,
            "delta_request_url": self.delta_request_url,
            "checked_sections": list(self.checked_sections),
        }


def mock_city_codifier_contracts() -> tuple[MockCityCodifierContract, ...]:
    """Return supported codifier/source contracts for the Brookfield mock city."""
    return (
        MockCityCodifierContract(
            connector="municode",
            publisher="Municode",
            source_type="municode",
            interface_status="vendor-export-contract",
            source_url="https://library.municode.com/mock/brookfield/codes/code_of_ordinances",
            retrieval_method="official_html_extract",
            auth_method="public_export",
            delta_query_param="updatedSince",
            sample_file="mock-city/municode/brookfield-code.html",
        ),
        MockCityCodifierContract(
            connector="american_legal",
            publisher="American Legal Publishing",
            source_type="american_legal",
            interface_status="vendor-export-contract",
            source_url="https://codelibrary.amlegal.com/codes/mockbrookfield/latest/overview",
            retrieval_method="official_html_extract",
            auth_method="public_export",
            delta_query_param="modifiedAfter",
            sample_file="mock-city/american-legal/brookfield-code.html",
        ),
        MockCityCodifierContract(
            connector="code_publishing",
            publisher="Code Publishing Company",
            source_type="code_publishing",
            interface_status="vendor-export-contract",
            source_url="https://www.codepublishing.com/mock/Brookfield/",
            retrieval_method="official_html_extract",
            auth_method="public_export",
            delta_query_param="changed_since",
            sample_file="mock-city/code-publishing/brookfield-code.html",
        ),
        MockCityCodifierContract(
            connector="general_code",
            publisher="General Code",
            source_type="general_code",
            interface_status="vendor-export-contract",
            source_url="https://ecode360.com/mock/BR0000",
            retrieval_method="official_html_extract",
            auth_method="public_export",
            delta_query_param="lastModified",
            sample_file="mock-city/general-code/brookfield-code.html",
        ),
    )


def mock_city_import_payload(contract: MockCityCodifierContract) -> dict[str, Any]:
    """Build a deterministic local import payload for a codifier contract."""
    prefix = contract.connector.replace("_", "-")
    section_number = {
        "municode": "6.12.040",
        "american_legal": "8.04.020",
        "code_publishing": "12.08.110",
        "general_code": "2.16.030",
    }[contract.connector]
    section_heading = {
        "municode": "Backyard chickens",
        "american_legal": "Animal noise control",
        "code_publishing": "Park shelter reservations",
        "general_code": "Board appointment terms",
    }[contract.connector]
    source_id = f"src_{contract.connector}_brookfield"
    section_id = f"sec_{contract.connector}_sample"
    body = {
        "municode": "Residents may keep up to six backyard chickens with a city permit.",
        "american_legal": "Animal noise complaints may be reviewed by code enforcement staff.",
        "code_publishing": "Park shelter reservations require a completed city reservation form.",
        "general_code": "Board appointments use staggered terms recorded by the City Clerk.",
    }[contract.connector]
    related_refs = {
        "municode": {
            "administrative_regulation_refs": ["Animal permit application rule A-6.12"],
            "resolution_refs": ["Resolution 2026-014 fee schedule"],
            "policy_refs": ["Planning counter permit intake policy"],
            "approved_summary_refs": ["summary_brookfield_chickens"],
        },
        "american_legal": {
            "administrative_regulation_refs": ["Noise complaint intake rule A-8.04"],
            "resolution_refs": [],
            "policy_refs": ["Code enforcement response policy"],
            "approved_summary_refs": [],
        },
        "code_publishing": {
            "administrative_regulation_refs": [],
            "resolution_refs": ["Resolution 2026-022 park shelter fees"],
            "policy_refs": ["Parks reservation desk policy"],
            "approved_summary_refs": [],
        },
        "general_code": {
            "administrative_regulation_refs": [],
            "resolution_refs": [],
            "policy_refs": ["Board appointment tracking policy"],
            "approved_summary_refs": [],
        },
    }[contract.connector]
    return {
        "job_id": f"job_{contract.connector}_brookfield",
        "connector_type": "official_html_extract",
        "source": {
            "source_id": source_id,
            "name": f"{MOCK_CITY_NAME} {contract.publisher} code source",
            "publisher": contract.publisher,
            "source_type": contract.source_type,
            "source_category": "municipal_code",
            "source_url": contract.source_url,
            "file_reference": contract.sample_file,
            "retrieved_at": MOCK_CITY_CODE_CHANGED_SINCE,
            "retrieval_method": contract.retrieval_method,
            "checksum": sha256(contract.sample_file.encode("utf-8")).hexdigest(),
            "source_owner": contract.source_owner,
            "is_official": True,
            "status": "active",
        },
        "titles": [{"title_id": f"title_{prefix}", "title_number": "6", "title_name": "Health and Safety"}],
        "chapters": [
            {
                "chapter_id": f"chapter_{prefix}",
                "title_id": f"title_{prefix}",
                "chapter_number": section_number.rsplit(".", maxsplit=1)[0],
                "chapter_name": "Sample Code Chapter",
            }
        ],
        "sections": [
            {
                "section_id": section_id,
                "chapter_id": f"chapter_{prefix}",
                "section_number": section_number,
                "section_heading": section_heading,
                **related_refs,
            }
        ],
        "versions": [
            {
                "version_id": f"version_{contract.connector}_current",
                "section_id": section_id,
                "source_id": source_id,
                "version_label": "current",
                "body": body,
                "effective_start": "2026-01-01",
                "effective_end": None,
                "status": "adopted",
                "is_current": True,
                "adoption_event_id": f"ord_{contract.connector}_2026_01",
            }
        ],
        "provenance": {
            "fixture_name": contract.sample_file,
            "retrieval_method": contract.retrieval_method,
        },
    }


def run_mock_city_code_contract_suite(
    *, base_url: str = "https://mock-city.example.gov"
) -> tuple[MockCityCodeCheck, ...]:
    """Validate codifier contracts through CivicCode's local import path."""
    checks: list[MockCityCodeCheck] = []
    for contract in mock_city_codifier_contracts():
        source_store = SourceRegistryStore()
        section_store = SectionLifecycleStore()
        import_store = ImportConnectorStore(source_store=source_store, section_store=section_store)
        payload = mock_city_import_payload(contract)
        job = import_store.run_import(payload, actor="codifier-contract@brookfield.example.gov")
        source_id = payload["source"]["source_id"]
        section_number = payload["sections"][0]["section_number"]
        if job.status != "completed":
            checks.append(
                MockCityCodeCheck(
                    connector=contract.connector,
                    ok=False,
                    message=f"{contract.publisher} mock import failed: {job.failure}",
                    fix="Review the mock import payload and source metadata before reusing the contract.",
                    source_id=source_id,
                    import_job_id=job.job_id,
                    delta_request_url=_render_base_url(base_url, contract),
                )
            )
            continue
        report = provenance_report(job, source_store)
        if report["report"]["no_outbound_dependency"] is not True:
            checks.append(
                MockCityCodeCheck(
                    connector=contract.connector,
                    ok=False,
                    message=f"{contract.publisher} mock import did not prove no-outbound dependency.",
                    fix="Set no_outbound_dependency=true in provenance reports before using this contract.",
                    source_id=source_id,
                    import_job_id=job.job_id,
                    delta_request_url=_render_base_url(base_url, contract),
                )
            )
            continue
        checks.append(
            MockCityCodeCheck(
                connector=contract.connector,
                ok=True,
                message=(
                    f"{contract.publisher} mock source imports one active official code section "
                    "without outbound vendor calls."
                ),
                fix="Reuse this contract for CivicCode and add module-specific assertions only.",
                source_id=source_id,
                import_job_id=job.job_id,
                delta_request_url=_render_base_url(base_url, contract),
                checked_sections=(section_number,),
            )
        )
    return tuple(checks)


def mock_city_code_report(*, base_url: str = "https://mock-city.example.gov") -> dict[str, Any]:
    """Return the reusable CivicCode mock-city report."""
    checks = run_mock_city_code_contract_suite(base_url=base_url)
    idp_checks = run_mock_city_idp_contract_suite()
    backup_checks = run_mock_city_backup_retention_suite()
    return {
        "mock_city": MOCK_CITY_NAME,
        "network_calls": False,
        "base_url": base_url,
        "contracts": [contract.public_dict() for contract in mock_city_codifier_contracts()],
        "checks": [check.public_dict() for check in checks],
        "idp_contract": mock_city_idp_contract().public_dict(),
        "idp_checks": [check.public_dict() for check in idp_checks],
        "backup_retention_contract": mock_city_backup_retention_contract().public_dict(),
        "backup_retention_checks": [check.public_dict() for check in backup_checks],
        "ready": all(check.ok for check in checks)
        and all(check.ok for check in idp_checks)
        and all(check.ok for check in backup_checks),
    }


def _render_base_url(base_url: str, contract: MockCityCodifierContract) -> str:
    rendered = contract.delta_request_url()
    return rendered.replace("https://", f"{base_url.rstrip('/')}/planned/https/", 1)


__all__ = [
    "MOCK_CITY_CODE_CHANGED_SINCE",
    "MOCK_CITY_NAME",
    "MockCityCodeCheck",
    "MockCityCodifierContract",
    "mock_city_code_report",
    "mock_city_codifier_contracts",
    "mock_city_import_payload",
    "run_mock_city_code_contract_suite",
]
