"""Server-rendered public lookup pages for CivicCode residents."""

from __future__ import annotations

from html import escape
from typing import Any
from urllib.parse import quote, urlencode

from civiccode.qa_harness import looks_like_legal_determination


LEGAL_ADVICE_MARKERS = (
    "should i sue",
    "do i need a lawyer",
    "legal advice",
    "liable",
    "liability",
    "defend me",
    "represent me",
)


def is_legal_advice_query(query: str) -> bool:
    normalized = query.strip().lower()
    return any(marker in normalized for marker in LEGAL_ADVICE_MARKERS) or looks_like_legal_determination(
        query
    )


def render_home_page(popular_questions: list[dict[str, Any]] | None = None) -> str:
    popular_questions = popular_questions or []
    return _page(
        "Read the municipal code",
        f"""
        <section class="hero" aria-labelledby="lookup-title">
          <p class="eyebrow">CivicCode public lookup</p>
          <h1 id="lookup-title">Read code with citations, not guesses.</h1>
          <p class="lede">Search adopted municipal code text, open a section, and see
          citation-ready source details. No live LLM calls run in this milestone.</p>
        </section>
        <section class="lookup-panel" aria-labelledby="search-heading">
          <h2 id="search-heading">Find a section</h2>
          <form action="/civiccode/search" method="get" role="search">
            <label for="q">Search by section number or resident phrase</label>
            <div class="search-row">
              <input id="q" name="q" type="search" autocomplete="off"
                placeholder="Example: backyard chickens or 6.12.040" />
              <button type="submit">Search code</button>
            </div>
          </form>
          <div class="state-card" aria-live="polite">
            <strong>Ready for a search.</strong>
            Results load after you submit the form. Empty and error states explain
            how to fix the request.
          </div>
        </section>
        <section class="lookup-panel" aria-labelledby="answer-heading">
          <h2 id="answer-heading">Ask about one section</h2>
          <form action="/civiccode/answer" method="get">
            <label for="question">Question</label>
            <div class="search-row">
              <input id="question" name="q" type="search" autocomplete="off"
                placeholder="Example: What does section 6.12.040 say?" />
            </div>
            <label for="section-number">Section number</label>
            <div class="search-row">
              <input id="section-number" name="section_number" type="search"
                autocomplete="off" placeholder="6.12.040" />
              <button type="submit">Get cited answer</button>
            </div>
          </form>
        </section>
        {_popular_questions_block(popular_questions)}
        <section class="notice-grid" aria-label="Lookup boundaries">
          <article>
            <h2>What this does</h2>
            <p>Shows authoritative adopted code text, citations, approved
            plain-language summaries, and pending codification warnings.</p>
          </article>
          <article>
            <h2>What this does not do</h2>
            <p>CivicCode does not provide legal advice. If the code answer
            affects rights, penalties, deadlines, or enforcement, contact the
            City Clerk or City Attorney.</p>
          </article>
        </section>
        """,
    )


def render_search_page(query: str, results: list[dict[str, Any]]) -> str:
    if is_legal_advice_query(query):
        return render_refusal_page(query)
    if not results:
        return _page(
            f"No results for {query}",
            f"""
            {_search_form(query)}
            <section class="state-card warning" role="status" aria-live="polite">
              <h1>No matching code sections yet.</h1>
              <p>Try a section number like <strong>6.12.040</strong>, use fewer
              words, or contact the City Clerk if you need help locating the
              official code section.</p>
              <p class="code-chip">code_answer_behavior: not_available</p>
            </section>
            """,
        )

    items = "\n".join(_search_result_item(result) for result in results)
    return _page(
        f"Search results for {query}",
        f"""
        {_search_form(query)}
        <section class="results" aria-labelledby="results-heading">
          <p class="eyebrow">Citation-ready results</p>
          <h1 id="results-heading">Search results for {escape(query)}</h1>
          <p class="lede">Open a section to see authoritative code text, source
          provenance, citation details, and any pending codification warnings.</p>
          <ol class="result-list">{items}</ol>
        </section>
        """,
    )


def render_answer_page(query: str, payload: dict[str, Any]) -> str:
    if payload.get("status") != "ok":
        return _page(
            "Code answer unavailable",
            f"""
            {_answer_form(query, "")}
            <section class="state-card warning" role="alert">
              <p class="eyebrow">{escape(payload.get("refusal_type", "answer refusal"))}</p>
              <h1>CivicCode cannot answer that question.</h1>
              <p>{escape(payload.get("reason", "No cited adopted code section could ground the answer."))}</p>
              <p>{escape(payload.get("fix", "Ask with an exact adopted section number."))}</p>
              <p class="code-chip">code_answer_behavior: not_available</p>
            </section>
            """,
        )
    citation = payload["citations"][0]
    return _page(
        "Cited code answer",
        f"""
        {_answer_form(query, payload.get("matched_section_number", ""))}
        <article class="section-detail" aria-labelledby="answer-title">
          <p class="eyebrow">Cited code answer</p>
          <h1 id="answer-title">Cited code answer</h1>
          <section class="code-card" aria-labelledby="answer-heading">
            <h2 id="answer-heading">Answer</h2>
            <p>{escape(payload["answer"])}</p>
          </section>
          <section class="citation-card" aria-labelledby="answer-citation-heading">
            <h2 id="answer-citation-heading">Citation</h2>
            <p>{escape(citation["citation_text"])}</p>
            <p><a href="/civiccode/sections/{escape(citation['section_number'])}">
            Open authoritative section text.</a></p>
          </section>
          <section class="contact-card" aria-labelledby="answer-boundary-heading">
            <h2 id="answer-boundary-heading">Review boundary</h2>
            <p>This is not a legal determination. City staff remain responsible
            for official interpretations, enforcement decisions, and legal advice.</p>
          </section>
        </article>
        """,
    )


def render_section_page(
    lookup: dict[str, Any],
    citation_payload: dict[str, Any],
    summaries: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    related_items: list[dict[str, Any]] | None = None,
) -> str:
    section = lookup["section"]
    version = lookup["version"]
    heading = f"{section['section_number']} - {section['section_heading']}"
    citation_html = _citation_block(citation_payload)
    summary_html = _summary_block(summaries)
    warning_html = _warning_block(warnings)
    related_html = _related_materials_block(related_items or [])
    return _page(
        heading,
        f"""
        <nav class="breadcrumb" aria-label="Breadcrumb">
          <a href="/civiccode">CivicCode</a>
          <span aria-hidden="true">/</span>
          <a href="/civiccode/search?{urlencode({'q': section['section_number']})}">Search</a>
        </nav>
        <article class="section-detail" aria-labelledby="section-title">
          <p class="eyebrow">Authoritative code text</p>
          <h1 id="section-title">{escape(heading)}</h1>
          <p class="version-line">Version {escape(version['version_label'])},
          effective {escape(str(version['effective_start']))}</p>
          {warning_html}
          <section class="code-card" aria-labelledby="code-text-heading">
            <h2 id="code-text-heading">Authoritative code text</h2>
            <p>{escape(version['body'])}</p>
          </section>
          {summary_html}
          {citation_html}
          {related_html}
          <section class="citation-card" aria-labelledby="export-heading">
            <h2 id="export-heading">Records-ready export</h2>
            <p><a href="/civiccode/sections/{escape(section['section_number'])}/export">
            Open an accessible export with citation and source provenance.</a></p>
          </section>
          <section class="contact-card" aria-labelledby="contact-heading">
            <h2 id="contact-heading">Need an official interpretation?</h2>
            <p>This page helps you read adopted code. It is not a legal
            determination. Contact the City Clerk for the official record or the
            City Attorney for legal advice.</p>
          </section>
        </article>
        """,
    )


def render_error_page(title: str, message: str, fix: str, *, status_label: str) -> str:
    return _page(
        title,
        f"""
        <section class="state-card warning" role="alert">
          <p class="eyebrow">{escape(status_label)}</p>
          <h1>{escape(message)}</h1>
          <p>{escape(fix)}</p>
          <p class="code-chip">code_answer_behavior: not_available</p>
          <a class="button-link" href="/civiccode">Start a new lookup</a>
        </section>
        """,
    )


def render_refusal_page(query: str) -> str:
    return _page(
        "Legal advice unavailable",
        f"""
        {_search_form(query)}
        <section class="state-card warning" role="alert">
          <p class="eyebrow">Legal-advice refusal</p>
          <h1>CivicCode cannot provide legal advice.</h1>
          <p>Ask for the code section or contact the City Attorney for legal
          advice. CivicCode can show adopted code text and citations, but it
          cannot tell you what legal action to take.</p>
          <p class="code-chip">code_answer_behavior: not_available</p>
        </section>
        """,
    )


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="icon" href="data:," />
  <title>{escape(title)} - CivicCode</title>
  <style>
    :root {{
      --ink: #1b261f;
      --paper: #f6f0e6;
      --card: #fffaf1;
      --line: #22382b;
      --moss: #496b50;
      --marigold: #d68c17;
      --clay: #9e4c32;
      --focus: #005fcc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(214, 140, 23, .26), transparent 34rem),
        linear-gradient(135deg, #f6f0e6 0%, #efe3d0 55%, #e4ecd9 100%);
      font-family: Georgia, "Times New Roman", serif;
      line-height: 1.55;
    }}
    a {{ color: #123f73; text-underline-offset: .18em; }}
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
      padding: 1.25rem 0;
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      align-items: center;
      border-bottom: 3px double var(--line);
    }}
    .brand {{ font-weight: 800; letter-spacing: .06em; text-transform: uppercase; }}
    main {{ padding: 2rem 0 4rem; }}
    h1, h2 {{ line-height: 1.05; }}
    h1 {{ font-size: clamp(2.4rem, 7vw, 5.6rem); margin: .25rem 0 1rem; max-width: 11ch; }}
    h2 {{ font-size: clamp(1.45rem, 3vw, 2.1rem); }}
    .eyebrow {{
      font-family: "Courier New", monospace;
      font-size: .8rem;
      letter-spacing: .14em;
      text-transform: uppercase;
      color: var(--clay);
      font-weight: 700;
    }}
    .lede {{ font-size: clamp(1.15rem, 2vw, 1.45rem); max-width: 62rem; }}
    .lookup-panel, .state-card, .code-card, .contact-card, .citation-card, .summary-card, .discovery-card, .result-list li {{
      background: rgba(255, 250, 241, .88);
      border: 2px solid var(--line);
      border-radius: 1.2rem;
      box-shadow: .5rem .5rem 0 rgba(34, 56, 43, .18);
      padding: clamp(1rem, 2vw, 1.5rem);
      margin: 1rem 0;
    }}
    .search-row {{ display: flex; gap: .8rem; flex-wrap: wrap; margin-top: .5rem; }}
    input {{
      flex: 1 1 18rem;
      min-height: 3rem;
      border: 2px solid var(--line);
      border-radius: .8rem;
      padding: .75rem 1rem;
      font: inherit;
      background: white;
    }}
    button, .button-link {{
      border: 2px solid var(--ink);
      border-radius: 999px;
      padding: .8rem 1.1rem;
      background: var(--marigold);
      color: #111;
      font-weight: 800;
      text-decoration: none;
      display: inline-block;
    }}
    .notice-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
      gap: 1rem;
    }}
    .result-list {{ padding-left: 1.2rem; }}
    .discovery-list {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
      gap: 1rem;
      padding: 0;
      list-style: none;
    }}
    .result-meta, .version-line, .code-chip {{
      font-family: "Courier New", monospace;
      font-size: .92rem;
    }}
    .warning {{
      border-color: var(--clay);
      background: #fff3df;
    }}
    .breadcrumb {{
      display: flex;
      gap: .5rem;
      align-items: center;
      margin-bottom: 1rem;
      font-family: "Courier New", monospace;
    }}
    footer {{
      padding: 2rem 0 3rem;
      border-top: 3px double var(--line);
      font-family: "Courier New", monospace;
      font-size: .9rem;
    }}
    @media (max-width: 680px) {{
      header {{ align-items: flex-start; flex-direction: column; }}
      h1 {{ max-width: 100%; }}
      .search-row {{ display: block; }}
      button {{ width: 100%; margin-top: .75rem; }}
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#content">Skip to content</a>
  <header>
    <a class="brand" href="/civiccode">CivicCode</a>
    <span>Resident code lookup - public beta foundation</span>
  </header>
  <main id="content">
    {body}
  </main>
  <footer>
    CivicCode shows adopted code text and citations. It does not provide legal
    advice or replace the official municipal record.
  </footer>
</body>
</html>"""


def _search_form(query: str) -> str:
    return f"""
    <section class="lookup-panel" aria-labelledby="search-heading">
      <h2 id="search-heading">Search again</h2>
      <form action="/civiccode/search" method="get" role="search">
        <label for="q">Search by section number or resident phrase</label>
        <div class="search-row">
          <input id="q" name="q" type="search" value="{escape(query)}" />
          <button type="submit">Search code</button>
        </div>
      </form>
    </section>
    """


def _answer_form(query: str, section_number: str) -> str:
    return f"""
    <section class="lookup-panel" aria-labelledby="answer-form-heading">
      <h2 id="answer-form-heading">Ask about one section</h2>
      <form action="/civiccode/answer" method="get">
        <label for="question">Question</label>
        <div class="search-row">
          <input id="question" name="q" type="search" autocomplete="off"
            value="{escape(query)}" />
        </div>
        <label for="section-number">Section number</label>
        <div class="search-row">
          <input id="section-number" name="section_number" type="search"
            value="{escape(section_number)}" />
          <button type="submit">Get cited answer</button>
        </div>
      </form>
    </section>
    """


def _search_result_item(result: dict[str, Any]) -> str:
    section_number = result.get("section_number") or result.get("source_section_number")
    heading = result.get("section_heading") or result.get("label") or "Related material"
    href = f"/civiccode/sections/{quote(str(section_number))}"
    result_type = str(result["result_type"]).replace("_", " ")
    description = result.get("snippet") or (
        "Open the cited section for authoritative adopted code text and source context."
        if result.get("result_type") == "code_section"
        else "This staff-approved related material is a navigation aid, not a legal determination."
    )
    return f"""
    <li>
      <h2><a href="{href}">{escape(str(section_number))} - {escape(str(heading))}</a></h2>
      <p>{escape(description)}</p>
      <p class="result-meta">Citation-ready - {escape(result_type)}</p>
    </li>
    """


def _popular_questions_block(popular_questions: list[dict[str, Any]]) -> str:
    if not popular_questions:
        return """
        <section class="discovery-card" aria-labelledby="popular-heading">
          <p class="eyebrow">Resident discovery</p>
          <h2 id="popular-heading">Popular questions</h2>
          <p>No staff-approved popular questions are published yet. Use search
          above or contact the City Clerk if you need help finding the official
          code section.</p>
          <p class="code-chip">code_answer_behavior: navigation_aid</p>
        </section>
        """
    items = "\n".join(_popular_question_item(question) for question in popular_questions)
    return f"""
    <section class="discovery-card" aria-labelledby="popular-heading">
      <p class="eyebrow">Resident discovery</p>
      <h2 id="popular-heading">Popular questions</h2>
      <p>These are staff-approved navigation aids that link to cited adopted
      sections. They are not legal determinations.</p>
      <ul class="discovery-list">{items}</ul>
    </section>
    """


def _popular_question_item(question: dict[str, Any]) -> str:
    return f"""
    <li class="state-card">
      <h3><a href="{escape(question['section_url'])}">{escape(question['question_text'])}</a></h3>
      <p>{escape(question['answer_excerpt'])}</p>
      <p class="result-meta">Cites Section {escape(question['section_number'])} -
      navigation aid, not a legal determination.</p>
    </li>
    """


def _related_materials_block(related_items: list[dict[str, Any]]) -> str:
    if not related_items:
        return """
        <section class="discovery-card" aria-labelledby="related-heading">
          <h2 id="related-heading">Related materials</h2>
          <p>No approved related materials are attached to this section yet.
          Read the authoritative code text above or contact the City Clerk for
          help locating related records.</p>
          <p class="code-chip">code_answer_behavior: navigation_aid</p>
        </section>
        """
    items = "\n".join(_related_material_item(item) for item in related_items)
    return f"""
    <section class="discovery-card" aria-labelledby="related-heading">
      <h2 id="related-heading">Related materials</h2>
      <p>These links are explicit cross-references for navigation only. They do
      not include staff notes and are not legal determinations.</p>
      <ul class="discovery-list">{items}</ul>
    </section>
    """


def _related_material_item(item: dict[str, Any]) -> str:
    return f"""
    <li class="state-card">
      <h3>{escape(item['label'])}</h3>
      <p class="result-meta">{escape(item['result_type'].replace('_', ' '))} -
      related to Section {escape(item['source_section_number'])}</p>
      <p>{escape(item['public_label'])}</p>
    </li>
    """


def _citation_block(payload: dict[str, Any]) -> str:
    if payload.get("status") != "ok":
        return f"""
        <section class="citation-card warning" aria-labelledby="citation-heading">
          <h2 id="citation-heading">Citation unavailable</h2>
          <p>{escape(payload.get('reason', 'Citation could not be built.'))}</p>
          <p>{escape(payload.get('fix', 'Refresh the source and try again.'))}</p>
          <p class="code-chip">code_answer_behavior: not_available</p>
        </section>
        """
    citation = payload["citation"]
    return f"""
    <section class="citation-card" aria-labelledby="citation-heading">
      <h2 id="citation-heading">Citation</h2>
      <p>{escape(citation['citation_text'])}</p>
      <p class="result-meta">Source: {escape(citation['source_name'])} -
      section_id {escape(citation['section_id'])} - version_id {escape(citation['version_id'])}</p>
    </section>
    """


def _summary_block(summaries: list[dict[str, Any]]) -> str:
    if not summaries:
        return """
        <section class="summary-card" aria-labelledby="summary-heading">
          <h2 id="summary-heading">Plain-language summary</h2>
          <p>No approved summary is available yet. Read the authoritative code
          text above or contact the City Clerk for help locating the official record.</p>
        </section>
        """
    items = "\n".join(
        f"<li>{escape(summary['summary_text'])}</li>" for summary in summaries
    )
    return f"""
    <section class="summary-card" aria-labelledby="summary-heading">
      <h2 id="summary-heading">Plain-language summary</h2>
      <p>These summaries are staff-approved reading aids and not a legal determination.</p>
      <ul>{items}</ul>
    </section>
    """


def _warning_block(warnings: list[dict[str, Any]]) -> str:
    if not warnings:
        return ""
    items = "\n".join(
        f"""
        <li>
          <strong>{escape(warning['handoff_state'].replace('_', ' '))}:</strong>
          {escape(warning['message'])}
          <span>{escape(warning['fix'])}</span>
        </li>
        """
        for warning in warnings
    )
    return f"""
    <section class="state-card warning" role="status" aria-labelledby="handoff-heading">
      <h2 id="handoff-heading">Pending codification warning</h2>
      <p>Pending ordinance language is not adopted law until staff codifies it.</p>
      <ul>{items}</ul>
    </section>
    """
