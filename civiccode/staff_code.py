"""Server-rendered staff code lifecycle workspace."""

from __future__ import annotations

from html import escape
from typing import Any


def render_staff_code_required_page() -> str:
    return _page(
        "Staff code workspace requires staff access",
        """
        <section class="state-card warning" role="alert">
          <p class="eyebrow">Staff access required</p>
          <h1>Staff code workspace requires staff access.</h1>
          <p>Open this page through the trusted staff shell or proxy that sends
          <code>X-CivicCode-Role: staff</code> and <code>X-CivicCode-Actor</code>.
          Public visitors should use the resident code lookup instead.</p>
          <p class="fix-path">Fix: sign in through the staff shell, then reopen
          <code>/staff/code</code>. Local testers can send both staff headers
          from the supervised test client or reverse proxy.</p>
        </section>
        """,
    )


def render_staff_code_workspace(payload: dict[str, Any], *, actor: str) -> str:
    sections = payload["sections"]
    if not sections:
        workspace = """
        <section class="state-card" role="status" aria-live="polite">
          <p class="eyebrow">Empty code workspace</p>
          <h1>No code sections are ready for staff review yet.</h1>
          <p>Staff need at least one active official source and one section with
          adopted text before resident lookup, citation exports, and summaries
          can be trusted.</p>
          <p class="fix-path">Fix: register an active official source, import a
          local code bundle, or create the title, chapter, section, and adopted
          section version through the staff API.</p>
        </section>
        """
    else:
        workspace = "".join(_section_card(section) for section in sections)
    return _page(
        "Staff code lifecycle workspace",
        f"""
        <section class="hero" aria-labelledby="workspace-title">
          <p class="eyebrow">CivicCode staff workspace</p>
          <h1 id="workspace-title">Code lifecycle command center</h1>
          <p class="lede">This workspace shows whether code text is safe to
          publish, whether summaries are approved, and whether CivicClerk
          ordinance handoffs require codification review before residents rely
          on the page.</p>
          <p class="actor-chip">Signed in as {escape(actor)}</p>
        </section>
        {_overview(payload)}
        <section class="sections" aria-labelledby="sections-heading">
          <h2 id="sections-heading">Sections needing staff attention</h2>
          {workspace}
        </section>
        """,
    )


def _overview(payload: dict[str, Any]) -> str:
    source = payload["source_status"]
    counts = payload["counts"]
    blockers = payload["blockers"]
    blocker_html = (
        "".join(f"<li>{escape(blocker)}</li>" for blocker in blockers)
        if blockers
        else "<li>No publication blockers detected in the loaded workspace.</li>"
    )
    return f"""
    <section class="overview" aria-labelledby="overview-heading">
      <h2 id="overview-heading">Readiness snapshot</h2>
      <div class="metric-grid">
        <article><strong>{counts["sections"]}</strong><span>sections</span></article>
        <article><strong>{counts["current_versions"]}</strong><span>current adopted versions</span></article>
        <article><strong>{counts["draft_summaries"]}</strong><span>draft summaries</span></article>
        <article><strong>{counts["handoff_warnings"]}</strong><span>handoff warnings</span></article>
      </div>
      <p class="source-line">Sources: {source["active"]} active, {source["stale"]} stale, {source["failed"]} failed.</p>
      <section class="blockers" role="status" aria-live="polite">
        <h3>Safe-publication blockers</h3>
        <ul>{blocker_html}</ul>
      </section>
    </section>
    """


def _section_card(section: dict[str, Any]) -> str:
    version = section.get("current_version")
    version_label = "No current adopted version"
    version_status = "blocked"
    if version:
        version_label = f"{version['version_label']} effective {version['effective_start']}"
        version_status = str(version["status"])
    summary_html = _summary_list(section["summaries"])
    warning_html = _warning_list(section["handoff_warnings"])
    return f"""
    <article class="section-card status-{escape(version_status)}">
      <div class="section-head">
        <div>
          <p class="eyebrow">Section {escape(section["section_number"])}</p>
          <h3>{escape(section["section_heading"])}</h3>
        </div>
        <a href="{escape(section["public_url"])}">Open public page</a>
      </div>
      <dl>
        <dt>Current text</dt><dd>{escape(version_label)}</dd>
        <dt>Source</dt><dd>{escape(section.get("source_label") or "No source linked")}</dd>
        <dt>Staff notes</dt><dd>{section["staff_note_count"]}</dd>
      </dl>
      {summary_html}
      {warning_html}
      <p class="fix-path">{escape(section["next_action"])}</p>
    </article>
    """


def _summary_list(summaries: list[dict[str, Any]]) -> str:
    if not summaries:
        return """
        <section class="summary-state warning" role="status">
          <h4>No plain-language summary</h4>
          <p>Fix: draft a non-authoritative summary and approve it only after
          staff confirms it matches the adopted code text.</p>
        </section>
        """
    items = "".join(
        f"<li><strong>{escape(summary['status'])}</strong>: {escape(summary['summary_text'])}</li>"
        for summary in summaries
    )
    return f"""
    <section class="summary-state">
      <h4>Plain-language summaries</h4>
      <ul>{items}</ul>
    </section>
    """


def _warning_list(warnings: list[dict[str, Any]]) -> str:
    if not warnings:
        return """
        <section class="source-ok" role="status">
          <strong>No pending codification warning for this section.</strong>
        </section>
        """
    items = "".join(
        f"<li><strong>{escape(str(warning.get('ordinance_number')))}</strong>: "
        f"{escape(str(warning.get('message')))} Fix: {escape(str(warning.get('fix')))}</li>"
        for warning in warnings
    )
    return f"""
    <section class="source-warning" role="alert">
      <h4>Pending codification review</h4>
      <ul>{items}</ul>
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
      --ink: #17231d;
      --paper: #f6efe1;
      --card: #fffaf0;
      --line: #27392e;
      --muted: #5f6a62;
      --gold: #bf8124;
      --red: #97412f;
      --green: #2d684b;
      --focus: #005fcc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 14% 6%, rgba(191, 129, 36, .22), transparent 28rem),
        linear-gradient(135deg, var(--paper) 0%, #e7efdf 100%);
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
      width: min(1160px, calc(100% - 2rem));
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
      font-size: clamp(2.5rem, 7vw, 5.2rem);
      line-height: .95;
      margin: .2rem 0 1rem;
      max-width: 12ch;
    }}
    h2 {{ font-size: clamp(1.5rem, 3vw, 2.1rem); }}
    .eyebrow {{
      color: var(--red);
      font: 800 .78rem/1.2 "Courier New", monospace;
      letter-spacing: .14em;
      text-transform: uppercase;
    }}
    .lede {{ color: var(--muted); font-size: 1.18rem; max-width: 64rem; }}
    .actor-chip, .source-line {{
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
    .overview, .state-card, .section-card {{
      background: rgba(255, 250, 240, .94);
      border: 2px solid var(--line);
      border-radius: 1.2rem;
      box-shadow: .45rem .45rem 0 rgba(23, 35, 29, .16);
      margin: 1rem 0;
      padding: clamp(1rem, 2vw, 1.5rem);
    }}
    .warning, .source-warning {{
      border-color: var(--red);
      background: #fff0df;
    }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: .8rem;
    }}
    .metric-grid article {{
      border: 2px solid var(--line);
      border-radius: 1rem;
      padding: 1rem;
      background: white;
    }}
    .metric-grid strong {{ display: block; font-size: 2.4rem; line-height: 1; }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      gap: 1rem;
    }}
    dl {{
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: .35rem .9rem;
    }}
    dt {{ color: var(--muted); font-weight: 700; }}
    dd {{ margin: 0; }}
    .source-ok, .source-warning, .summary-state {{
      border: 2px solid;
      border-radius: .9rem;
      margin: 1rem 0;
      padding: .8rem;
    }}
    .source-ok, .summary-state {{ border-color: var(--green); background: #edf8ef; }}
    code {{ background: #f1dec2; border-radius: .25rem; padding: .1rem .25rem; }}
    footer {{
      border-top: 3px double var(--line);
      padding: 2rem 0 3rem;
      color: var(--muted);
      font-family: "Courier New", monospace;
    }}
    @media (max-width: 760px) {{
      header, .section-head {{ flex-direction: column; }}
      h1 {{ max-width: 100%; }}
      .metric-grid {{ grid-template-columns: 1fr 1fr; }}
      dl {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 460px) {{
      .metric-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#content">Skip to staff code workspace</a>
  <header>
    <a class="brand" href="/staff/code">CivicCode</a>
    <span>Staff code lifecycle</span>
  </header>
  <main id="content">
    {body}
  </main>
  <footer>
    Staff lifecycle review protects residents from stale code, unapproved
    summaries, and pending codification ambiguity.
  </footer>
</body>
</html>"""
