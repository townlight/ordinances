"""Server-rendered staff import ledger workspace."""

from __future__ import annotations

from html import escape
from typing import Any


def render_staff_import_required_page() -> str:
    return _page(
        "Staff import ledger requires staff access",
        """
        <section class="state-card warning" role="alert">
          <p class="eyebrow">Staff access required</p>
          <h1>Staff import ledger requires staff access.</h1>
          <p>Open this page through the trusted staff shell or proxy that sends
          <code>X-CivicCode-Role: staff</code> and <code>X-CivicCode-Actor</code>.
          Import failures, local file names, and source provenance are staff-only
          operational records.</p>
          <p class="fix-path">Fix: sign in through the staff shell, then reopen
          <code>/staff/imports</code>. Local testers can send both staff headers
          from the supervised test client or reverse proxy.</p>
        </section>
        """,
    )


def render_staff_import_ledger(payload: dict[str, Any], *, actor: str) -> str:
    jobs = payload["jobs"]
    if not jobs:
        ledger_html = """
        <section class="state-card" role="status" aria-live="polite">
          <p class="eyebrow">Empty import ledger</p>
          <h1>No local import jobs have run yet.</h1>
          <p>Staff cannot verify imported code provenance until a CSV bundle,
          official HTML extract, or other local import connector creates an
          import job record.</p>
          <p class="fix-path">Fix: post a vetted local bundle to
          <code>/api/v1/civiccode/staff/imports/local-bundle</code>, then reopen
          this ledger to verify job status, failure copy, and provenance.</p>
        </section>
        """
    else:
        job_html = "".join(_job_card(job) for job in jobs) or _empty_jobs_note()
        ledger_html = f"""
        <section class="ledger" aria-labelledby="jobs-heading">
          <h2 id="jobs-heading">Import jobs</h2>
          {job_html}
        </section>
        """
    return _page(
        "Staff import ledger",
        f"""
        <section class="hero" aria-labelledby="workspace-title">
          <p class="eyebrow">CivicCode staff workspace</p>
          <h1 id="workspace-title">Import provenance ledger</h1>
        <p class="lede">This ledger exposes local import jobs, failure recovery
          paths, and source provenance so staff can verify what entered
          CivicCode before residents rely on the text.</p>
          <p class="actor-chip">Signed in as {escape(actor)}</p>
        </section>
        {_overview(payload)}
        {ledger_html}
        """,
    )


def _overview(payload: dict[str, Any]) -> str:
    counts = payload["counts"]
    return f"""
    <section class="overview" aria-labelledby="overview-heading">
      <h2 id="overview-heading">Import snapshot</h2>
      <div class="metric-grid">
        <article><strong>{counts["total_jobs"]}</strong><span>total jobs</span></article>
        <article><strong>{counts["completed_jobs"]}</strong><span>completed</span></article>
        <article><strong>{counts["failed_jobs"]}</strong><span>failed</span></article>
        <article><strong>{counts["retried_jobs"]}</strong><span>retries</span></article>
      </div>
      <p class="source-line">Import connector types: {escape(payload["connector_types"])}.</p>
    </section>
    """


def _job_card(item: dict[str, Any]) -> str:
    job = item["job"]
    report = item["report"]
    source = item.get("source")
    status = str(job["status"])
    counts = job.get("counts") or {}
    provenance = job.get("provenance") or {}
    count_html = "".join(
        f"<li><strong>{escape(key.replace('_', ' '))}:</strong> {escape(str(value))}</li>"
        for key, value in counts.items()
        if value
    ) or "<li>No records were created or reused.</li>"
    source_name = (
        source["name"]
        if source
        else provenance.get("source_name") or job.get("source_id") or "No source recorded"
    )
    failure = _failure_state(job)
    return f"""
    <article class="job-card status-{escape(status)}">
      <div class="job-head">
        <div>
          <p class="eyebrow">{escape(status)}</p>
          <h3>{escape(job["job_id"])}</h3>
        </div>
        <span class="connector-pill">{escape(job["connector_type"])}</span>
      </div>
      <dl>
        <dt>Source</dt><dd>{escape(str(source_name))}</dd>
        <dt>Actor</dt><dd>{escape(str(job["actor"]))}</dd>
        <dt>Created</dt><dd>{escape(str(job["created_at"]))}</dd>
        <dt>Completed</dt><dd>{escape(str(job.get("completed_at") or "Not completed"))}</dd>
        <dt>Retry of</dt><dd>{escape(str(job.get("retry_of") or "Original import"))}</dd>
        <dt>Fixture</dt><dd>{escape(str(provenance.get("fixture_name") or "Not recorded"))}</dd>
        <dt>Retrieval</dt><dd>{escape(str(report.get("retrieval_method") or "Not recorded"))}</dd>
        <dt>Checksum</dt><dd>{escape(str(report.get("fixture_checksum") or "Not recorded"))}</dd>
      </dl>
      <ul class="count-list">{count_html}</ul>
      {failure}
      <p class="fix-path">Fix: open
      <code>/api/v1/civiccode/staff/imports/{escape(job["job_id"])}/provenance</code>
      to verify source provenance. For completed jobs, open the tree endpoint;
      for failed jobs, correct the bundle and retry the failed job endpoint.</p>
    </article>
    """


def _failure_state(job: dict[str, Any]) -> str:
    failure = job.get("failure")
    if not failure:
        return """
        <section class="source-ok" role="status">
          <strong>Import completed or has no recorded failure.</strong>
          <span>Staff can inspect provenance and the imported tree before
          treating the text as ready for lifecycle review.</span>
        </section>
        """
    return f"""
    <section class="source-warning" role="alert">
      <h4>Import failure</h4>
      <p><strong>{escape(str(failure.get("message") or "Import failed."))}</strong></p>
      <p>Fix: {escape(str(failure.get("fix") or "Review the bundle, correct the data, and retry the job."))}</p>
    </section>
    """


def _empty_jobs_note() -> str:
    return """
    <section class="state-card" role="status">
      <p>No import jobs are recorded yet.</p>
      <p class="fix-path">Fix: run a local bundle import or codifier sync local
      payload before reviewing imported records here.</p>
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
        radial-gradient(circle at 12% 4%, rgba(191, 129, 36, .22), transparent 28rem),
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
    .actor-chip, .source-line, .connector-pill {{
      display: inline-block;
      max-width: 100%;
      background: var(--card);
      border: 2px solid var(--line);
      border-radius: 999px;
      padding: .55rem .8rem;
      font-family: "Courier New", monospace;
      font-size: .92rem;
      overflow-wrap: anywhere;
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
    .overview, .state-card, .job-card {{
      background: rgba(255, 250, 240, .94);
      border: 2px solid var(--line);
      border-radius: 1.2rem;
      box-shadow: .45rem .45rem 0 rgba(23, 35, 29, .16);
      margin: 1rem 0;
      padding: clamp(1rem, 2vw, 1.5rem);
    }}
    .warning, .source-warning, .status-failed {{
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
    .job-head {{
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      align-items: start;
    }}
    dl {{
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: .35rem .9rem;
    }}
    dt {{ color: var(--muted); font-weight: 700; }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    .count-list {{
      display: flex;
      flex-wrap: wrap;
      gap: .5rem;
      list-style: none;
      padding: 0;
    }}
    .count-list li {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: .35rem .65rem;
      background: white;
    }}
    .source-ok, .source-warning {{
      border: 2px solid;
      border-radius: .9rem;
      margin: 1rem 0;
      padding: .8rem;
    }}
    .source-ok {{ border-color: var(--green); background: #edf8ef; }}
    code {{
      background: #f1dec2;
      border-radius: .25rem;
      padding: .1rem .25rem;
      overflow-wrap: anywhere;
    }}
    footer {{
      border-top: 3px double var(--line);
      padding: 2rem 0 3rem;
      color: var(--muted);
      font-family: "Courier New", monospace;
    }}
    @media (max-width: 760px) {{
      header, .job-head {{ flex-direction: column; }}
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
  <a class="skip-link" href="#content">Skip to staff import ledger</a>
  <header>
    <a class="brand" href="/staff/imports">CivicCode</a>
    <span>Staff import ledger</span>
  </header>
  <main id="content">
    {body}
  </main>
  <footer>
    Staff import review keeps local fixtures, retry state, and provenance
    visible before imported code reaches resident workflows.
  </footer>
</body>
</html>"""
