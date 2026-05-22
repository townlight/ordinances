from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from civiccode.shared_ingestion import (  # noqa: E402
    _SECTION_RE,
    _extract_pdf_column_text,
    _extract_sections,
    _normalize_text,
    _trim_non_code_appendices,
)


POLLUTION_PATTERNS = (
    "LONGMONT CODE",
    "Supp. No.",
    "CD4:",
    "CD4:64.1",
    "LAND DEVELOPMENT CODE",
    "HEALTH AND SAFETY",
    "BUSINESS TAXES, LICENSES AND REGULATIONS",
    "REVENUE AND FINANCE",
)
REQUIRED_SAMPLE_SECTIONS = (
    "1.12.010",
    "2.04.010",
    "3.04.010",
    "4.12.040",
    "4.12.050",
    "4.12.160",
    "5.04.010",
    "6.04.010",
    "8.04.010",
    "9.04.010",
    "10.04.010",
    "11.12.010",
    "12.04.010",
    "13.04.010",
    "14.04.010",
    "15.02.010",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quantify and sample CivicCode Longmont section-body fidelity against source PDF text."
    )
    parser.add_argument(
        "--pdf",
        default=str(
            Path(__file__).resolve().parents[2]
            / "longmont-code-corpus"
            / "Longmont, CO Code of Ordinances.pdf"
        ),
    )
    parser.add_argument("--sample-count", type=int, default=25)
    args = parser.parse_args()
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    source_text = _extract_pdf_column_text(pdf_path)
    normalized = _normalize_text(_trim_non_code_appendices(source_text))
    sections = _extract_sections(source_text)
    source_sections = _source_section_snippets(normalized)
    sample_numbers = _sample_section_numbers(sections, args.sample_count)
    samples = [
        _sample_for_section(section, source_sections.get(section["number"], ""))
        for section in sections
        if section["number"] in sample_numbers
    ]
    output = {
        "pdf": str(pdf_path),
        "pdf_size_bytes": pdf_path.stat().st_size,
        "section_count": len(sections),
        "quality": _quality_counts(sections),
        "samples_requested": args.sample_count,
        "samples_returned": len(samples),
        "samples": samples,
    }
    print("CIVICCODE-LONGMONT-SECTION-FIDELITY-PROOF")
    print(json.dumps(output, indent=2, default=str))
    return 0


def _quality_counts(sections: list[dict[str, str]]) -> dict[str, Any]:
    empty = []
    too_short = []
    polluted = []
    for section in sections:
        body = section["body"].strip()
        if not body:
            empty.append(section["number"])
        if len(body) < 160:
            too_short.append(section["number"])
        if _is_polluted(body):
            polluted.append(section["number"])
    return {
        "empty_body_count": len(empty),
        "too_short_body_count": len(too_short),
        "header_footer_polluted_count": len(polluted),
        "empty_body_sections": empty[:25],
        "too_short_body_sections": too_short[:25],
        "header_footer_polluted_sections": polluted[:25],
    }


def _source_section_snippets(normalized_text: str) -> dict[str, str]:
    matches = list(_SECTION_RE.finditer(normalized_text))
    snippets: dict[str, str] = {}
    for index, match in enumerate(matches):
        number = match.group("number")
        if number in snippets:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized_text)
        snippet = normalized_text[match.start() : end].strip()
        if len(snippet) < 80:
            continue
        snippets[number] = snippet
    return snippets


def _sample_section_numbers(sections: list[dict[str, str]], sample_count: int) -> set[str]:
    by_number = {section["number"]: section for section in sections}
    selected = [number for number in REQUIRED_SAMPLE_SECTIONS if number in by_number]
    if len(selected) < sample_count and sections:
        stride = max(1, len(sections) // sample_count)
        for index in range(0, len(sections), stride):
            number = sections[index]["number"]
            if number not in selected:
                selected.append(number)
            if len(selected) >= sample_count:
                break
    return set(selected[:sample_count])


def _sample_for_section(section: dict[str, str], source_text: str) -> dict[str, Any]:
    body = section["body"].strip()
    source_excerpt = _compact(source_text)
    structured_excerpt = _compact(body)
    return {
        "section_number": section["number"],
        "heading": section["heading"],
        "structured_body_length": len(body),
        "source_pdf_excerpt": source_excerpt[:900],
        "structured_body_excerpt": structured_excerpt[:900],
        "body_excerpt_found_in_source": structured_excerpt[:240] in source_excerpt,
        "header_footer_polluted": _is_polluted(body),
        "too_short": len(body) < 160,
    }


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _is_polluted(value: str) -> bool:
    return any(pattern in value for pattern in POLLUTION_PATTERNS)


if __name__ == "__main__":
    raise SystemExit(main())
