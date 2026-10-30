"""Server-rendered staff codifier sync health workspace."""

from __future__ import annotations

from html import escape
from typing import Any


def render_staff_sync_required_page() -> str:
    return _page(
        "Staff sync health requires staff access",
        """
        <section class="state-card warning" role="alert">
          <p class="eyebrow">Staff access required</p>
          <h1>Staff sync health requires staff access.</h1>
          <p>Open this page through the trusted staff shell or proxy that sends
          <code>X-CivicCode-Role: staff</code> and <code>X-CivicCode-Actor</code>.
          Public visitors cannot view vendor sync readiness, host checks, or
          local payload run history.</p>
          <p class="fix-path">Fix: sign in through the staff shell, then reopen
          <code>/staff/sync</code>. Local testers can send both staff headers
          from the supervised test client or reverse proxy.</p>
        </section>
        """,
    )


def render_staff_sync_workspace(
    sources: list[dict[str, Any]],
    *,
    actor: str,
) -> str:
    if not sources:
        sync_html = """
        <section class="state-card" role="status" aria-live="polite">
          <p class="eyebrow">No synced codifier source</p>
          <h1>No codifier sync source is configured yet.</h1>
          <p>Staff can still import local file-drop bundles, but this page has
          no sync readiness, circuit-breaker, cursor, or local payload run state
          to review.</p>
          <p class="fix-path">Fix: register an active official Municode,
          American Legal, Code Publishing, or General Code source, then configure
          codifier sync readiness from the staff API before running a local
          payload import.</p>
        </section>
        """
    else:
        sync_html = "\n".join(_sync_source_card(source) for source in sources)
    return _page(
        "Staff codifier sync health",
        f"""
        <section class="hero" aria-labelledby="workspace-title">
          <p class="eyebrow">CivicCode staff workspace</p>
          <h1 id="workspace-title">Codifier sync health</h1>
          <p class="lede">This page shows staff whether codifier sync readiness
          is configured, whether the circuit breaker is healthy, and which local
          payload run last refreshed CivicCode. It does not call an external
          vendor or automatically codify ordinances.</p>
          <p class="actor-chip">Signed in as {escape(actor)}</p>
        </section>
        {_overview(sources)}
        <section class="sources" aria-labelledby="sources-heading">
          <h2 id="sources-heading">Configured sync sources</h2>
          {sync_html}
        </section>
        """,
    )


def _overview(sources: list[dict[str, Any]]) -> str:
    paused = sum(1 for source in sources if source["operator_status"].get("sync_paused"))
    unhealthy = sum(
        1
        for source in sources
        if source["operator_status"].get("health_status") not in {"healthy", "ready"}
    )
    with_payload = sum(1 for source in sources if source.get("last_import_job_id"))
    return f"""
    <section class="overview" aria-labelledby="overview-heading">
      <h2 id="overview-heading">Readiness snapshot</h2>
      <div class="metric-grid">
        <article><strong>{len(sources)}</strong><span>configured sources</span></article>
        <article><strong>{with_payload}</strong><span>with local payload runs</span></article>
        <article><strong>{paused}</strong><span>paused circuits</span></article>
        <article><strong>{unhealthy}</strong><span>needing staff review</span></article>
      </div>
    </section>
    """


def _sync_source_card(source: dict[str, Any]) -> str:
    operator = source["operator_status"]
    source_status = source["source_status"]
    health = str(operator.get("health_status") or "unknown")
    warning_class = " warning" if health not in {"healthy", "ready"} else ""
    return f"""
    <article class="source-card status-{escape(health)}{warning_class}">
      <div class="source-head">
        <div>
          <p class="eyebrow">{escape(source["connector"])}</p>
          <h3>{escape(source["source_name"])}</h3>
        </div>
        <a href="{escape(source["source_url"])}">Open configured source</a>
      </div>
      <dl>
        <dt>Source ID</dt><dd>{escape(source["source_id"])}</dd>
        <dt>Schedule</dt><dd>{escape(source["sync_schedule"])}</dd>
        <dt>Health</dt><dd>{escape(str(operator.get("health_status", "unknown")))}</dd>
        <dt>Next sync</dt><dd>{escape(str(source.get("next_sync_at") or "Not scheduled"))}</dd>
        <dt>Last successful sync</dt><dd>{escape(str(source.get("last_successful_sync_at") or "No successful local payload run"))}</dd>
        <dt>Last attempted sync</dt><dd>{escape(str(source.get("last_attempted_sync_at") or "No local payload run attempted"))}</dd>
        <dt>Last import job</dt><dd>{escape(str(source.get("last_import_job_id") or "No local payload import recorded"))}</dd>
      </dl>
      {_host_validation(source)}
      {_local_payload_state(source)}
      <section class="operator-state" role="status" aria-live="polite">
        <h4>Operator message</h4>
        <p>{escape(str(operator.get("message") or source_status.get("message") or "No sync status message recorded."))}</p>
        <p class="fix-path">Fix: {escape(str(operator.get("fix") or source_status.get("fix") or "Review this source and rerun a local payload import."))}</p>
      </section>
    </article>
    """


def _host_validation(source: dict[str, Any]) -> str:
    validation = source.get("host_validation") or {}
    return f"""
    <section class="host-state">
      <h4>Host validation</h4>
      <p><strong>{escape(str(validation.get("status") or "not recorded"))}</strong>:
      {escape(str(validation.get("message") or "Configure sync readiness to run SSRF-safe host validation."))}</p>
    </section>
    """


def _local_payload_state(source: dict[str, Any]) -> str:
    plans = source.get("delta_plan_history") or []
    if not plans:
        return """
        <section class="payload-state warning" role="status">
          <h4>No local payload run recorded</h4>
          <p>Fix: run the configured codifier source with an already fetched
          local payload so staff can verify import status, cursor planning, and
          replay history before residents rely on refreshed text.</p>
        </section>
        """
    latest = plans[-1]
    delta_label = "delta request planned" if latest.get("delta_enabled") else "full request planned"
    return f"""
    <section class="payload-state" role="status" aria-live="polite">
      <h4>Latest local payload run</h4>
      <dl>
        <dt>Import job</dt><dd>{escape(str(latest.get("import_job_id") or "Not recorded"))}</dd>
        <dt>Plan</dt><dd>{escape(delta_label)}</dd>
        <dt>Cursor</dt><dd>{escape(str(latest.get("cursor_param") or "No cursor parameter"))}</dd>
        <dt>Planned at</dt><dd>{escape(str(latest.get("planned_at") or "Not recorded"))}</dd>
      </dl>
      <p>{escape(str(latest.get("message") or "Local payload run recorded."))}</p>
      <p class="fix-path">Fix: {escape(str(latest.get("fix") or "If staff sees missed sections, run a full reconciliation import."))}</p>
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
      --paper: #f7efe1;
      --card: #fffaf0;
      --line: #26392f;
      --muted: #5b675f;
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
        radial-gradient(circle at 16% 4%, rgba(191, 129, 36, .2), transparent 28rem),
        linear-gradient(135deg, var(--paper) 0%, #e5efe0 100%);
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
    .overview, .state-card, .source-card {{
      background: rgba(255, 250, 240, .94);
      border: 2px solid var(--line);
      border-radius: 1.2rem;
      box-shadow: .45rem .45rem 0 rgba(23, 35, 29, .16);
      margin: 1rem 0;
      padding: clamp(1rem, 2vw, 1.5rem);
    }}
    .warning {{
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
    .source-head {{
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
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    .host-state, .operator-state, .payload-state {{
      border: 2px solid var(--green);
      border-radius: .9rem;
      margin: 1rem 0;
      padding: .8rem;
      background: #edf8ef;
    }}
    .payload-state.warning {{
      border-color: var(--red);
      background: #fff0df;
    }}
    code {{ background: #f1dec2; border-radius: .25rem; padding: .1rem .25rem; }}
    footer {{
      border-top: 3px double var(--line);
      padding: 2rem 0 3rem;
      color: var(--muted);
      font-family: "Courier New", monospace;
    }}
    @media (max-width: 760px) {{
      header, .source-head {{ flex-direction: column; }}
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
  <a class="skip-link" href="#content">Skip to staff sync health</a>
  <header>
    <a class="brand" href="/staff/sync">CivicCode</a>
    <span>Staff codifier sync</span>
  </header>
  <main id="content">
    {body}
  </main>
  <footer>
    Staff sync health shows readiness and local payload state. External vendor
    fetching remains outside this server-rendered workspace.
  </footer>
</body>
</html>"""
