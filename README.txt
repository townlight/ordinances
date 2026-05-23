CivicCode
=========

Municipal code and ordinance access for the CivicSuite product family.

Current status
--------------

As of 2026-05-04, CivicCode has a durable code, discovery, staff guidance, CivicClerk handoff, local import-job, codifier sync-state, and operational retry/replay/cursor runtime layered on the
mock-city codifier contract suite, staff code lifecycle workspace,
records-ready export and accessibility
hardening foundation, local import foundation, public code lookup
surface, CivicClerk handoff persistence foundation,
plain-language summaries foundation, staff workbench foundation,
citation-grounded Q&A foundation, citation contract foundation, search and permalink foundation, section/version
foundation, database-backed source registry foundation, runtime foundation, and canonical
schema foundation. The package can
be installed, the FastAPI app can start, / plus /health are available for IT
smoke checks, Alembic can create the canonical civiccode schema tables after
CivicCore migrations run, staff can register official source records, persist
source records with CIVICCODE_SOURCE_REGISTRY_DB_URL when configured, staff can
create titles, chapters, sections, and adopted or pending section versions,
public-safe search/permalink APIs are available, deterministic citation or
refusal objects can be built, and citation-grounded questions can be answered
when one adopted section and active source can be cited. Downstream CivicSuite
modules can use the `civiccode.section_resolution.v1` contract for adopted
section context. Staff-only
interpretation notes, staff Q&A context, and staff workbench audit events are
available behind the trusted staff header seam.
Staff-approved plain-language summaries are available after review, are labeled
non-authoritative, and keep authoritative code text visible.
Local CSV/file-drop bundle and official HTML extract imports are available
through staff-only endpoints, with durable job status, retry, actionable
failure details, counts, completion timestamps, and provenance report behavior
when CIVICCODE_SOURCE_REGISTRY_DB_URL is configured. CivicClerk ordinance/adoption handoff events are accepted and
persisted as pending codification warnings without replacing adopted code text.
Residents can open
/civiccode, search by section number or plain-language phrase, read adopted
code text, ask a cited question at /civiccode/answer, see citations, view approved summaries, and see pending
codification warnings. Docker Compose can start PostgreSQL 17 with pgvector,
run migrations, serve the FastAPI app, persist source registry, staff guidance,
plain-language summary, and CivicClerk handoff records, seed a
City of Brookfield demo with CIVICCODE_DEMO_SEED=1, and rehearse a
Docker/PostgreSQL backup-restore with pg_dump, pg_restore, restored-table
verification, and a checksum manifest.

This is not a legal-advice product. The active v1 work includes local Ollama
support for source-bounded, cited, staff-review-required answers when
CIVICCODE_AI_MODE=ollama and CIVICCODE_OLLAMA_URL are configured. The
staff-controlled codifier sync foundation can validate schedules and source
hosts, persist host-validation results, plan delta requests, run already-fetched local payloads through the
import path, and show CivicCore circuit-breaker health. There is no
CivicAccess runtime dependency, bundled vendor credentials, automatic ordinance codification, or legal
determination behavior yet.
Staff notes are not public. Summaries are not law. Pending ordinance language is not adopted law. Source,
section/version, search, permalink, citation-contract, citation-grounded Q&A,
staff workbench, semantic retrieval, local AI, and local import behavior exists
so authoritative text can be found, cited, imported from local fixtures, and
annotated internally without uncited public answers. Code-answer behavior is
limited to citation_grounded responses.

Local import truth today
------------------------

Staff can submit local CSV/file-drop bundles and official HTML extract fixtures
to /api/v1/civiccode/staff/imports/local-bundle. Completed imports populate the
in-memory source/title/chapter/section/version tree. Failed imports remain
visible through staff endpoints with an actionable fix path. Re-importing the
same bundle is idempotent. Provenance report endpoints expose source metadata,
fixture checksums, and a no-outbound-dependency marker. Redis/Celery workers
and vendor credentials are not required for local import.
Staff can open /staff/imports to review import status, failure recovery copy,
and provenance links in the browser.

Codifier sync foundation truth today
------------------------------------

Staff can configure active official codifier sources at
/api/v1/civiccode/staff/sync/codifier-sources, validate cron schedules and
SSRF-safe source hosts, view next-run and circuit-breaker health, plan delta
requests, and run already-fetched local payloads through the import path.
CivicCode does not ship vendor credentials, make outbound calls from the
foundation smoke, or automatically codify ordinances.
Staff can open /staff/sync to review configured source readiness, circuit
health, host validation, cursor planning, and local payload run state.

Mock-city codifier contract truth today
---------------------------------------

Run:

python scripts/run_mock_city_environment_suite.py --output .tmp-civiccode-mock-city-report.json

The suite validates secret-free Municode, American Legal Publishing, Code
Publishing Company, and General Code source contracts through the local import
path without outbound vendor calls. It renders planned delta URLs for future
codifier sync foundation and reuses CivicCore municipal IdP and backup-retention
mock-city contracts so later modules can reuse the same environment pattern.

Records-ready export truth today
--------------------------------

Public adopted sections can be exported through
/api/v1/civiccode/sections/{section}/export and
/civiccode/sections/{section}/export. The export includes authoritative text,
version metadata, deterministic citation, source provenance, retrieval
metadata, accessibility labels, semantic headings, and legal-boundary copy.
CivicAccess is planned infrastructure, not a shipped runtime dependency.

CivicCode is the next planning lane because CivicZone needs an authoritative
municipal-code source before zoning runtime work begins.

Source of truth
---------------

1. CivicSuite/civicsuite/docs/CivicSuiteUnifiedSpec.md, section 11.
2. CivicSuite/civicsuite/docs/roadmap/civiccode-next-module-plan.md.
3. CivicSuite/civicsuite/specs/01_catalog.md, CivicCode section.

License
-------

Code: Apache License 2.0; see LICENSE-CODE.
Documentation: CC BY 4.0 unless otherwise stated; see LICENSE-DOCS.

Run locally
-----------

1. python -m pip install "civiccore @ https://github.com/CivicSuite/civiccore/releases/download/v1.2.0/civiccore-1.2.0-py3-none-any.whl#sha256=a94ce958e36fb03c8d961e4db4672ce5bcfa25765c57d75886e999cf15703ec7"
2. python -m pip install -e ".[dev]"
3. python -m uvicorn civiccode.main:app --reload
4. curl http://127.0.0.1:8000/health
5. curl http://127.0.0.1:8000/api/v1/civiccode/sources/catalog
6. create staff notes with X-CivicCode-Role: staff and X-CivicCode-Actor

Docker demo
-----------

1. cp docker.env.example .env
2. docker compose up --build
3. open http://127.0.0.1:8000/civiccode
4. search for 6.12.040 to see the seeded City of Brookfield code section
5. bash scripts/docker-demo-smoke.sh

The default Docker password is local-demo only. Change .env before any shared
environment.

Docker/PostgreSQL backup-restore rehearsal
------------------------------------------

1. Start the stack with docker compose up -d.
2. On Windows, run powershell -ExecutionPolicy Bypass -File scripts/start_docker_backup_restore_rehearsal.ps1 -Strict
3. On Bash, run bash scripts/start_docker_backup_restore_rehearsal.sh --strict

The helper writes .docker-backup-restore-rehearsal/<run-id>/backup/civiccode-postgres.dump,
restores into a temporary civiccode_restore_* database, verifies restored
application tables, writes civiccode-docker-backup-manifest.json with a SHA-256
checksum, and drops the temporary database by default. If it fails, confirm
Docker Desktop is running, inspect docker compose logs postgres api, and rerun
with a fresh run id.

The local Docker Compose demo sets CIVICCODE_STAFF_TRUSTED_PROXY_CIDRS to
127.0.0.1/32, ::1/128, and the Docker bridge range 172.16.0.0/12 so
scripts/docker-demo-smoke.sh can verify the seeded staff workspace. Production
deployments should replace that value with the actual trusted reverse-proxy
CIDR list for their staff shell.

Migration smoke
---------------

1. set DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/civiccode
2. python -m alembic -c civiccode/migrations/alembic.ini upgrade head
3. set CIVICCODE_SOURCE_REGISTRY_DB_URL=sqlite:///civiccode-sources.db before source persistence smoke checks

Release
-------

CivicCode v1.0.8 supersedes the earlier v1.0.0 municipal-code module release. It
persists source registry records, title/chapter/section/version records,
staff-approved popular questions, staff notes, plain-language summaries,
CivicClerk handoff records, handoff audit events, local import job records, and codifier sync source records through
`CIVICCODE_SOURCE_REGISTRY_DB_URL` on the Docker/PostgreSQL product path,
reuses the shared CivicCore source-list health projection for codifier sync
source lists, and retains CivicCode-specific legal-boundary copy. Popular
questions and related materials are navigation aids, not legal determinations.
Staff operators can call /api/v1/civiccode/staff/operational-state to inspect
current handoff, import, and sync readiness from existing operational records
with actionable missing-data and retry-work fixes. The endpoint requires no
external deployment proof or outbound network.
