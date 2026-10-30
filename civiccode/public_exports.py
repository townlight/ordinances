"""Records-ready public export helpers for CivicCode Milestone 13."""

from __future__ import annotations

from html import escape
from typing import Any


EXPORT_VERSION = "civiccode.records_ready.v1"


def build_records_ready_export(
    *,
    lookup: dict[str, Any],
    citation_payload: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    """Build a CivicAccess-ready export shape without depending on CivicAccess runtime."""
    section = lookup["section"]
    version = lookup["version"]
    citation = citation_payload["citation"]
    heading = f"{section['section_number']} - {section['section_heading']}"
    return {
        "export_version": EXPORT_VERSION,
        "document_type": "municipal_code_section",
        "title": heading,
        "canonical_url": citation["canonical_url"],
        "section": {
            "section_id": section["section_id"],
            "section_number": section["section_number"],
            "section_heading": section["section_heading"],
            "authoritative_text": version["body"],
        },
        "version": {
            "version_id": version["version_id"],
            "version_label": version["version_label"],
            "effective_start": version["effective_start"],
            "effective_end": version["effective_end"],
            "is_current": version["is_current"],
            "status": version["status"],
        },
        "citation": citation,
        "source_provenance": {
            "source_id": source["source_id"],
            "source_name": source["name"],
            "publisher": source["publisher"],
            "source_url": source.get("source_url"),
            "file_reference": source.get("file_reference"),
            "retrieved_at": source.get("retrieved_at"),
            "retrieval_method": source.get("retrieval_method"),
            "checksum": source.get("checksum"),
            "source_owner": source.get("source_owner"),
            "is_official": source["is_official"],
        },
        "accessibility": {
            "language": "en",
            "required_headings": [
                "Authoritative code text",
                "Citation",
                "Source provenance",
                "Legal boundary",
            ],
            "labels": {
                "authoritative_text": "Authoritative code text",
                "citation_text": "Citation text",
                "source_provenance": "Source provenance",
            },
            "civicaccess_runtime_dependency": "not_shipped",
        },
        "legal_boundary": {
            "classification": "information_not_determination",
            "notice": "This export is public information, not legal advice.",
        },
        "code_answer_behavior": "not_available",
    }


def render_records_ready_export_page(export: dict[str, Any]) -> str:
    """Render an accessible HTML export page for public and staff verification."""
    section = export["section"]
    version = export["version"]
    citation = export["citation"]
    source = export["source_provenance"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(export['title'])} - CivicCode export</title>
  <style>
    :root {{
      --ink: #152018;
      --paper: #fffaf0;
      --card: #ffffff;
      --line: #24382b;
      --accent: #8b4b1f;
      --focus: #005fcc;
    }}
    * {{ box-sizing: border-box; }}
    html {{ overflow-wrap: anywhere; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: linear-gradient(135deg, #fffaf0, #eef4e8);
      font-family: Georgia, "Times New Roman", serif;
      line-height: 1.6;
    }}
    p, dd, a {{ overflow-wrap: anywhere; }}
    a {{ color: #0b4f82; text-underline-offset: .18em; }}
    a:focus-visible {{
      outline: 4px solid var(--focus);
      outline-offset: 3px;
    }}
    .skip-link {{
      position: absolute;
      left: .75rem;
      top: .75rem;
      transform: translateY(-200%);
      background: var(--ink);
      color: white;
      padding: .65rem .9rem;
      z-index: 5;
    }}
    .skip-link:focus {{ transform: translateY(0); }}
    main {{
      width: min(960px, calc(100% - 2rem));
      margin-inline: auto;
      padding: 2rem 0 4rem;
    }}
    h1 {{ font-size: clamp(2.2rem, 6vw, 4.8rem); line-height: 1; }}
    h2 {{ color: var(--accent); }}
    section {{
      background: var(--card);
      border: 2px solid var(--line);
      border-radius: 1rem;
      padding: 1rem 1.25rem;
      margin: 1rem 0;
    }}
    dt {{ font-weight: 700; }}
    dd {{ margin: 0 0 .75rem; }}
    .boundary {{ background: #fff2dd; }}
    @media print {{
      .skip-link {{ display: none; }}
      body {{ background: white; }}
      section {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#content">Skip to export content</a>
  <main id="content">
    <p>CivicCode records-ready export</p>
    <h1>{escape(export['title'])}</h1>
    <section aria-labelledby="code-text-heading">
      <h2 id="code-text-heading">Authoritative code text</h2>
      <p>{escape(section['authoritative_text'])}</p>
      <dl aria-label="Section metadata">
        <dt>Section number</dt><dd>{escape(section['section_number'])}</dd>
        <dt>Version</dt><dd>{escape(version['version_label'])}</dd>
        <dt>Effective start</dt><dd>{escape(version['effective_start'])}</dd>
      </dl>
    </section>
    <section aria-labelledby="citation-heading">
      <h2 id="citation-heading">Citation</h2>
      <p>{escape(citation['citation_text'])}</p>
      <p><a href="{escape(citation['canonical_url'])}">Canonical public section URL</a></p>
    </section>
    <section aria-labelledby="source-heading">
      <h2 id="source-heading">Source provenance</h2>
      <dl aria-label="Source provenance">
        <dt>Source name</dt><dd>{escape(source['source_name'])}</dd>
        <dt>Publisher</dt><dd>{escape(source['publisher'])}</dd>
        <dt>Retrieval method</dt><dd>{escape(str(source['retrieval_method']))}</dd>
        <dt>Retrieved at</dt><dd>{escape(str(source['retrieved_at']))}</dd>
        <dt>Checksum</dt><dd>{escape(str(source['checksum']))}</dd>
      </dl>
    </section>
    <section class="boundary" aria-labelledby="boundary-heading">
      <h2 id="boundary-heading">Legal boundary</h2>
      <p>This export is public information, not legal advice. Contact the City
      Clerk for the official record or the City Attorney for legal advice.</p>
    </section>
  </main>
</body>
</html>"""
