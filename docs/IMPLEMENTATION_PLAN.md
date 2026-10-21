# CivicCode Implementation Plan

Status: Active execution plan  
Date: 2026-04-27  
Applies to: CivicCode v0.1.0 implementation after Milestone 0

This document breaks CivicCode into manageable implementation chunks. Each
chunk is meant to be one PR unless an audit forces a smaller split. The plan
keeps CivicCode legally cautious: exact citations first, legal advice never,
and no planned behavior promoted as shipped.

## Unified Spec Traceability

This plan is keyed directly to `CivicSuite/civicsuite/docs/CivicSuiteUnifiedSpec.md`
and cross-checked against the original catalog extract at
`docx-canonical-extracts/CivicSuiteAI_Module_Catalog_v1 (1).txt`.

- Section 4.4: documentation, QA, version, browser-QA, and shipped/planned
  truth are release gates.
- Section 5.1: runtime modules follow the CivicRecords AI backend pattern:
  FastAPI, PostgreSQL 17 with pgvector where needed, Redis 7.2, Celery/Celery
  Beat for background work, Alembic migrations, pinned CivicCore dependency,
  per-module schema/namespace, and future hash-chained audit logging.
- Section 5.2: frontend work must include React staff/public pages where
  appropriate, no color-only status indicators, visible focus states,
  keyboard-complete workflows, and actionable empty/error states.
- Section 5.3: policy-bearing prompts live in module-specific YAML, use
  CivicCore LLM/provider/template infrastructure, enforce citations, and ship
  with an eval harness.
- Section 5.4: search is permission-aware, public search never leaks
  staff-only content, and advice-like answers distinguish information from
  determination.
- Section 11: CivicCode owns authoritative municipal code storage, cited Q&A,
  plain-language explanations, CivicClerk ordinance handoff, amendment/version
  history, and section resolution for CivicZone/CivicLegal/CivicAccess/CivicComms.
- Section 12: CivicAccess is the future accessibility/plain-language layer;
  CivicCode must not bake in designs that prevent that integration.
- Section 13: CivicCode owns its public "Read code" surface but must remain
  compatible with a future shared resident portal shell.
- Section 19: CivicCode is the next lane before CivicZone runtime, and CivicZone
  starts only after CivicCode has a versioned source-of-code contract or an ADR
  accepts a temporary substitute.

## Catalog v1 Traceability

The catalog extract is older than the current umbrella specification in two
ways: it says MIT licensing and "26 modules across 6 tiers." CivicSuite's
current governing decisions supersede those with AGPL-3.0-only licensing and 26
modules across 7 tiers. The CivicCode product requirements from the catalog are
still preserved here:

- Import municipal code from codifier exports or official source material,
  including Municode, American Legal, Code Publishing, General Code, XML, DOCX,
  file drops, and official web scrape/export paths.
- Search across titles, chapters, sections, subsections, administrative
  regulations, resolutions, policies, and approved summaries.
- Answer resident questions such as "can I have chickens" only when the answer
  can cite exact code sections and link to the authoritative text.
- Support staff Q&A with richer context, cross-references, and prior approved
  interpretations while keeping staff-only material out of public answers.
- Provide section permalinks, version history, amendment tracking, and
  effective-date lookup.
- Track adopted ordinances from CivicClerk, mark affected code stale or pending
  codification, and detect likely conflicts when proposed or adopted language
  touches existing sections.
- Publish popular questions and related sections without implying legal advice.
- Generate plain-language summaries that are approved by staff before public
  display and remain ready for CivicAccess multilingual/accessibility workflows.
- Preserve the catalog's "not a codifier replacement" boundary: CivicCode helps
  residents and staff find and understand official code, but it does not replace
  the official codifier contract or make legal determinations.

## Operating Pattern

Every chunk follows the same loop:

1. Write failing tests first.
2. Implement the smallest code needed.
3. Update all affected docs and user-facing copy.
4. Run local verification.
5. Browser-QA every frontend/user-visible state when UI changes.
6. Run audit-lite.
7. Fix audit findings once, re-audit once, then push/merge only if clear.

Required gates for every PR:

- `bash scripts/verify-docs.sh`
- `python scripts/check-civiccore-placeholder-imports.py`
- project test suite once runtime tests exist
- browser QA evidence for every frontend-visible change

## v0.1.0 Chunk Map

| Chunk | PR Theme | Main Outcome | Frontend? | Release Risk |
|---|---|---|---|---|
| 1 | Runtime foundation | Installable package + FastAPI shell | No | Low |
| 2 | Database foundation | CivicCode schema + Alembic | No | High |
| 3 | Source registry | Official source metadata API | Optional | Medium |
| 4 | Section/version model | Titles, chapters, sections, versions | Durable v0.1.13 | High |
| 5 | Search + permalinks | Search and stable section URLs | Yes | Medium |
| 6 | Citation contract | Deterministic citation model and refusal rules | No | High |
| 7 | Q&A harness | Local-LLM provider wiring with no legal advice | Optional | High |
| 8 | Popular questions + related sections | Safe resident discovery helpers | Shipped v0.1.12 | Medium |
| 9 | Plain-language summaries | Staff-approved non-authoritative summaries | Yes | High |
| 10 | Staff workbench | Staff Q&A, notes, cross-references, interpretation history | Yes | High |
| 11 | CivicClerk handoff + conflict detection | Ordinance/adoption event intake and likely-code-conflict warnings | No | High |
| 12 | Resident portal/public lookup | Resident-facing "Read code" surface | Yes | High |
| 13 | Import and async hardening | Codifier/import fixtures, Redis/Celery recovery paths | Optional | High |
| 14 | Accessibility/export hardening | CivicAccess-ready publishing/export posture | Yes | High |
| 15 | Release | v0.1.0 packaging, docs, compatibility PR | Yes | High |

## Chunk 1 - Runtime Foundation

Goal: make CivicCode installable and runnable without shipping code-answer
behavior.

Work:

- Add `pyproject.toml` with package metadata and the published CivicCore release-wheel dependency.
- Add `civiccode/__init__.py` with `__version__ = "0.1.0.dev0"`.
- Add `civiccode/main.py` FastAPI app with `/` and `/health`.
- Add app settings surface for local-only runtime defaults.
- Establish route naming for the future module API under `/api/v1/civiccode`
  and document that frontend pages will mount under `/civiccode` in the shared
  CivicSuite shell when UI ships.
- Add tests for package import, version, root payload, health payload, and
  no accidental shipped-feature claims.
- Update README/manual/landing page from "scaffold only" to "runtime
  foundation" only after the runtime shell exists.

Explicit non-goals:

- No database models.
- No source registry.
- No LLM calls.
- No code answers.

Acceptance tests:

- `GET /` says runtime foundation and points to Chunk 2.
- `GET /health` returns package version and civiccore version.
- Tests assert the root endpoint says no code-answer behavior is available.

## Chunk 2 - Database Foundation

Goal: establish CivicCode's database namespace without duplicating CivicCore.

Work:

- Add Alembic config under `civiccode/migrations`.
- Run CivicCore migrations before CivicCode migrations.
- Add first migration for the schema/table foundation.
- Add real Postgres/pgvector migration smoke test.
- Add idempotency/re-run test.
- Add migration docs that explain the one-way dependency on CivicCore.

Initial table set:

- `civiccode.code_sources`
- `civiccode.code_titles`
- `civiccode.code_chapters`
- `civiccode.code_sections`
- `civiccode.section_versions`
- `civiccode.section_citations`
- `civiccode.interpretation_notes`
- `civiccode.plain_language_summaries`
- `civiccode.code_questions`
- `civiccode.ordinance_events`

Audit risks:

- Accidental local SQLAlchemy `Base`.
- CivicCore migration runner called inside active Alembic context.
- Schema-blind idempotency guards.

Acceptance tests:

- Real Postgres upgrade creates CivicCore version table, CivicCode version
  table, and all CivicCode tables.
- Running upgrade twice is safe.
- No local declarative `Base` exists.

## Chunk 3 - Official Source Registry

Goal: register official code sources before sections or answers exist.

Work:

- Add source registry service/API.
- Support source type, publisher, URL/file reference, retrieved timestamp,
  status, and notes.
- Include codifier/source names needed by catalog v1: Municode, American Legal,
  Code Publishing, General Code, official XML/DOCX exports, official file drops,
  and official web scrape/export paths.
- Support source categories for municipal code, administrative regulations,
  resolutions, policies, adopted ordinances, historical versions, approved
  summaries, and internal staff notes.
- Add source provenance fields required for "configuration transparency":
  source owner, retrieval method, checksum/hash where available, and whether the
  source is official.
- Add source states: `draft`, `active`, `stale`, `superseded`, `failed`.
- Add actionable error messages for missing source, stale source, and failed
  source.

Acceptance tests:

- Full source-state transition matrix.
- Invalid URLs/file references return 4xx with fix path.
- Public endpoints do not expose staff-only source notes.
- Active source cannot be promoted without official-source metadata or an
  explicit non-official label.
- Source category controls public visibility and downstream search eligibility.

## Chunk 4 - Section And Version Model

Goal: model authoritative code structure and effective dates.

Work:

- Add title/chapter/section/subsection APIs.
- Add section version effective-date semantics.
- Add deterministic lookup by section number and date.
- Add admin regulation, resolution, and policy linkage fields so search can
  surface related non-code materials without labeling them as code.
- Add amendment/version history fields so CivicCode can answer what changed and
  when.
- Refuse when date context is ambiguous or missing.

Acceptance tests:

- Lookup current section by number.
- Lookup historical section by date.
- Ambiguous overlapping effective dates fail with actionable 409/422.
- Pending ordinance language is not treated as adopted law.
- Amendment history preserves prior text and current text without silent edits.

## Chunk 5 - Search And Section Permalinks

Goal: let users find code sections without Q&A.

Work:

- Add full-text search across titles/chapters/sections.
- Include subsections, administrative regulations, resolutions, policies, and
  approved summaries in the indexed corpus with public/staff visibility labels.
- Add stable section permalink endpoint.
- Add related-section suggestions for exact section lookups and search results.
- Add empty/no-result/error states.
- Make public search permission-aware even before staff-only notes exist, so the
  leakage contract is established early.
- If UI is added, keep it minimal: search box, results, section detail.

Browser states if UI changes:

- Loading.
- Success with results.
- Empty/no results.
- Error.
- Partial/stale source warning.
- Mobile and desktop.

Acceptance tests:

- Search by exact section number.
- Search by phrase, including resident-style questions such as "can I have
  chickens" when matching source text exists.
- No-result response tells the user what to try next.
- Permalink stays stable across text revisions.
- Public search response never includes internal-only fields.
- Public search clearly distinguishes code, regulation, policy, resolution, and
  summary result types.

## Chunk 6 - Citation Contract

Goal: define the deterministic citation object before any LLM answer exists.

Work:

- Add citation builder.
- Add exact citation format for title/chapter/section/subsection.
- Add source/date/version fields.
- Add refusal object for missing/stale/contradictory sources.
- Add "information, not determination" classification to advice-like responses.

Acceptance tests:

- Every citation includes section id, version id, source id, and effective date.
- Refusal responses include reason and fix path.
- Citation builder never returns uncited prose.
- Advice-like responses are explicitly classified as informational.

## Chunk 7 - Citation-Grounded Q&A Harness

Goal: introduce local-LLM answer drafting under strict refusal rules.

Work:

- Use `civiccore.llm` provider abstraction.
- Add module-specific YAML prompt templates for code Q&A; do not hardcode
  policy-bearing prompts in Python.
- Use the CivicCore template resolver for defaults/overrides.
- Add no-live-provider-call tests.
- Add prompt eval fixtures for routine questions.
- Add refusal tests for missing, stale, ambiguous, and legal-advice questions.
- Add staff-mode answer path only after leakage tests exist; staff answers may
  cite prior approved interpretations and cross-references, but public answers
  may not use staff-only notes.

Acceptance tests:

- Every successful answer has at least one exact citation.
- Legal-advice prompts refuse and route to staff.
- Missing/stale sources refuse.
- Air-gap/no outbound-network check passes.
- Prompt evals fail if an answer lacks citations or presents legal advice.
- Resident answers include authoritative links and "not legal advice" routing.
- Staff answers include richer cross-references without changing the public
  refusal/citation contract.

## Chunk 8 - Popular Questions And Related Sections

Goal: provide safe discovery aids without pretending popular questions are legal
advice.

Status: shipped in CivicCode v0.1.12 as staff-approved popular questions and
explicit related-material navigation aids. Popular questions persist through
`CIVICCODE_SOURCE_REGISTRY_DB_URL` on the Docker/PostgreSQL product path while
the lightweight local path keeps its in-memory store. These surfaces link only
to cited adopted code or public cross-references, keep staff notes private, and
label themselves as navigation aids rather than legal determinations.

Work:

- Add popular-question records tied to approved Q&A fixtures or staff-approved
  summaries.
- Add related-section service using explicit cross-references and search signals.
- Add public display rules for popular questions, related sections, and "people
  also ask" style prompts.
- Add clear labels that these are navigation aids, not determinations.

Browser states if UI changes:

- Popular questions populated.
- No popular questions yet.
- Related sections populated.
- Related sections unavailable.
- Mobile and desktop.

Acceptance tests:

- Public popular questions only link to cited, approved source-backed answers.
- Related sections never include staff-only notes or hidden source material.
- Empty states explain how staff can approve public questions later.
- UI copy says navigation aid, not legal determination.

## Chunk 9 - Plain-Language Summaries

Goal: allow staff-approved summaries without making them authoritative.

Work:

- Add draft/approved/retired summary lifecycle.
- Add staff approval endpoint.
- Add public display of approved summaries only.
- Add visible "non-authoritative explanation" label.
- Keep summary output CivicAccess-ready for future plain-language/multilingual
  workflows.

Browser states if UI changes:

- Draft summary.
- Approved summary.
- Retired summary.
- Missing authoritative section.
- Approval error.

Acceptance tests:

- Public never sees draft summary.
- Approved summary always links back to authoritative section.
- Summary cannot be approved without source citation.
- Summary copy is distinguishable from authoritative code text in API and UI.

## Chunk 10 - Staff Workbench

Goal: support staff Q&A, internal interpretation notes, and prior approved
interpretations without public leakage.

Work:

- Add staff-only note model/API.
- Add staff Q&A workbench that can show cross-references and prior approved
  interpretations.
- Add visibility tests before implementation.
- Add retention/audit behavior once ADR is accepted.
- Add public endpoint leakage tests.
- Add role/RBAC seam without importing unreleased CivicCore auth/RBAC
  placeholders.

Acceptance tests:

- Anonymous/public requests never include note text, metadata, or counts.
- Staff requests include notes only with correct role.
- Staff Q&A can cite internal notes only in staff responses.
- Every note create/update/delete writes audit entry.
- Search and Q&A never use staff-only notes for public answers.

## Chunk 11 - CivicClerk Handoff And Conflict Detection

Goal: receive ordinance/adoption events from CivicClerk and flag likely code
conflicts.

Work:

- Implement accepted handoff contract.
- Accept adopted ordinance/resolution event payloads.
- Mark affected sections/source as stale or pending recodification.
- Distinguish adopted law from pending codifier update.
- Preserve CivicClerk event provenance so the code history can point back to the
  public meeting/action record.
- Detect likely conflicts when proposed or adopted ordinance language touches
  existing sections, repeal/amend phrases, or overlapping effective dates.

Acceptance tests:

- Valid CivicClerk event accepted.
- Invalid event rejected with fix path.
- Pending ordinance language never appears as codified law.
- Stale-code warning appears in affected lookups.
- Likely conflict warnings cite the affected sections and the triggering
  ordinance/resolution event.
- Handoff failures are actionable and do not mutate code state.

## Chunk 12 - Resident Portal/Public Code Lookup UI

Goal: provide CivicCode's resident-facing "Read code" surface while remaining
compatible with the future shared resident portal shell.

Work:

- Add public search/section pages.
- Mount pages under `/civiccode` while remaining compatible with a future shared
  resident portal shell.
- Add clear citation UI.
- Add legal-disclaimer and staff-contact routing.
- Add accessible empty/error/ambiguous states.
- Ensure no color-only status indicators, visible focus states, and
  keyboard-complete workflows per unified spec section 5.2.

Browser states:

- Loading.
- Search success.
- Section detail.
- Empty/no result.
- Ambiguous source refusal.
- Stale source warning.
- Legal-advice refusal.
- Mobile and desktop.

Acceptance tests:

- Keyboard navigation works.
- Focus states visible.
- Contrast acceptable.
- Every user-visible warning has a fix path.
- UI copy separates authoritative code text, plain-language explanation, and
  staff-contact routing.

## Chunk 13 - Import And Async Hardening

Goal: make source ingestion recoverable, auditable, and ready for background
work.

Work:

- Implement chosen codifier/file import strategy.
- Add file-drop/CSV/export import first unless ADR-0002 decides otherwise.
- Support fixture coverage for XML, DOCX, official HTML/web scrape, and
  codifier export shapes where legally available.
- Add Redis/Celery worker path only when async import/indexing needs it.
- Add fixtures for at least two source shapes.
- Add import failure recovery and retry.
- Add provenance report.

Acceptance tests:

- Fixture import creates expected section tree.
- Failed import records actionable error.
- Re-import is idempotent.
- No outbound dependency is required for local file import.
- Background failures are visible through API and docs.

## Chunk 14 - Accessibility And Export Hardening

Goal: align CivicCode public outputs with CivicAccess expectations before
release.

Work:

- Add records-ready export shape for sections, versions, citations, and source
  provenance.
- Add accessible HTML/public-output checks.
- Add tagged-heading expectations for generated docs/exports where applicable.
- Add CivicAccess integration notes without depending on an unshipped
  CivicAccess runtime.

Acceptance tests:

- Public lookup pages pass keyboard/focus/contrast checks.
- Export includes source, version, citation, and retrieval metadata.
- No generated public output lacks headings/labels needed for accessibility.
- Docs state that CivicAccess is planned infrastructure, not a shipped
  dependency.

## Chunk 15 - v0.1.0 Release

Goal: publish CivicCode's first runtime release only after the product is
honest, documented, tested, and browser-verified.

Work:

- Synchronize version surfaces.
- Regenerate docs/manual artifacts.
- Run full release verification.
- Tag and publish release.
- Update `CivicSuite/civicsuite` compatibility matrix after release.

Acceptance tests:

- All tests pass with 0 skipped and 0 xfail.
- Docs gate passes.
- Placeholder-import gate passes.
- Prompt eval gate passes.
- Air-gap/no-live-provider-call checks pass.
- Browser QA evidence attached.
- GitHub release contains expected artifacts and checksums.

## ADR Decision Timing

These ADRs block the listed chunks:

- ADR-0001 official source precedence blocks Chunk 4 and later.
- ADR-0002 codifier import strategy blocks Chunk 13.
- ADR-0003 section versioning blocks Chunk 4.
- ADR-0004 CivicClerk handoff blocks Chunk 11.
- ADR-0005 disclaimer/refusal policy blocks Chunk 7 and Chunk 12.
- ADR-0006 staff interpretation notes blocks Chunk 10.

If an ADR is not decided when a chunk starts, stop and resolve the ADR before
coding that chunk.

## Release Boundary

CivicCode v0.1.0 is not complete until:

- source registry exists,
- section/version model exists,
- search/permalinks exist,
- citation contract exists,
- Q&A refuses unsafe questions and cites exact sections,
- public lookup UI exists,
- accessible/export-ready public outputs exist,
- docs/manual/landing pages match shipped truth,
- compatibility matrix is updated after release.

Anything less is a pre-release foundation, not CivicCode v0.1.0.
