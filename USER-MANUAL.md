# Townlight Code — User manual

Current operating guide · reviewed 2026-10-26 · Code 1.0.8 in accepted connected desktops.

[Product page](https://townlight.github.io/products/code/) · [Overall manual](https://github.com/townlight/townlight/blob/main/USER-MANUAL.md) · [Requirements assessment](https://github.com/townlight/townlight/blob/main/docs/assessment/feature-and-integration-review.md)

## Purpose and audience

Code keeps authoritative code text, section identity, version/date context and the distinction between pending and adopted law. Cited explanations are informational and are not legal advice.

Primary operators: **Clerks, code custodians and legal reviewers**. [Release and acceptance notes](https://github.com/townlight/townlight/releases/tag/townlight-records-meetings-code-zoning-planning-permitting-inspections-v1.7.0-beta.1).

## Before starting

Use the explicit product composition in the installed Townlight desktop. Sign in with the required local staff account, confirm System Health readiness and take a backup before maintenance. If a workspace is absent, inspect the profile and release identity before importing data. Optional AI is not needed for the accepted deterministic workflow. The procedures below use real saved sources; sample/demo web pages are not substitutes.

## Complete the workflow

### 1. Load an authoritative source

Use Code’s import control with a complete supported source bundle. Preview jurisdiction, section identifiers, source date, original file/hash and code text before confirming. A fictional demonstration must remain labelled fictional; an imported file is not automatically adopted law.

### 2. Find a section

Search the intended topic and open the exact cited section. Inspect effective/version context and authoritative text. Keep an explanation separate from the legal text and preserve its citation when using it in staff work.

### 3. Review an adoption handoff

Open actual adopted meeting evidence. Compare the ordinance, adoption date and affected sections. Pending proposals remain pending; adoption and codification are distinct operations.

### 4. Record codification deliberately

Authorized code staff reconcile the imported/adopted text and record the separate code change. Preserve prior versions and the relationship to meeting evidence. A source synchronization or imported candidate is not an automatic legal approval.

### 5. Share a source

Select permitted public section/version evidence for Records, Zoning, Permitting or Inspections. The downstream workflow retains the exact citation and hash. If permissions or the source change, reselect current evidence rather than silently accepting a cached version.

### 6. Review changes and exports

Read the version/adoption history and inspect the exact exported source. Keep any separately edited explanatory document as a derivative with its own hash; do not replace the bytes represented by an existing source hash.

## How this product connects

Meetings supplies adoption evidence; Code supplies cited authority to Zoning, Permitting, Inspections and Records. Planning’s installed selected links are Meetings/Zoning, not a claimed direct Code integration.

## Boundaries and known gaps

Local import, codifier sync orchestration and operational readiness code exist. That does not establish a live contract with every commercial codifier, continuous production fetching or an approved legal codification decision.

## Shared operating rules

Use the installed native desktop for the accepted workflow. Standalone package web pages, sample endpoints and developer API examples are different surfaces. A local Resident/Public view is not an internet deployment. Confirm the selected composition before looking for a workspace.

1. Keep named staff accounts and least privilege. Administrators manage setup; ordinary staff use their authorized workspace. Do not put credentials, unredacted evidence or resident data into public issues.
2. Preserve originals and their hashes. Import preview and confirmation are distinct actions. Treat fictional fixtures as fictional; they are not municipal authority.
3. Save before navigating away, closing or signing out. Unsaved drafts are not a durable record. On a conflict, reopen and reconcile; on an unknown result, inspect the saved record before repeating a write.
4. Review the exact revision and audience. A private packet and a public copy are different artifacts. Public text is explicitly edited/reviewed; changing a filename does not sanitize private content.
5. Keep source permission, version and hash checks. If a provider is stopped or a source becomes restricted, retain the draft, restore authorized access and deliberately reselect evidence. Never bypass the check or substitute a sample.
6. Approval, attachment, export and publication are separate actions. No cross-product attachment is an automatic records response, official permit, legal determination or enforcement decision.

## Installation, maintenance and recovery

Choose a release from the overall manual; do not infer a supported upgrade from a higher version number. Verify its published checksum, publisher signature and acceptance notes before installing. The default download remains the signed 1.4 beta, and Records-only remains its default selection. Planning 1.5.1 has a fresh-install boundary; Permitting and Inspections use separately identified products.

Complete Setup and normal runtime activation for the selected composition. Optional local AI can be deferred. Use System Health to distinguish stopped, starting, ready and failed dependencies. Wait for readiness before opening a dependent workspace. Use documented Retry controls after recovery; do not repeat business writes to refresh a stale screen.

Back up through the canonical desktop controls before migration or maintenance. Keep the coherent data, document and profile backup and its receipt in protected storage. A source export is not a full backup. Stop dependent services before PostgreSQL maintenance. Restore through the supported controls rather than editing SQL or restoring historical JSON into the active runtime. Uninstall can retain data; backup before uninstalling and inspect the chosen removal options. Never assume uninstall means data deletion.

For an error, retain the message, time, selected profile, installed version and operation; inspect System Health and relevant logs. Use a redacted support bundle. Do not delete the profile, run an arbitrary downgrade or repair prerequisites as a first response. If an installer requests a restart, save work and obtain the operator’s explicit restart decision before proceeding.

## Evidence and scope

This manual reuses the accepted installed, required-CI and signed-delivery evidence. It does not turn source inspection into a new installed test. Recovery evidence is reused only within its recorded candidate/profile boundaries; no universal upgrade, hardware, accessibility or production deployment certification is implied. The [overall manual](https://github.com/townlight/townlight/blob/main/USER-MANUAL.md) gives release identities and shared operations. The [feature and integration assessment](https://github.com/townlight/townlight/blob/main/docs/assessment/feature-and-integration-review.md) separates implementation, explicit deferral, missing capability and unverified acceptance.


## Maintainer and API reference

The following source contracts support these instructions. The historical reference below retains older API/setup details for their original version; it does not override this operating guide or the release acceptance.

- [civiccode/main.py](https://github.com/townlight/ordinances/tree/main/civiccode/main.py)
- [civiccode/import_connectors.py](https://github.com/townlight/ordinances/tree/main/civiccode/import_connectors.py)
- [civiccode/codifier_sync.py](https://github.com/townlight/ordinances/tree/main/civiccode/codifier_sync.py)
- [civiccode/operational_readiness.py](https://github.com/townlight/ordinances/tree/main/civiccode/operational_readiness.py)


---

## Historical package/API reference

The material below is retained from the previous manual for historical and developer reference. Version, unreleased, sample, planned and installation claims below describe that earlier document, not current desktop release status. Use the current guide above for operation. Existing detailed API reference remains useful only for the matching package/version.

<a id="civiccode-user-manual"></a>

# Townlight Code User Manual

## Published connected desktop: 1.4.0-beta.1

This module participates in the signed Townlight Records + Meetings + Code +
Zoning desktop beta published October 21, 2026. Select zoning-beta for all four
products; Records-only remains default and city-core excludes Zoning.
[Download and release limits](https://github.com/townlight/townlight/releases/tag/townlight-records-meetings-code-zoning-v1.4.0-beta.1) ·
[Current operator manual](https://github.com/townlight/townlight/blob/main/USER-MANUAL.md) ·
[Signed acceptance](https://github.com/townlight/townlight/blob/main/docs/installer/townlight-zoning-beta1-signed-acceptance.md).

This is a connected desktop release, not a new standalone package version.
Package/import/API names remain compatibility identifiers. Historical development
checkpoints below retain their original scope; they are superseded for current
desktop publication status. No signed installer or historical evidence is changed.

Townlight Code currently ships a popular-questions and related-sections discovery
runtime built on the
mock-city codifier contract suite, staff code lifecycle workspace,
records-ready export and accessibility hardening foundation, local import
job persistence foundation, public code lookup surface,
Townlight Meetings handoff persistence foundation,
plain-language summaries foundation, staff workbench foundation,
citation-grounded Q&A foundation, citation contract foundation, search and
permalink foundation, section/version foundation, source
registry foundation, runtime foundation, and canonical schema foundation. This manual
explains what a first-time installer can do today and what is still planned.

The source registry remains the official source metadata foundation for every
summary, citation, lookup, popular question, related-material navigation aid,
and Q&A response. It can now persist source records, popular questions, code
section lifecycle records, staff notes, plain-language summaries,
Townlight Meetings handoff records, local import job ledgers, and codifier sync source
state when
`CIVICCODE_SOURCE_REGISTRY_DB_URL` is configured; otherwise it uses the
in-memory stores for lightweight local demos. Staff source mutations and
staff-only source reads require the trusted staff header seam, and
`/staff/sources` makes active, stale, and failed source readiness visible to
code administrators. `/staff/code` gives staff a single lifecycle review page
for current adopted versions, source readiness, draft summaries, staff note
counts, and pending Townlight Meetings codification warnings. The Docker Compose path
starts PostgreSQL 17 with pgvector, runs migrations, serves the API, enables a
Portland Title 13 seeded demo with `CIVICCODE_DEMO_SEED=1`, and includes a
Docker/PostgreSQL backup-restore rehearsal for IT staff to prove `pg_dump` and
`pg_restore` before trusting a shared environment.

## For municipal decision-makers

Townlight Code is planned to make municipal code easier to search, cite, and
explain. It will not replace the city's official codifier and will not provide
legal advice. The goal is to help residents and staff find exact code sections
and understand next steps.

Current truth:

- the Python package can be installed,
- the FastAPI app can be started,
- `/` explains the current product boundary,
- `/health` reports service, Townlight Code version, and Townlight Core version,
- Alembic can create ten canonical `civiccode.*` tables after Townlight Core
  migrations run,
- staff can register source records for official and explicitly non-official
  municipal code materials,
- source registry creation requires a Townlight Core suite-session bearer token, and
  staff-only source reads require either a suite-session bearer token or trusted
  staff headers,
- staff can open `/staff/sources` through the trusted staff shell to review
  source readiness, staff-only notes, and stale/failed fix paths,
- staff can open `/staff/code` through the trusted staff shell to review
  section readiness, current adopted versions, draft summaries, pending
  codification warnings, and next safe actions,
- staff can persist source registry records with
  `CIVICCODE_SOURCE_REGISTRY_DB_URL`,
- public source endpoints do not expose staff-only notes,
- staff can create titles, chapters, sections, subsections, and immutable
  section versions,
- current and historical lookup returns adopted law only,
- pending ordinance language and ambiguous overlapping effective dates return
  actionable errors instead of being treated as settled law,
- public-safe search can find adopted section text and related public material
  references,
- when a city operator enables local Ollama embeddings, Townlight Code persists
  learned vectors and uses PostgreSQL pgvector ranking for semantic search,
- staff can approve popular questions that link only to cited adopted code,
- popular questions and related materials are labeled as navigation aids, not
  legal determinations,
- public related-material lists come only from explicit public cross-references
  and do not expose staff notes,
- stable section permalinks remain the same across text revisions,
- downstream Townlight modules can resolve adopted code context through
  `civiccode.section_resolution.v1` for Townlight Zoning, Townlight Legal, Townlight Access, and
  Townlight Communications,
- deterministic citation objects can be built from adopted section text,
- citation refusals include reasons and fix paths for missing, stale, or
  contradictory source situations,
- citation-grounded questions can be answered when they resolve to one adopted
  section and one active source,
- legal-determination, uncited, stale, missing, ambiguous, or contradictory
  questions return structured refusals,
- staff can create staff-only interpretation notes for a code section,
- staff Q&A responses can include approved staff interpretation notes with a
  `staff_only_do_not_publish` warning,
- public lookup, public search, and public Q&A responses do not expose staff
  notes or staff note counts,
- staff note writes append audit events,
- staff notes and staff workbench audit events persist on the configured
  Docker/PostgreSQL path,
- staff can draft and approve plain-language summaries tied to adopted section
  versions,
- public summaries are visible only after staff approval,
- approved public summaries are labeled `non_authoritative_explanation` and
  displayed with authoritative section text,
- summary drafts, approvals, and summary audit events persist on the configured
  Docker/PostgreSQL path,
- staff can receive Townlight Meetings ordinance/adoption handoff events,
- Townlight Meetings handoff records and handoff audit events persist on the configured
  Docker/PostgreSQL path,
- affected section lookups include pending codification warnings,
- pending ordinance language is not adopted law and does not replace codified
  text,
- staff can run local CSV/file-drop bundle and official HTML extract imports,
- the bundled Portland Title 13 evidence corpus imports two official chapter
  sources and five adopted sections with package-local source artifacts,
- failed imports remain visible with an actionable fix and can be retried with
  corrected local bundles,
- local import job ledgers persist status, counts, provenance, actionable
  failure details, and completion timestamps on the configured
  Docker/PostgreSQL path,
- codifier sync source state persists configuration, host-validation result,
  next-run cursor, last attempted/successful run, circuit-breaker state, and
  delta-plan history on the configured Docker/PostgreSQL path,
- staff operators can call `/api/v1/civiccode/staff/operational-state` to view
  current handoff, import, and sync readiness from existing operational records,
  including specific fixes when state is missing or queued retry work exists,
- staff operators can open `/staff/imports` and `/staff/sync` for browser
  review of import provenance and codifier sync health,
- provenance reports show source metadata, fixture checksum, and
  no-outbound-dependency status,
- staff can configure active official codifier sources for sync readiness,
- codifier sync schedules and source hosts are validated before a sync source
  can run,
- already-fetched local codifier payloads can run through the import path with
  delta request planning,
- repeated sync failures surface Townlight Core circuit-breaker health and an
  actionable fix path,
- adopted sections can be exported with source, version, citation, and
  retrieval metadata,
- records-ready HTML exports include semantic headings, labels, focus styling,
  and print-friendly output,
- Townlight Access is documented as future integration infrastructure, not a shipped
  runtime dependency,
- residents can open `/civiccode`, search by section number or phrase, and read
  adopted code text with citations and warnings,
- residents can open `/civiccode/answer` to ask what one adopted section says
  and receive a cited, non-determination answer,
- staff can mark Townlight Meetings handoffs codified after creating the current
  adopted section version, which removes stale-code warnings for that handoff,
- no bundled vendor credentials, automatic ordinance codification, or legal
  determinations are generated. Local Ollama answers are available only when
  explicitly configured and remain cited, non-authoritative, and
  staff-review-required.

For a non-technical user, the first public "Read code" workflow is now available: open
`/civiccode`, enter a section number or phrase, review search results, open a
section detail page, and read the authoritative code text, citation,
plain-language summary, popular-question/related-material navigation aids, and
any pending codification warning. The page also routes legal-advice questions
back to staff.

## For IT and technical staff

This repo contains staff operations surfaces, Townlight Core v1 contracts, durable
import/codifier sync state, and documentation and verification gates. Townlight Code
is at v1.0.8 after independent release-gate re-audit #5 cleared PR #61 at
`bfaffc01` with 0 Blocker, 0 Critical, and 0 Major findings. Runtime
implementation must follow the Townlight pattern:

- standalone module repo under `CivicSuite/`,
- Townlight Core shared-ingestion dependency at the published v1.2.1 release wheel,
- local LLM only through `civiccore.llm`,
- no cloud dependency,
- no imports from unreleased Townlight Core placeholder packages.

Townlight Code can ingest the full Longmont Code of Ordinances PDF through Townlight Core
shared ingestion, persist the resulting `document_chunks` with 768-dimensional
Ollama embeddings, structure the corpus into Townlight Code title/chapter/section/
version records, and answer a cited question through a local Ollama model.

Install and run:

```bash
python -m pip install "civiccore @ https://github.com/townlight/core/releases/download/v1.2.1/civiccore-1.2.1-py3-none-any.whl#sha256=8dde29408e206048bde63ec14156a8e6329382af4d16b12710d12aa5c27f3f59"
python -m pip install -e ".[dev]"
python -m uvicorn civiccode.main:app --reload
```

Run the Docker demo:

```bash
cp docker.env.example .env
docker compose up --build
```

With the default `CIVICCODE_DEMO_SEED=1`, a first-time evaluator can open
`http://127.0.0.1:8000/civiccode`, search for `13.40.020`, read seeded
Portland Title 13 code text, and see the non-authoritative summary warning. The
Compose file binds the published API port to loopback only. The default
database password in `docker.env.example` is for local demo use only; change it
before a shared environment. Smoke the running stack with:

```bash
bash scripts/docker-demo-smoke.sh
```

Rehearse Docker/PostgreSQL backup and restore after the stack is running:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_docker_backup_restore_rehearsal.ps1
```

```bash
bash scripts/start_docker_backup_restore_rehearsal.sh
```

The rehearsal is intentionally non-destructive: it dumps the `civiccode`
database from the Compose `postgres` service, restores into a temporary
`civiccode_restore_*` database, verifies restored application tables, writes
`.docker-backup-restore-rehearsal/<run-id>/backup/civiccode-docker-backup-manifest.json`,
and drops the temporary restore database unless instructed otherwise. Both launchers
call `scripts/check_docker_backup_restore_rehearsal.py` in strict mode by default,
which can also be run directly with `--print-only` to review the plan without touching Docker. If it
fails, confirm Docker Desktop is running, start the stack with `docker compose
up -d`, inspect `docker compose logs postgres api`, and rerun with a new run id.

Smoke checks:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
```

Run migrations:

```bash
set DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/civiccode
python -m alembic -c civiccode/migrations/alembic.ini upgrade head
```

The migration chain runs Townlight Core first and stores Townlight Code's revision in
`alembic_version_civiccode`. The durable product path adds
`source_registry_records`, `popular_question_records`, and
`code_title_records` / `code_chapter_records` / `code_section_records` /
`section_version_records`, plus `staff_interpretation_note_records`,
`staff_workbench_audit_event_records`, `plain_language_summary_records`, and
`plain_language_summary_audit_event_records`, `ordinance_handoff_records`,
`ordinance_handoff_audit_event_records`, `import_job_records`,
`codifier_sync_source_records`, and `codifier_sync_delta_plan_records` as runtime
tables for source metadata, resident discovery aids, adopted-code lifecycle
data, staff guidance, non-authoritative public summaries, Townlight Meetings
pending-codification warnings, and staff import history.

Inspect source-registry vocabulary:

```bash
curl http://127.0.0.1:8000/api/v1/civiccode/sources/catalog
```

Register an official source:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/sources \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CIVICCORE_SUITE_SESSION_TOKEN" \
  -d '{
    "source_id": "municode_current",
    "name": "Example Municipal Code",
    "publisher": "Municode",
    "source_type": "municode",
    "source_category": "municipal_code",
    "source_url": "https://library.municode.com/example/codes/code_of_ordinances",
    "retrieved_at": "2026-04-27T12:00:00Z",
    "retrieval_method": "official_web_export",
    "source_owner": "City Clerk",
    "is_official": true,
    "status": "active"
  }'
```

The registry accepts `draft`, `active`, `stale`, `superseded`, and `failed`
source states. Source creation requires a Townlight Core suite-session bearer token
with a Townlight Code staff role; legacy `X-CivicCode-Role` / `X-CivicCode-Actor`
headers alone cannot create sources. `active` official sources require source
owner and retrieval metadata. `active` non-official sources require an explicit
non-official note. Stale and failed sources return actionable fix guidance. Set
`CIVICCODE_SOURCE_REGISTRY_DB_URL` before persistence smoke checks.

Create section structure:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/titles \
  -H "Content-Type: application/json" \
  -d '{"title_id":"title_6","title_number":"6","title_name":"Animals"}'

curl -X POST http://127.0.0.1:8000/api/v1/civiccode/chapters \
  -H "Content-Type: application/json" \
  -d '{"chapter_id":"chapter_6_12","title_id":"title_6","chapter_number":"6.12","chapter_name":"Urban Livestock"}'

curl -X POST http://127.0.0.1:8000/api/v1/civiccode/sections \
  -H "Content-Type: application/json" \
  -d '{"section_id":"sec_chickens","chapter_id":"chapter_6_12","section_number":"6.12.040","section_heading":"Backyard chickens"}'
```

Create adopted text:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/sections/sec_chickens/versions \
  -H "Content-Type: application/json" \
  -d '{
    "version_id": "v_current",
    "section_id": "sec_chickens",
    "source_id": "municode_current",
    "version_label": "Current",
    "body": "Up to six hens are allowed with a permit.",
    "effective_start": "2026-01-01",
    "status": "adopted",
    "is_current": true
  }'
```

Lookup current adopted text:

```bash
curl "http://127.0.0.1:8000/api/v1/civiccode/sections/lookup?section_number=6.12.040"
```

The lookup response is still not a code answer. It returns structured section
and version data with `code_answer_behavior=not_available`.

Search public-safe section data:

```bash
curl "http://127.0.0.1:8000/api/v1/civiccode/search?q=chickens"
```

Read a stable section permalink:

```bash
curl "http://127.0.0.1:8000/api/v1/civiccode/sections/sec_chickens/permalink"
```

Search results distinguish code sections from related administrative
regulations, resolutions, policies, and approved summaries when those public
references exist. Empty search results include a fix path such as trying an
exact section number or fewer words.

Build a deterministic citation object:

```bash
curl "http://127.0.0.1:8000/api/v1/civiccode/citations/build?section_number=6.12.040"
```

Citation objects include section id, version id, source id, effective date, and
canonical URL. If the source is missing, stale, contradictory, or ambiguous, the
response is a structured refusal with a reason and fix path.

Ask a citation-grounded code question:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/questions/answer \
  -H "Content-Type: application/json" \
  -d '{"question":"What does section 6.12.040 say about backyard chickens?","section_number":"6.12.040"}'
```

Code-answer behavior is limited to citation-grounded responses. The Q&A harness
returns an answer only when it can attach one deterministic citation to adopted
code text. It refuses legal determinations, uncited questions, missing sections,
stale sources, and contradictory effective-date windows with a reason and fix
path. When local Ollama is configured with `CIVICCODE_AI_MODE=ollama`,
`CIVICCODE_OLLAMA_URL`, and `CIVICCODE_OLLAMA_MODEL`, Townlight Code sends only the
retrieved cited section text to the local model and marks the response
`ai_review_required=true`. Without that local runtime, it returns the
deterministic cited extract with `llm_provider=not_configured`.

Create a staff-only interpretation note:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/staff/sections/sec_chickens/notes \
  -H "Content-Type: application/json" \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: planner@example.gov" \
  -d '{
    "note_text": "Planning staff generally treats coop setbacks as measured from the property line.",
    "status": "approved"
  }'
```

Ask a staff Q&A question with approved staff note context:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/staff/questions/answer \
  -H "Content-Type: application/json" \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: planner@example.gov" \
  -d '{"question":"What does section 6.12.040 say about backyard chickens?","section_number":"6.12.040"}'
```

Staff endpoints accept Townlight Core suite-session bearer tokens. Legacy
`X-CivicCode-Role: staff` and `X-CivicCode-Actor` headers are accepted only from
a trusted proxy source for staff read/workbench flows; source creation requires
the suite-session bearer contract. Local mock runs allow loopback
(`127.0.0.1/32` and `::1/128`) by default. Shared environments must keep
Townlight Code behind a header-stripping reverse proxy, set
`CIVICCODE_STAFF_TRUSTED_PROXY_CIDRS` only to that reverse proxy CIDR list, and
strip client-supplied staff headers before Townlight Code sees the request. Do not
trust the Docker bridge CIDR on a published API port. Staff Q&A context is
explicitly marked `staff_only_do_not_publish`. Public lookup, public search, and
public Q&A responses must not expose staff note text or staff note counts.

Draft and approve a plain-language summary:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/staff/sections/sec_chickens/summaries \
  -H "Content-Type: application/json" \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: clerk@example.gov" \
  -d '{
    "summary_id": "summary_chickens",
    "section_version_id": "v_current",
    "summary_text": "In plain language: residents may keep up to six chickens if they get a city permit."
  }'

curl -X POST http://127.0.0.1:8000/api/v1/civiccode/staff/summaries/summary_chickens/approve \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: clerk@example.gov"
```

Read approved public summaries:

```bash
curl http://127.0.0.1:8000/api/v1/civiccode/sections/sec_chickens/summaries
```

Public summaries are non-authoritative explanations. They must link back to the
adopted section version and keep the authoritative code text visible beside the
summary.

Receive a Townlight Meetings ordinance/adoption handoff:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/staff/civicclerk/ordinance-events \
  -H "Content-Type: application/json" \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: clerk@example.gov" \
  -d '{
    "external_event_id": "cc_event_2026_041",
    "civicclerk_meeting_id": "meeting_2026_04_27",
    "civicclerk_agenda_item_id": "agenda_14",
    "ordinance_number": "2026-041",
    "title": "Ordinance amending backyard chicken permits",
    "status": "adopted",
    "affected_sections": ["6.12.040"],
    "source_document_url": "https://example.gov/minutes/2026-041.pdf",
    "source_document_hash": "sha256:REPLACE_WITH_HASH_OF_SOURCE_DOCUMENT",
    "ordinance_text": "An ordinance amending Section 6.12.040."
  }'
```

Public lookup route:

```bash
curl "http://127.0.0.1:8000/civiccode"
curl "http://127.0.0.1:8000/civiccode/search?q=6.12.040"
curl "http://127.0.0.1:8000/civiccode/sections/6.12.040"
curl "http://127.0.0.1:8000/civiccode/answer?q=What%20does%20section%206.12.040%20say%3F&section_number=6.12.040"
```

Townlight Meetings handoff events preserve meeting and agenda item provenance. They
persist with handoff audit events when `CIVICCODE_SOURCE_REGISTRY_DB_URL` is
configured, surface pending codification warnings on affected lookups, and show
likely conflict signals when ordinance text references existing sections. They
do not perform automatic ordinance codification and pending ordinance language
is not adopted law. After staff creates the codified adopted section version,
staff can resolve the handoff so stale-code warnings no longer show for that
event.

Local import route:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/staff/imports/local-bundle \
  -H "Content-Type: application/json" \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: clerk@example.gov" \
  --data-binary @tests/fixtures/milestone_12/csv_bundle.json

curl -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: clerk@example.gov" \
  http://127.0.0.1:8000/api/v1/civiccode/staff/imports/import_csv_animals/provenance
```

Local imports are synchronous and air-gap friendly in this milestone. The
fixture import creates or reuses source, title, chapter, section, and version
records; failed imports are stored with a fix path and can be retried. Local
imports do not require Redis/Celery workers, vendor credentials, or outbound
network calls.

Codifier sync foundation route:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/staff/sync/codifier-sources \
  -H "Content-Type: application/json" \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: clerk@example.gov" \
  -d '{"source_id":"municode_current","sync_schedule":"*/15 * * * *"}'

curl -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: clerk@example.gov" \
  http://127.0.0.1:8000/api/v1/civiccode/staff/sync/codifier-sources
```

The sync foundation is staff-controlled: it validates the active official
source, validates the schedule, checks the source URL against Townlight Core's host
guardrails, plans delta request URLs, runs already-fetched local payloads
through the import path, and shows operator health using Townlight Core's
circuit-breaker copy. It does not ship vendor credentials, contact vendor
networks during the foundation smoke, make legal determinations, or
automatically codify ordinances.

Mock-city codifier contract route:

```bash
python scripts/run_mock_city_environment_suite.py --output .tmp-civiccode-mock-city-report.json
```

The reusable mock-city suite validates secret-free Municode, American Legal
Publishing, Code Publishing Company, and General Code source contracts through
Townlight Code's local import path. It renders planned delta URLs for the codifier
sync foundation but performs no outbound vendor calls. The same report also reuses
Townlight Core municipal IdP and backup-retention mock-city contracts so later
Townlight modules can inherit the pattern instead of rebuilding it.

Records-ready export route:

```bash
curl "http://127.0.0.1:8000/api/v1/civiccode/sections/6.12.040/export"
curl "http://127.0.0.1:8000/civiccode/sections/6.12.040/export"
```

The export API returns authoritative section text, version metadata,
deterministic citation, source provenance, retrieval metadata, accessibility
labels, and legal-boundary copy. The HTML export page uses semantic headings,
labels, focus styling, and print-friendly output. Townlight Access is planned
infrastructure, not a required or shipped dependency in this repo.

## Architecture reference

Planned dependency direction:

```text
civicsuite docs/governance
        |
        v
civiccore shared platform
        |
        v
civiccode municipal-code module
        |
        v
future consumers: civiczone, civiclegal, civicaccess, civiccomms
```

Townlight Code v1.0.8 supersedes the earlier v1.0.0 municipal-code module release. The
older v0.1.17, v0.1.18, v0.5.0, and mistaken 2026-05-21 v1.0.0 publications are historical pre-gate releases; check
`docs/ops/tier1-retrofit-ledger.md` before relying on those older artifacts.
The product line
reuses the shared Townlight Core source-list health projection for codifier sync
source lists while retaining Townlight Code-specific legal-boundary copy, and it now
keeps local import job status, codifier sync configuration, host-validation
results, circuit-breaker state, delta-plan history, and completion timestamps
in the configured database. Future work moves to the next module or release
plan only after Townlight Code release evidence is reconciled.
