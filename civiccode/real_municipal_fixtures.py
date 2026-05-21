"""Small real municipal-code fixtures for CivicCode release evidence.

The fixtures are intentionally tiny and source-attributed. They prove the local
bundle import path can ingest non-fabricated municipal code data without adding
network calls to tests or the installed runtime.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any


PORTLAND_BACKYARD_LIVESTOCK_SOURCE_URL = "https://www.portland.gov/code/13/40/020"
PORTLAND_BACKYARD_LIVESTOCK_RETRIEVED_AT = "2026-05-21T18:30:00Z"
PORTLAND_BACKYARD_LIVESTOCK_BODY = (
    "Up to four chickens, ducks, pigeons, or similarly sized domestic fowl may "
    "be kept on any lot. Up to six small domestic fowl may be kept on lots "
    "10,000 square feet and greater. Roosters are not allowed except for "
    "agricultural purposes on lots that allow agricultural uses."
)


def portland_backyard_livestock_payload() -> dict[str, Any]:
    """Return an attributed local-bundle import for a real Portland code section."""
    checksum = sha256(
        (
            PORTLAND_BACKYARD_LIVESTOCK_SOURCE_URL
            + PORTLAND_BACKYARD_LIVESTOCK_RETRIEVED_AT
            + PORTLAND_BACKYARD_LIVESTOCK_BODY
        ).encode("utf-8")
    ).hexdigest()
    return {
        "job_id": "job_portland_13_40_020",
        "connector_type": "official_html_extract",
        "source": {
            "source_id": "src_portland_code_13_40_020",
            "name": "Portland City Code section 13.40.020",
            "publisher": "City of Portland, Oregon",
            "source_type": "official_web_export",
            "source_category": "municipal_code",
            "source_url": PORTLAND_BACKYARD_LIVESTOCK_SOURCE_URL,
            "file_reference": "fixtures/portland/code/13.40.020-backyard-livestock.html",
            "retrieved_at": PORTLAND_BACKYARD_LIVESTOCK_RETRIEVED_AT,
            "retrieval_method": "official_web_page_extract",
            "checksum": checksum,
            "source_owner": "City Auditor / City Code",
            "is_official": True,
            "status": "active",
            "official_status_note": (
                "Source page labels this as a City code section and records "
                "Ordinance 192002 effective January 10, 2025."
            ),
        },
        "titles": [
            {
                "title_id": "title_portland_13",
                "title_number": "13",
                "title_name": "Bees and Livestock",
            }
        ],
        "chapters": [
            {
                "chapter_id": "chapter_portland_13_40",
                "title_id": "title_portland_13",
                "chapter_number": "13.40",
                "chapter_name": "Keeping Livestock",
            }
        ],
        "sections": [
            {
                "section_id": "sec_portland_13_40_020",
                "chapter_id": "chapter_portland_13_40",
                "section_number": "13.40.020",
                "section_heading": "Backyard Livestock",
                "administrative_regulation_refs": [],
                "resolution_refs": ["Ordinance 192002"],
                "policy_refs": ["Portland City Code Title 13"],
                "approved_summary_refs": [],
            }
        ],
        "versions": [
            {
                "version_id": "version_portland_13_40_020_current",
                "section_id": "sec_portland_13_40_020",
                "source_id": "src_portland_code_13_40_020",
                "version_label": "current as retrieved 2026-05-21",
                "body": PORTLAND_BACKYARD_LIVESTOCK_BODY,
                "effective_start": "2025-01-10",
                "effective_end": None,
                "status": "adopted",
                "is_current": True,
                "adoption_event_id": "portland_ordinance_192002",
            }
        ],
        "provenance": {
            "fixture_name": "fixtures/portland/code/13.40.020-backyard-livestock.html",
            "retrieval_method": "official_web_page_extract",
            "source_url": PORTLAND_BACKYARD_LIVESTOCK_SOURCE_URL,
            "source_page_label": "City code section",
        },
    }


__all__ = [
    "PORTLAND_BACKYARD_LIVESTOCK_BODY",
    "PORTLAND_BACKYARD_LIVESTOCK_RETRIEVED_AT",
    "PORTLAND_BACKYARD_LIVESTOCK_SOURCE_URL",
    "portland_backyard_livestock_payload",
]
