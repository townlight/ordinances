# CivicCode

**Municipal code and ordinance access for the CivicSuite product family.**

CivicCode is the next CivicSuite planning lane. It will help residents,
staff, clerks, planners, and attorneys ask what the municipal code says about
a topic and receive cited, date-aware answers tied to authoritative code
sections.

## Current status

As of 2026-05-04, CivicCode has a **durable code, discovery, staff guidance, CivicClerk handoff, local import-job, codifier sync-state, and operational retry/replay/cursor runtime**
layered on the mock-city codifier contract suite, staff code lifecycle
workspace, records-ready export and accessibility hardening foundation,
local import foundation, public code
lookup surface, CivicClerk handoff,
plain-language summaries, staff workbench, citation-grounded Q&A, citation
contract, search and permalink, section/version, source registry, runtime
foundation, and canonical schema foundations: an
installable Python package, a FastAPI app shell, `/` and `/health` endpoints,
a CivicCore shared-ingestion dependency, canonical SQLAlchemy table
metadata, Alembic migrations under the `civiccode` schema, source registry APIs,
optional database-backed source registry persistence, staff-header-protected
source registry mutations and staff source reads, staff source registry
workspace pages, optional database-backed popular-question persistence,
optional database-backed title/chapter/section/version lifecycle persistence,
optional database-backed staff interpretation-note, plain-language summary,
CivicClerk handoff, import-job, codifier sync-state, and operational retry/replay/cursor persistence,
staff code lifecycle workspace pages,
section/version APIs, public-safe text search, stable section permalinks,
deterministic citation/refusal objects, deterministic citation-grounded answers,
staff-approved public popular questions, explicit related-material navigation
aids,
staff-only interpretation-note APIs with audit events and staff Q&A context,
staff-approved plain-language summaries labeled as non-authoritative, and
CivicClerk ordinance/adoption handoff intake with durable pending codification
warnings and handoff audit events, durable staff import job ledgers with
provenance and actionable failure records, durable codifier sync source
configuration, run cursors, circuit state, delta-plan history, and durable
operational retry queue, replay, and delta-cursor records,
and a Docker Compose product path that starts PostgreSQL 17 with pgvector, runs
migrations, serves the FastAPI app, can seed a Portland Title 13 demo with
`CIVICCODE_DEMO_SEED=1`, and can rehearse a Docker/PostgreSQL backup-restore
with `pg_dump`, `pg_restore`, restored-table verification, and a checksum
manifest.
Residents can open `/civiccode`, search by section number or plain-language
phrase, read adopted code text, see deterministic citations, view approved
plain-language summaries, follow staff-approved popular questions and related
materials as navigation aids, and see pending-codification warnings when
CivicClerk handoffs may affect a section.

This is deliberately not a legal-advice product. The active completion work now includes
local Ollama support for source-bounded answers when configured with
`CIVICCODE_AI_MODE=ollama`; AI output is cited, non-authoritative, and marked
staff-review-required. Deterministic citation extraction remains the fallback
when local Ollama is not configured.
The staff-controlled codifier sync foundation can validate schedules and
source hosts, persist host-validation results, plan delta requests, run
already-fetched local payloads through the import path, and show CivicCore
circuit-breaker health plus the shared source-list health projection. It does not bundle
vendor credentials, make legal determinations, call live LLMs unless a city
operator explicitly configures local Ollama, replace the official codifier, or
automatically codify ordinances. There is no CivicAccess
runtime dependency in this repo yet.
Staff interpretation notes are staff-only and must not be published to public
endpoints. CivicClerk handoff events warn about pending codification but do not
replace adopted code text.

The current CivicCode label is v1.0.8 after the independent release-gate audit
cleared PR #61 at `bfaffc01` with 0 Blocker, 0 Critical, and 0 Major findings.
CivicCode has a real backend, database migrations, substantial municipal-code
workflow logic, local AI integration, React frontend work, real Ollama
embedding retrieval with PostgreSQL pgvector runtime proof, installed-stack and
suite module-selection evidence, source-attributed Portland Title 13 municipal
data fixture proof, and full Longmont PDF ingestion through CivicCore shared
ingestion. The older v0.1.17, v0.1.18, v0.5.0, and mistaken 2026-05-21 v1.0.0
postures remain historical evidence only.

- install and import the package,
- expose health/root endpoints for IT smoke checks,
- run CivicCore migrations before CivicCode migrations,
- create the canonical CivicCode schema tables,
- register official and explicitly non-official source records,
- persist source registry records with `CIVICCODE_SOURCE_REGISTRY_DB_URL`,
- require CivicCore suite-session bearer auth before source registry creation,
  and require either suite-session bearer auth or trusted staff headers before
  staff-only source reads,
- open `/staff/sources` through the trusted staff shell to review source
  readiness, stale/failed blockers, and staff-only notes,
- open `/staff/code` through the trusted staff shell to review section readiness,
  current adopted versions, draft summaries, pending codification warnings, and
  next safe staff actions,
- track source provenance, owner, retrieval method, retrieved timestamp, status,
  and staff notes,
- keep staff-only source notes out of public endpoints,
- create titles, chapters, sections, subsections, and immutable section versions,
- persist title, chapter, section, and section-version lifecycle records with
  `CIVICCODE_SOURCE_REGISTRY_DB_URL` so adopted code structure survives process
  restarts on the Docker/PostgreSQL path,
- look up current or historical adopted text by section number and effective
  date,
- refuse ambiguous overlapping dates and pending ordinance language with an
  actionable fix path,
- search public-visible adopted section text and related public material
  references, and use configured Ollama embeddings plus PostgreSQL pgvector for
  semantic retrieval when the operator enables that runtime,
- publish staff-approved popular questions that link only to cited adopted code,
- persist staff-approved popular questions with `CIVICCODE_SOURCE_REGISTRY_DB_URL`
  so the Docker/PostgreSQL product path keeps resident discovery aids after
  process restarts,
- reject popular-question prompts that ask for legal determinations and return a
  concrete rewrite path,
- show related materials from explicit public cross-references without exposing
  staff notes,
- label popular questions and related materials as navigation aids, not legal
  determinations,
- expose stable section permalinks that survive text revisions,
- resolve adopted section context for CivicZone, CivicLegal, CivicAccess, and
  CivicComms through the `civiccode.section_resolution.v1` contract,
- build deterministic citation objects for adopted section text,
- return structured refusals for missing, stale, or contradictory source
  situations,
- answer citation-grounded questions only when one adopted section and active
  source can be cited,
- refuse legal-determination, uncited, ambiguous, missing, stale, or
  contradictory situations with a reason and fix path,
- create staff-only interpretation notes for a code section,
- persist staff interpretation notes and staff workbench audit events with
  `CIVICCODE_SOURCE_REGISTRY_DB_URL` so staff guidance survives process
  restarts on the Docker/PostgreSQL path,
- keep staff interpretation notes out of public lookup, public search, and
  public Q&A responses,
- let staff Q&A responses include approved staff note context with a
  `staff_only_do_not_publish` warning,
- append staff workbench audit events when notes are created,
- create draft plain-language summaries tied to adopted section versions,
- require staff approval before summaries become public,
- label public summaries as `non_authoritative_explanation`,
- keep authoritative code text visible beside approved summaries,
- append audit events when summaries are created and approved,
- persist draft/approved plain-language summaries and their audit events with
  `CIVICCODE_SOURCE_REGISTRY_DB_URL` so public approved summaries survive
  process restarts on the Docker/PostgreSQL path,
- accept CivicClerk ordinance/adoption handoff events with meeting and agenda
  item provenance,
- persist CivicClerk handoff records and handoff audit events with
  `CIVICCODE_SOURCE_REGISTRY_DB_URL` so pending codification warnings survive
  process restarts on the Docker/PostgreSQL path,
- distinguish pending codification from adopted codified law,
- let staff mark a CivicClerk handoff codified after creating the current
  adopted section version,
- warn affected section lookups when a handoff may make the codified text stale,
- detect likely conflicts when ordinance text references affected sections,
- render a resident-facing public code lookup surface under `/civiccode`,
- serve the React/Vite resident app under `/civiccode/app` with live API search
  and answer calls,
- render a resident-facing cited-answer page under `/civiccode/answer` when one
  adopted section and exact citation ground the response,
- show accessible search success, empty, refusal, stale-source, and section
  detail states,
- import local CSV/file-drop bundles and official HTML extract fixtures through
  staff-only endpoints,
- ingest the full Longmont Code of Ordinances PDF through CivicCore shared
  ingestion, then structure the resulting chunks into CivicCode titles,
  chapters, sections, and adopted versions,
- prove that import/search/cited-answer path against a source-attributed
  Portland municipal code fixture without treating that fixture as a full city
  corpus,
- record import jobs with success or actionable failure states,
- persist import job status, counts, provenance, failure details, and completion
  timestamps with `CIVICCODE_SOURCE_REGISTRY_DB_URL` so staff can inspect
  import history after process restarts on the Docker/PostgreSQL path,
- retry failed import jobs with corrected local bundles,
- produce provenance reports with fixture checksums, source metadata, and a
  no-outbound-dependency marker,
- configure staff-controlled codifier sync readiness for active official
  codifier sources,
- validate codifier sync schedules, source hosts, and supported connector types
  before a source can be synced,
- persist codifier sync source configuration, host-validation result,
  next-run cursor, last attempted/successful run, last import job,
  circuit-breaker state, and delta-plan history with
  `CIVICCODE_SOURCE_REGISTRY_DB_URL`,
- persist operational retry queue, replay, and delta-cursor records for
  CivicClerk handoffs, local imports, and codifier sync runs with
  `CIVICCODE_SOURCE_REGISTRY_DB_URL`,
- expose `/api/v1/civiccode/staff/operational-state` for staff operators to
  inspect current handoff, import, and sync readiness from existing local or
  durable operational records with actionable missing-data fixes,
- render `/staff/imports` and `/staff/sync` so staff can review import
  provenance and codifier sync health without calling external vendors,
- run already-fetched local codifier payloads through the import path without
  outbound vendor calls,
- plan delta request URLs for Municode, American Legal Publishing, Code
  Publishing Company, and General Code,
- expose CivicCore circuit-breaker health, shared source-list health projection,
  and actionable operator copy for repeated sync failures,
- export adopted section records with source, version, citation, and retrieval
  metadata,
- render an accessible, print-friendly records-ready export page,
- validate reusable mock-city codifier contracts for Municode, American Legal
  Publishing, Code Publishing Company, and General Code without outbound vendor
  calls,
- reuse CivicCore municipal IdP and backup-retention mock-city contracts in the
  CivicCode mock-city environment report,
- write a secret-free mock-city environment JSON report with planned delta URLs,
- run `docker compose up --build` against PostgreSQL 17 with pgvector,
  migrations, source-registry persistence, and Portland Title 13 demo data
  enabled by `CIVICCODE_DEMO_SEED=1`,
- smoke the Docker demo with `scripts/docker-demo-smoke.sh`,
- rehearse the Docker/PostgreSQL backup and restore path with
  `scripts/start_docker_backup_restore_rehearsal.ps1` on Windows or
  `scripts/start_docker_backup_restore_rehearsal.sh` on Bash,
- document CivicAccess as planned infrastructure, not a shipped runtime
  dependency,
- consume the CivicCore shared-ingestion pipeline from the published v1.2.0 release wheel,
- reuse the shared CivicCore source-list health projection for codifier sync
  list responses, and
- keep docs, browser QA, adversarial mock validation, and CI gates green for
  the future public-use release gate.

## Why CivicCode before CivicZone

CivicZone remains the first major Tier 2 land-use product, but it needs an
authoritative municipal-code source before it can safely answer zoning
questions. CivicCode is that Tier 1 dependency: it owns code sections,
versions, citations, plain-language summaries, and ordinance-adoption context.

## Product promise

CivicCode will:

- ingest municipal code sources from a city's official publisher,
- preserve title/chapter/section/subsection structure,
- track section versions and effective dates,
- answer natural-language code questions with exact citations,
- label plain-language explanations as non-authoritative,
- route legal-interpretation questions to staff,
- receive ordinance/adoption events from CivicClerk when that contract is
  defined.

## Non-goals

CivicCode is not:

- a codifier,
- legal advice,
- automatic ordinance codification,
- automatic legal interpretation,
- CivicZone runtime work,
- a resident portal shell.

## Source of truth

Read these upstream documents first:

1. `CivicSuite/civicsuite/docs/CivicSuiteUnifiedSpec.md`, section 11.
2. `CivicSuite/civicsuite/docs/roadmap/civiccode-next-module-plan.md`.
3. `CivicSuite/civicsuite/specs/01_catalog.md`, "CivicCode - Municipal Code & Ordinance Access."

## Development status

Install the CivicCore shared-ingestion dependency, then install
CivicCode in editable mode:

```bash
python -m pip install "civiccore @ https://github.com/CivicSuite/civiccore/releases/download/v1.2.0/civiccore-1.2.0-py3-none-any.whl#sha256=a94ce958e36fb03c8d961e4db4672ce5bcfa25765c57d75886e999cf15703ec7"
python -m pip install -e ".[dev]"
python -m uvicorn civiccode.main:app --reload
```

The CivicCore v1.2.0 release wheel is the shared-ingestion dependency for this release train.

Docker demo path:

```bash
cp docker.env.example .env
docker compose up --build
```

Expected Docker truth today: Compose starts PostgreSQL 17 with pgvector and the
CivicCode API bound to `127.0.0.1:${CIVICCODE_PORT:-8000}` for local operator
evaluation, runs CivicCore then CivicCode migrations before serving traffic,
persists source registry, section lifecycle, popular-question, staff-note,
plain-language summary, CivicClerk handoff, handoff audit, import job, codifier sync, and operational state records through
`CIVICCODE_SOURCE_REGISTRY_DB_URL`, and
seeds the Portland Title 13 demo when `CIVICCODE_DEMO_SEED=1`. Open
`http://127.0.0.1:8000/civiccode` and search for `13.40.020` to review the
seeded public lookup path. The default Compose password is local-demo only;
change it in `.env` before any shared environment.

Docker demo smoke:

```bash
bash scripts/docker-demo-smoke.sh
```

The smoke test verifies public lookup behavior and confirms that forged
`X-CivicCode-*` staff headers sent through the published demo port receive HTTP
403. It does not publish or certify a staff shell.

Docker/PostgreSQL backup-restore rehearsal:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_docker_backup_restore_rehearsal.ps1
```

```bash
bash scripts/start_docker_backup_restore_rehearsal.sh
```

The rehearsal expects the Compose stack to be running. It writes a
`.docker-backup-restore-rehearsal/<run-id>/backup/civiccode-postgres.dump`,
restores it into a temporary `civiccode_restore_*` database, verifies restored
application tables, writes
`backup/civiccode-docker-backup-manifest.json` with a SHA-256 checksum, and
drops the temporary restore database unless `--keep-restore-database` is used.
Both launchers call `scripts/check_docker_backup_restore_rehearsal.py`, which
now runs in strict mode by default and can also be run directly with
`--print-only` to review the plan without touching Docker.
If it fails, confirm Docker Desktop is running, start the stack with
`docker compose up -d`, inspect `docker compose logs postgres api`, and rerun
with a fresh run id.

Smoke checks:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
```

Expected truth today: the service reports `docker demo codifier runtime`,
exposes source registry endpoints under `/api/v1/civiccode/sources`, exposes
section/version and search endpoints under `/api/v1/civiccode/sections` and
`/api/v1/civiccode/search`, exposes deterministic citation objects under
`/api/v1/civiccode/citations/build`, exposes citation-grounded answers under
`/api/v1/civiccode/questions/answer`, exposes staff-only workbench endpoints
under `/api/v1/civiccode/staff`, exposes approved public summaries under
`/api/v1/civiccode/sections/{section_id}/summaries`, receives CivicClerk
handoff events at `/api/v1/civiccode/staff/civicclerk/ordinance-events`, exposes
records-ready exports at `/api/v1/civiccode/sections/{section}/export`,
exposes codifier sync readiness endpoints under
`/api/v1/civiccode/staff/sync/codifier-sources`, and marks successful answers
with `code_answer_behavior=citation_grounded`.

Migration smoke:

```bash
set DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/civiccode
python -m alembic -c civiccode/migrations/alembic.ini upgrade head
```

Expected migration truth today: CivicCore migrations run first, CivicCode uses
`alembic_version_civiccode`, ten canonical `civiccode.*` tables are created,
and runtime persistence tables are available for the optional DB-backed source
registry, resident discovery, section lifecycle, staff note, plain-language
summary, CivicClerk handoff, local import-job, codifier sync-state, and operational retry/replay/cursor paths.

Source registry smoke:

```bash
curl http://127.0.0.1:8000/api/v1/civiccode/sources/catalog
```

Expected source-registry truth today: source types include Municode, American
Legal, Code Publishing, General Code, official XML/DOCX exports, official file
drops, and official web scrape/export paths. Source creation requires a
CivicCore suite-session bearer token with a CivicCode staff role; legacy
`X-CivicCode-Role` / `X-CivicCode-Actor` headers alone cannot create sources.
Source states are `draft`, `active`, `stale`, `superseded`, and `failed`. Set
`CIVICCODE_SOURCE_REGISTRY_DB_URL` before source registry persistence smoke
checks; without it, the runtime uses the in-memory store for local demos.

Section/version smoke:

```bash
curl "http://127.0.0.1:8000/api/v1/civiccode/sections/lookup?section_number=6.12.040"
```

Expected section/version truth today: adopted versions can be looked up by
current flag or effective date, pending ordinance language is not treated as
adopted law, and overlapping effective dates return actionable 409 responses.

Search smoke:

```bash
curl "http://127.0.0.1:8000/api/v1/civiccode/search?q=6.12.040"
curl "http://127.0.0.1:8000/api/v1/civiccode/sections/sec_chickens/permalink"
```

Expected search truth today: search returns public-safe structured results and
stable section permalinks. It does not generate answers by itself.

Citation contract smoke:

```bash
curl "http://127.0.0.1:8000/api/v1/civiccode/citations/build?section_number=6.12.040"
```

Expected citation truth today: citation responses are deterministic objects with
section id, version id, source id, effective date, and canonical URL. Refusals
include a reason and fix path.

Citation-grounded Q&A smoke:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/questions/answer \
  -H "Content-Type: application/json" \
  -d '{"question":"What does section 6.12.040 say about backyard chickens?","section_number":"6.12.040"}'
```

Expected Q&A truth today: successful answers quote adopted section text, include
one citation object, set `classification=information_not_determination`, and
state that the answer is not a legal determination. Without local Ollama
configuration the response sets `llm_provider=not_configured` and returns the
deterministic cited extract. With `CIVICCODE_AI_MODE=ollama`,
`CIVICCODE_OLLAMA_URL`, and `CIVICCODE_OLLAMA_MODEL`, CivicCode calls the local
Ollama `/api/generate` endpoint with only the retrieved cited section text and
marks the answer `ai_review_required=true`. Code-answer behavior remains
limited to cited adopted text. Legal-advice, uncited, stale, missing,
ambiguous, or contradictory requests return structured refusals.

Longmont shared-ingestion proof:

```powershell
$env:CIVICCODE_SOURCE_REGISTRY_DB_URL='postgresql+psycopg2://civiccode@localhost:33134/civiccode'
$env:OLLAMA_BASE_URL='http://localhost:11434'
$env:CIVICCODE_OLLAMA_EMBEDDING_URL='http://localhost:11434'
$env:CIVICCODE_EMBEDDING_MODE='ollama'
$env:CIVICCODE_AI_MODE='ollama'
$env:CIVICCODE_OLLAMA_URL='http://localhost:11434'
$env:CIVICCODE_OLLAMA_MODEL='gemma4:e4b'
$env:CIVICCODE_SEMANTIC_SCORE_FLOOR='0.58'
python scripts\prove-longmont-shared-ingestion.py --db-url $env:CIVICCODE_SOURCE_REGISTRY_DB_URL --force-reingest
python scripts\prove-longmont-civiccore-chunk-params.py --db-url $env:CIVICCODE_SOURCE_REGISTRY_DB_URL
```

Expected Longmont proof today: the full Longmont PDF is parsed through
CivicCore shared ingestion, persisted as `document_chunks` with 768-dimensional
Ollama embeddings, structured into CivicCode titles, chapters, sections, and
versions, searched through PostgreSQL pgvector, and answered through a cited,
staff-review-required local Ollama response. See
`docs/qa/civiccode-longmont-shared-ingestion-proof-2026-05-23.md`.

Fresh force-reingest proof for PR #61 completed against the same
12,394,756-byte PDF with 1,604 pages, 2,931 queryable shared chunks, 2,931
embedded rows, `chunk_size=500`, `chunk_overlap=50`, and 1,995 structured
CivicCode sections. The committed section-fidelity proof reports 0 empty
bodies, 0 header/footer-polluted bodies, and a side-by-side `4.12.040`
source/structured sample containing the full public-records paragraph. The
committed dual-run proof script demonstrates that the
older CivicCore evidence listing 1,789 chunks used `chunk_size=900` /
`chunk_overlap=90`; that count is valid for its parameter set but must not be
cited as the current CivicCode PR #61 proof count.

For staff API imports, `pdf_path` must resolve inside
`CIVICCODE_SHARED_INGEST_ALLOWED_DIRS`/`CIVICCODE_SHARED_INGEST_ALLOWED_DIR`,
or the default local `longmont-code-corpus` / module `fixtures` directories.
Semantic nearest-neighbor results below `CIVICCODE_SEMANTIC_SCORE_FLOOR`
(`0.58` by default) are filtered out instead of returning low-confidence
sections for unrelated resident queries.

Staff workbench smoke:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/staff/sections/sec_chickens/notes \
  -H "Content-Type: application/json" \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: planner@example.gov" \
  -d '{"note_text":"Planning staff treats coop setbacks as measured from the property line.","status":"approved"}'

curl -X POST http://127.0.0.1:8000/api/v1/civiccode/staff/questions/answer \
  -H "Content-Type: application/json" \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: planner@example.gov" \
  -d '{"question":"What does section 6.12.040 say about backyard chickens?","section_number":"6.12.040"}'
```

Expected staff-workbench truth today: staff endpoints accept CivicCore
suite-session bearer tokens. Legacy `X-CivicCode-Role: staff` and
`X-CivicCode-Actor` headers are accepted only from a trusted proxy source for
staff read/workbench flows; source creation requires the suite-session bearer
contract. Local mock runs allow loopback (`127.0.0.1/32` and `::1/128`) by
default; shared environments must keep the API behind a header-stripping
reverse proxy, set `CIVICCODE_STAFF_TRUSTED_PROXY_CIDRS` only to that reverse
proxy CIDR list, and strip client-supplied staff headers before CivicCode sees
the request. Do not trust the Docker bridge CIDR on a published API port. Staff
interpretation notes are returned only to staff endpoints, staff Q&A adds
`staff_context` with `staff_only_do_not_publish`, and public lookup, search, and
Q&A never expose staff notes or staff note counts.

Plain-language summary smoke:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/staff/sections/sec_chickens/summaries \
  -H "Content-Type: application/json" \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: clerk@example.gov" \
  -d '{"summary_id":"summary_chickens","section_version_id":"v_current","summary_text":"In plain language: residents may keep up to six chickens if they get a city permit."}'

curl -X POST http://127.0.0.1:8000/api/v1/civiccode/staff/summaries/summary_chickens/approve \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: clerk@example.gov"

curl http://127.0.0.1:8000/api/v1/civiccode/sections/sec_chickens/summaries
```

Expected plain-language truth today: public summaries appear only after staff
approval, are labeled `non_authoritative_explanation`, warn that
plain-language summaries are not law, and include authoritative section text so
the official code remains visible.

CivicClerk handoff smoke:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/civiccode/staff/civicclerk/ordinance-events \
  -H "Content-Type: application/json" \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: clerk@example.gov" \
  -d '{"external_event_id":"cc_event_2026_041","civicclerk_meeting_id":"meeting_2026_04_27","civicclerk_agenda_item_id":"agenda_14","ordinance_number":"2026-041","title":"Ordinance amending backyard chicken permits","status":"adopted","affected_sections":["6.12.040"],"source_document_url":"https://example.gov/minutes/2026-041.pdf","source_document_hash":"sha256:REPLACE_WITH_HASH_OF_SOURCE_DOCUMENT","ordinance_text":"An ordinance amending Section 6.12.040."}'

curl "http://127.0.0.1:8000/api/v1/civiccode/sections/lookup?section_number=6.12.040"
```

Expected CivicClerk handoff truth today: the handoff is stored as pending
codification, persisted with its audit event when
`CIVICCODE_SOURCE_REGISTRY_DB_URL` is configured, CivicClerk meeting/agenda
provenance is preserved, affected lookups include `handoff_warnings`, likely
conflicts cite the affected section, and pending ordinance language is not
adopted law or automatic ordinance codification.

Public lookup smoke:

```bash
curl "http://127.0.0.1:8000/civiccode"
curl "http://127.0.0.1:8000/civiccode/search?q=6.12.040"
curl "http://127.0.0.1:8000/civiccode/sections/6.12.040"
```

Expected public lookup truth today: the page separates authoritative adopted
code text, non-authoritative plain-language summaries, citations, and pending
codification warnings. Legal-advice requests receive refusal copy with a staff
contact route. Live LLM calls remain disabled.

Local import smoke:

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

Expected import truth today: local fixtures can populate the in-memory
title/chapter/section/version tree, re-importing the same bundle is
idempotent, failed imports remain visible through staff endpoints with a fix
path, and provenance reports show source metadata and fixture checksums.
Local imports do not require outbound network calls, Redis/Celery workers, or
vendor credentials.

Codifier sync foundation smoke:

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

Expected codifier sync truth today: staff can configure active official
codifier sources for sync readiness, validate schedules and source hosts,
persist host-validation results, see next-run and circuit-breaker health, plan
delta requests with durable history, and run already
fetched local payloads through the import path. CivicCode does not ship vendor
credentials, does not make outbound calls from the foundation smoke, and does
not automatically codify ordinances.

Mock-city codifier contract smoke:

```bash
python scripts/run_mock_city_environment_suite.py --output .tmp-civiccode-mock-city-report.json
```

Expected mock-city truth today: CivicCode validates secret-free Municode,
American Legal Publishing, Code Publishing Company, and General Code source
contracts through the same local import path used by staff file drops. The
suite renders planned delta URLs for the codifier sync foundation but makes no
outbound vendor calls. Municipal IdP and backup-retention checks come from
shared CivicCore mock-city contracts so later modules can reuse the same
environment pattern.

Records-ready export smoke:

```bash
curl "http://127.0.0.1:8000/api/v1/civiccode/sections/6.12.040/export"
curl "http://127.0.0.1:8000/civiccode/sections/6.12.040/export"
```

Expected export truth today: export payloads include the adopted section text,
section version, deterministic citation, source provenance, retrieval metadata,
accessibility labels, and legal-boundary copy. The HTML export page includes
semantic headings, labels, focus styling, and print-friendly output. CivicAccess
is documented as a future integration target; no CivicAccess dependency is
required or shipped in this repo.

## License

Code: Apache License 2.0; see `LICENSE-CODE`.

Documentation: CC BY 4.0 unless otherwise stated; see `LICENSE-DOCS`.
