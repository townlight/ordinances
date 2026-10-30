"""Server-rendered staff source registry workspace."""

from __future__ import annotations

from html import escape
from typing import Any


def render_staff_source_required_page() -> str:
    return _page(
        "Staff source workspace requires staff access",
        """
        <section class="state-card warning" role="alert">
          <p class="eyebrow">Staff access required</p>
          <h1>Staff source workspace requires staff access.</h1>
          <p>Open this page through the trusted staff shell or proxy that sends
          <code>X-CivicCode-Role: staff</code> and <code>X-CivicCode-Actor</code>.
          Direct public browser access is blocked so staff-only source notes and
          failed-ingest details do not leak.</p>
          <p class="fix-path">Fix: sign in through the staff shell, then reload
          this page. If you are testing locally, send the staff headers from the
          supervised test client or reverse proxy.</p>
        </section>
        """,
    )


def render_staff_source_workspace(sources: list[dict[str, Any]], *, actor: str) -> str:
    if not sources:
        source_html = """
        <section class="state-card" role="status" aria-live="polite">
          <p class="eyebrow">Empty source registry</p>
          <h1>No code sources registered yet.</h1>
          <p>Register an official Municode, American Legal, Code Publishing, General Code,
          official XML/DOCX export, or municipal file-drop source
          before publishing adopted code text or citation-grounded answers.</p>
          <p class="fix-path">Fix: use the staff source API to create an active
          official source with publisher, source owner, retrieval method,
          retrieved timestamp, and URL or file reference.</p>
        </section>
        """
    else:
        source_html = "\n".join(_source_card(source) for source in sources)
    return _page(
        "Staff source registry",
        f"""
        <section class="hero" aria-labelledby="workspace-title">
          <p class="eyebrow">CivicCode staff workspace</p>
          <h1 id="workspace-title">Source of truth gate</h1>
          <p class="lede">Before residents see code answers, staff must know
          which official source is active, stale, failed, or superseded. Signed
          source provenance is boring in the best way: it keeps legal ambiguity
          from quietly becoming public text.</p>
          <p class="actor-chip">Signed in as {escape(actor)}</p>
        </section>
        <section class="rules" aria-labelledby="rules-heading">
          <h2 id="rules-heading">Publication rules</h2>
          <ul>
            <li>Active official sources need publisher, source owner, retrieval
            method, retrieved timestamp, and source URL or file reference.</li>
            <li>Stale and failed sources block new citation-grounded answers
            until staff refreshes or repairs them.</li>
            <li>Staff-only notes stay off public endpoints and public lookup pages.</li>
          </ul>
        </section>
        <section class="sources" aria-labelledby="sources-heading">
          <h2 id="sources-heading">Registered sources</h2>
          {source_html}
        </section>
        """,
    )


def _source_card(source: dict[str, Any]) -> str:
    status = str(source["status"])
    warning = _source_warning(source)
    flags = [
        ("Public-visible", source["public_visible"]),
        ("Search eligible", source["search_eligible"]),
        ("Official", source["is_official"]),
    ]
    flag_html = "".join(
        f"<li><strong>{escape(label)}:</strong> {'yes' if value else 'no'}</li>"
        for label, value in flags
    )
    notes = source.get("staff_notes") or "No staff notes recorded."
    return f"""
    <article class="source-card status-{escape(status)}">
      <div>
        <p class="eyebrow">{escape(status.replace('_', ' '))}</p>
        <h3>{escape(source['name'])}</h3>
        <p>{escape(source['publisher'])} - {escape(source['source_type'])}</p>
      </div>
      <dl>
        <dt>Source ID</dt><dd>{escape(source['source_id'])}</dd>
        <dt>Owner</dt><dd>{escape(str(source.get('source_owner') or 'Not recorded'))}</dd>
        <dt>Retrieval</dt><dd>{escape(str(source.get('retrieval_method') or 'Not recorded'))}</dd>
        <dt>Retrieved</dt><dd>{escape(str(source.get('retrieved_at') or 'Not recorded'))}</dd>
      </dl>
      <ul class="flag-list">{flag_html}</ul>
      {warning}
      <section class="staff-note" aria-label="Staff-only source note">
        <h4>Staff-only note</h4>
        <p>{escape(notes)}</p>
      </section>
    </article>
    """


def _source_warning(source: dict[str, Any]) -> str:
    warning = source.get("warning")
    fix = source.get("fix")
    if not warning and not fix:
        return """
        <section class="source-ok" role="status">
          <strong>Source usable.</strong>
          <span>This source can support public search and citation-grounded answers.</span>
        </section>
        """
    return f"""
    <section class="source-warning" role="alert">
      <strong>{escape(str(warning or 'Source needs staff review.'))}</strong>
      <span>{escape(str(fix or 'Review the source record and update its lifecycle state.'))}</span>
    </section>
    """


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)} - CivicCode</title>
  <style>
    :root {{
      --ink: #16241d;
      --paper: #f5efe2;
      --card: #fffaf1;
      --line: #263b31;
      --muted: #59675f;
      --gold: #ca8b22;
      --red: #98472f;
      --green: #2f6749;
      --focus: #005fcc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 10% 0%, rgba(202, 139, 34, .24), transparent 28rem),
        linear-gradient(135deg, var(--paper) 0%, #e8efdf 100%);
      font-family: Georgia, "Times New Roman", serif;
      line-height: 1.55;
    }}
    a:focus-visible, button:focus-visible, input:focus-visible {{
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
    header, main, footer {{
      width: min(1120px, calc(100% - 2rem));
      margin-inline: auto;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      padding: 1.2rem 0;
      border-bottom: 3px double var(--line);
    }}
    .brand {{
      color: var(--ink);
      font-weight: 900;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    main {{ padding: 2rem 0 4rem; }}
    h1 {{
      font-size: clamp(2.6rem, 7vw, 5.4rem);
      line-height: .95;
      margin: .2rem 0 1rem;
      max-width: 11ch;
    }}
    h2 {{ font-size: clamp(1.6rem, 3vw, 2.2rem); }}
    .eyebrow {{
      color: var(--red);
      font: 800 .78rem/1.2 "Courier New", monospace;
      letter-spacing: .14em;
      text-transform: uppercase;
    }}
    .lede {{ color: var(--muted); font-size: 1.2rem; max-width: 62rem; }}
    .actor-chip {{
      display: inline-block;
      background: var(--card);
      border: 2px solid var(--line);
      border-radius: 999px;
      padding: .55rem .8rem;
      font-family: "Courier New", monospace;
      font-size: .92rem;
    }}
    .fix-path {{
      display: block;
      max-width: 62rem;
      background: var(--card);
      border: 2px solid var(--line);
      border-radius: .5rem;
      padding: .75rem .9rem;
      font-family: "Courier New", monospace;
      font-size: .92rem;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }}
    .rules, .state-card, .source-card {{
      background: rgba(255, 250, 241, .92);
      border: 2px solid var(--line);
      border-radius: 1.2rem;
      box-shadow: .45rem .45rem 0 rgba(22, 36, 29, .16);
      margin: 1rem 0;
      padding: clamp(1rem, 2vw, 1.5rem);
    }}
    .warning, .source-warning {{
      border-color: var(--red);
      background: #fff0df;
    }}
    .source-ok, .source-warning {{
      display: grid;
      gap: .25rem;
      border: 2px solid;
      border-radius: .9rem;
      margin: 1rem 0;
      padding: .8rem;
    }}
    .source-ok {{
      border-color: var(--green);
      background: #edf8ef;
    }}
    dl {{
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: .35rem .9rem;
    }}
    dt {{ color: var(--muted); font-weight: 700; }}
    dd {{ margin: 0; }}
    .flag-list {{
      display: flex;
      flex-wrap: wrap;
      gap: .5rem;
      list-style: none;
      padding: 0;
    }}
    .flag-list li {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: .35rem .65rem;
      background: white;
    }}
    .staff-note {{
      border-left: 5px solid var(--gold);
      padding-left: 1rem;
    }}
    code {{ background: #f1dec2; border-radius: .25rem; padding: .1rem .25rem; }}
    footer {{
      border-top: 3px double var(--line);
      padding: 2rem 0 3rem;
      color: var(--muted);
      font-family: "Courier New", monospace;
    }}
    @media (max-width: 680px) {{
      header {{ flex-direction: column; }}
      h1 {{ max-width: 100%; }}
      dl {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#content">Skip to staff source registry</a>
  <header>
    <a class="brand" href="/staff/sources">CivicCode</a>
    <span>Staff source registry</span>
  </header>
  <main id="content">
    {body}
  </main>
  <footer>
    Staff source records control what code text can safely power public lookup,
    exports, and citation-grounded answers.
  </footer>
</body>
</html>"""
