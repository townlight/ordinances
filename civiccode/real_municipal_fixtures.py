"""Real municipal-code fixtures for CivicCode release evidence.

The local bundle is intentionally bounded, but it is no longer synthetic: it
contains multiple Portland City Code sections transcribed from official
Portland.gov chapter pages with package-local source artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from typing import Any


PORTLAND_TITLE_13_RETRIEVED_AT = "2026-05-21T18:30:00Z"
PORTLAND_CHAPTER_13_10_SOURCE_URL = "https://www.portland.gov/code/13/10"
PORTLAND_CHAPTER_13_40_SOURCE_URL = "https://www.portland.gov/code/13/40"


@dataclass(frozen=True)
class PortlandSectionFixture:
    section_id: str
    section_number: str
    heading: str
    source_id: str
    source_url: str
    file_reference: str
    body: str
    effective_start: str
    adoption_event_id: str | None = None


PORTLAND_SECTIONS = [
    PortlandSectionFixture(
        section_id="sec_portland_13_10_010",
        section_number="13.10.010",
        heading="Purpose",
        source_id="src_portland_code_13_10",
        source_url=PORTLAND_CHAPTER_13_10_SOURCE_URL,
        file_reference="fixtures/portland/code/13.10-purpose-and-definitions.txt",
        body=(
            "The purpose of Title 13 is to allow Portland residents to keep bees and "
            "livestock in an urban environment under circumstances that support the "
            "health and safety of people and animals and reduce animal-related "
            "nuisances such as vermin, smells, noise, and property damage."
        ),
        effective_start="2025-01-10",
    ),
    PortlandSectionFixture(
        section_id="sec_portland_13_10_020",
        section_number="13.10.020",
        heading="Definitions",
        source_id="src_portland_code_13_10",
        source_url=PORTLAND_CHAPTER_13_10_SOURCE_URL,
        file_reference="fixtures/portland/code/13.10-purpose-and-definitions.txt",
        body=(
            "Livestock include fowl, horses, cattle, sheep, goats, llamas, emu, "
            "ostriches, rabbits, swine, or other domesticated farm animals excluding "
            "dogs and cats. Backyard livestock are small animals kept humanely in "
            "urban backyards, including small domestic fowl, rabbits, and some "
            "miniature breeds of goats, sheep, and pigs."
        ),
        effective_start="2025-01-10",
        adoption_event_id="portland_ordinance_192002",
    ),
    PortlandSectionFixture(
        section_id="sec_portland_13_40_010",
        section_number="13.40.010",
        heading="Owner Responsibilities",
        source_id="src_portland_code_13_40",
        source_url=PORTLAND_CHAPTER_13_40_SOURCE_URL,
        file_reference="fixtures/portland/code/13.40-keeping-livestock.txt",
        body=(
            "Livestock keepers must meet Title 13 provisions and applicable "
            "administrative rules. The keeping of livestock must not create a "
            "nuisance or disturb neighboring residents due to noise, odor, damage, "
            "or threats to public health."
        ),
        effective_start="2025-01-10",
        adoption_event_id="portland_ordinance_192002",
    ),
    PortlandSectionFixture(
        section_id="sec_portland_13_40_020",
        section_number="13.40.020",
        heading="Backyard Livestock",
        source_id="src_portland_code_13_40",
        source_url=PORTLAND_CHAPTER_13_40_SOURCE_URL,
        file_reference="fixtures/portland/code/13.40-keeping-livestock.txt",
        body=(
            "Up to four chickens, ducks, pigeons, or similarly sized domestic fowl "
            "may be kept on any lot. Up to six small domestic fowl may be kept on "
            "lots 10,000 square feet and greater. Roosters may not be kept except "
            "for agricultural purposes on lots that allow agricultural uses."
        ),
        effective_start="2025-01-10",
        adoption_event_id="portland_ordinance_192002",
    ),
    PortlandSectionFixture(
        section_id="sec_portland_13_40_030",
        section_number="13.40.030",
        heading="Large Livestock",
        source_id="src_portland_code_13_40",
        source_url=PORTLAND_CHAPTER_13_40_SOURCE_URL,
        file_reference="fixtures/portland/code/13.40-keeping-livestock.txt",
        body=(
            "Large livestock may only be kept on lots 20,000 square feet or greater "
            "that allow agricultural uses through Portland City Code Title 33 "
            "Zoning or that have an approved conditional use. Additional animals "
            "depend on lot size and animal type."
        ),
        effective_start="2025-01-10",
        adoption_event_id="portland_ordinance_192002",
    ),
]


def portland_backyard_livestock_payload() -> dict[str, Any]:
    """Return a source-attributed local-bundle import for Portland Title 13."""
    source_payloads = [
        _source_payload(
            source_id="src_portland_code_13_10",
            name="Portland City Code Chapter 13.10",
            source_url=PORTLAND_CHAPTER_13_10_SOURCE_URL,
            file_reference="fixtures/portland/code/13.10-purpose-and-definitions.txt",
            note="Official chapter page for purpose and definitions in Title 13.",
        ),
        _source_payload(
            source_id="src_portland_code_13_40",
            name="Portland City Code Chapter 13.40",
            source_url=PORTLAND_CHAPTER_13_40_SOURCE_URL,
            file_reference="fixtures/portland/code/13.40-keeping-livestock.txt",
            note=(
                "Official chapter page for keeping livestock; sections cite "
                "Ordinance 192002 effective January 10, 2025."
            ),
        ),
    ]
    return {
        "job_id": "job_portland_title_13_livestock",
        "connector_type": "official_html_extract",
        "sources": source_payloads,
        "source": source_payloads[1],
        "titles": [
            {
                "title_id": "title_portland_13",
                "title_number": "13",
                "title_name": "Bees and Livestock",
            }
        ],
        "chapters": [
            {
                "chapter_id": "chapter_portland_13_10",
                "title_id": "title_portland_13",
                "chapter_number": "13.10",
                "chapter_name": "Purpose and Definitions",
            },
            {
                "chapter_id": "chapter_portland_13_40",
                "title_id": "title_portland_13",
                "chapter_number": "13.40",
                "chapter_name": "Keeping Livestock",
            },
        ],
        "sections": [_section_payload(section) for section in PORTLAND_SECTIONS],
        "versions": [_version_payload(section) for section in PORTLAND_SECTIONS],
        "provenance": {
            "fixture_name": "fixtures/portland/code",
            "retrieval_method": "official_web_page_extract",
            "source_urls": [
                PORTLAND_CHAPTER_13_10_SOURCE_URL,
                PORTLAND_CHAPTER_13_40_SOURCE_URL,
            ],
            "source_page_label": "City code chapter",
            "section_count": len(PORTLAND_SECTIONS),
            "source_artifacts_present": _source_artifacts_present(),
        },
    }


def _source_payload(
    *,
    source_id: str,
    name: str,
    source_url: str,
    file_reference: str,
    note: str,
) -> dict[str, Any]:
    source_text = _read_fixture(file_reference)
    checksum = sha256((source_url + PORTLAND_TITLE_13_RETRIEVED_AT + source_text).encode("utf-8")).hexdigest()
    return {
        "source_id": source_id,
        "name": name,
        "publisher": "City of Portland, Oregon",
        "source_type": "official_web_export",
        "source_category": "municipal_code",
        "source_url": source_url,
        "file_reference": file_reference,
        "retrieved_at": PORTLAND_TITLE_13_RETRIEVED_AT,
        "retrieval_method": "official_web_page_extract",
        "checksum": checksum,
        "source_owner": "City Auditor / City Code",
        "is_official": True,
        "status": "active",
        "official_status_note": note,
    }


def _section_payload(section: PortlandSectionFixture) -> dict[str, Any]:
    chapter_id = "chapter_portland_13_10" if section.section_number.startswith("13.10") else "chapter_portland_13_40"
    return {
        "section_id": section.section_id,
        "chapter_id": chapter_id,
        "section_number": section.section_number,
        "section_heading": section.heading,
        "administrative_regulation_refs": [],
        "resolution_refs": [section.adoption_event_id] if section.adoption_event_id else [],
        "policy_refs": ["Portland City Code Title 13"],
        "approved_summary_refs": [],
    }


def _version_payload(section: PortlandSectionFixture) -> dict[str, Any]:
    return {
        "version_id": f"version_{section.section_id}_current",
        "section_id": section.section_id,
        "source_id": section.source_id,
        "version_label": "current as retrieved 2026-05-21",
        "body": section.body,
        "effective_start": section.effective_start,
        "effective_end": None,
        "status": "adopted",
        "is_current": True,
        "adoption_event_id": section.adoption_event_id,
    }


def _read_fixture(file_reference: str) -> str:
    return files("civiccode").joinpath(file_reference).read_text(encoding="utf-8")


def _source_artifacts_present() -> bool:
    return all(
        files("civiccode").joinpath(section.file_reference).is_file()
        for section in PORTLAND_SECTIONS
    )


PORTLAND_BACKYARD_LIVESTOCK_SOURCE_URL = PORTLAND_CHAPTER_13_40_SOURCE_URL
PORTLAND_BACKYARD_LIVESTOCK_RETRIEVED_AT = PORTLAND_TITLE_13_RETRIEVED_AT
PORTLAND_BACKYARD_LIVESTOCK_BODY = PORTLAND_SECTIONS[3].body


__all__ = [
    "PORTLAND_BACKYARD_LIVESTOCK_BODY",
    "PORTLAND_BACKYARD_LIVESTOCK_RETRIEVED_AT",
    "PORTLAND_BACKYARD_LIVESTOCK_SOURCE_URL",
    "PORTLAND_CHAPTER_13_10_SOURCE_URL",
    "PORTLAND_CHAPTER_13_40_SOURCE_URL",
    "PORTLAND_SECTIONS",
    "portland_backyard_livestock_payload",
]
