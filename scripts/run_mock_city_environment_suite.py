"""Run the reusable CivicCode mock-city codifier contract suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from civiccode.mock_city_environment import (
    MOCK_CITY_NAME,
    mock_city_code_report,
    mock_city_codifier_contracts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate reusable mock-city codifier contracts without contacting vendor networks."
    )
    parser.add_argument(
        "--base-url",
        default="https://mock-city.example.gov",
        help="Base URL used only to render planned request URLs. No network calls are made.",
    )
    parser.add_argument("--output", help="Optional JSON report path.")
    parser.add_argument("--print-only", action="store_true", help="Print the reusable mock-city plan without checks.")
    return parser.parse_args()


def _write_report(path: str, payload: dict) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _print_plan(base_url: str) -> int:
    print("Townlight Code mock city environment suite")
    print(f"mock_city={MOCK_CITY_NAME}")
    print("network_calls=false")
    print(f"base_url={base_url}")
    print("Reusable codifier/source contracts:")
    for contract in mock_city_codifier_contracts():
        print(
            f"- {contract.connector}: {contract.retrieval_method} {contract.source_url} "
            f"auth={contract.auth_method} status={contract.interface_status} "
            f"delta={contract.delta_query_param}"
        )
    print("Reusable municipal IdP and backup-retention contracts come from civiccore.testing.mock_city.")
    print("Fix path: module teams should reuse these contracts and add only module-specific assertions.")
    print("MOCK-CITY-CODE-ENVIRONMENT-SUITE: PLAN")
    return 0


def main() -> int:
    args = parse_args()
    if args.print_only:
        return _print_plan(args.base_url)

    payload = mock_city_code_report(base_url=args.base_url)
    if args.output:
        _write_report(args.output, payload)

    print("Townlight Code mock city environment suite")
    print(f"mock_city={payload['mock_city']}")
    print(f"ready={str(payload['ready']).lower()}")
    print("network_calls=false")
    for check in payload["checks"]:
        status = "PASS" if check["ok"] else "FAIL"
        print(f"[{status}] {check['connector']}: {check['message']}")
        print(f"  fix: {check['fix']}")
        print(f"  planned_delta_url: {check['delta_request_url']}")
    for check in payload["idp_checks"]:
        status = "PASS" if check["ok"] else "FAIL"
        print(f"[{status}] municipal-idp: {check['message']}")
        print(f"  fix: {check['fix']}")
    for check in payload["backup_retention_checks"]:
        status = "PASS" if check["ok"] else "FAIL"
        print(f"[{status}] backup-retention: {check['message']}")
        print(f"  fix: {check['fix']}")
    print(
        "MOCK-CITY-CODE-ENVIRONMENT-SUITE: PASSED"
        if payload["ready"]
        else "MOCK-CITY-CODE-ENVIRONMENT-SUITE: FAILED"
    )
    return 0 if payload["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
