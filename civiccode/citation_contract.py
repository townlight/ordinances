"""Deterministic citation contract for CivicCode Milestone 6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CitationRefusal:
    """Structured refusal object for unsafe citation requests."""

    reason: str
    fix: str
    refusal_type: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "refused",
            "refusal_type": self.refusal_type,
            "reason": self.reason,
            "fix": self.fix,
            "citation": None,
            "classification": "information_not_determination",
            "code_answer_behavior": "not_available",
        }


def build_citation_payload(
    *,
    section: dict[str, Any],
    version: dict[str, Any],
    title: dict[str, Any],
    chapter: dict[str, Any],
    source: dict[str, Any],
    as_of: str | None,
) -> dict[str, Any]:
    """Build a deterministic citation object without generating prose answers."""
    citation_text = (
        f"Title {title['title_number']} ({title['title_name']}), "
        f"Chapter {chapter['chapter_number']} ({chapter['chapter_name']}), "
        f"Section {section['section_number']} ({section['section_heading']}), "
        f"version {version['version_label']}, effective {version['effective_start']}"
    )
    if version["effective_end"]:
        citation_text += f" through {version['effective_end']}"

    return {
        "status": "ok",
        "citation": {
            "citation_text": citation_text,
            "body_text": version["body"],
            "section_id": section["section_id"],
            "section_number": section["section_number"],
            "version_id": version["version_id"],
            "source_id": version["source_id"],
            "source_name": source["name"],
            "source_url": source.get("source_url"),
            "effective_start": version["effective_start"],
            "effective_end": version["effective_end"],
            "as_of": as_of,
            "canonical_url": f"/civiccode/sections/{section['section_id']}",
        },
        "classification": "information_not_determination",
        "code_answer_behavior": "not_available",
    }


def refusal(reason: str, fix: str, refusal_type: str) -> dict[str, Any]:
    return CitationRefusal(reason=reason, fix=fix, refusal_type=refusal_type).to_dict()
