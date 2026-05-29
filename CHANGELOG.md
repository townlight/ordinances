# Changelog

## [Unreleased]

- Aligns the default local Ollama answer model with the city-core installer
  pull set by using `gemma4:e4b` when `CIVICCODE_OLLAMA_MODEL` is unset.
- Hardened the existing CivicClerk ordinance-event intake route with an
  optional shared-intake authorization header for city-core service-to-service
  handoff calls, without broadening trusted staff-header access for the rest of
  the staff API.
- Accepts the same configured CivicClerk handoff secret as a suite bearer token
  so the city-core launcher can wire CivicClerk to CivicCode without re-enabling
  spoofable staff headers.
- Documented the shipped CivicClerk live-emitter counterpart in ADR-0004.

## [1.0.8] - 2026-05-23

- Installs the Playwright Chromium browser immediately before public browser QA
  in the release workflow so `npm ci` cannot replace the Playwright package
  after the browser cache has been prepared.
- Keeps the explicit `workflow_dispatch` release fallback, valid workflow YAML,
  conservative action versions, split bounded release verification, PR #61
  shared-ingestion implementation, CivicCore v1.2.0 release wheel pin, and
  Longmont end-to-end proof unchanged.
- Supersedes the failed, unpublished v1.0.1 through v1.0.7 tag attempts
  without rewriting those tags.

## [1.0.7] - 2026-05-23

- Fixes the release workflow YAML syntax error that kept v1.0.5 and v1.0.6
  from registering runnable release jobs or the manual dispatch fallback.
- Keeps the explicit `workflow_dispatch` release fallback, conservative action
  versions, split bounded release verification, PR #61 shared-ingestion
  implementation, CivicCore v1.2.0 release wheel pin, and Longmont
  end-to-end proof unchanged.
- Supersedes the failed, unpublished v1.0.1 through v1.0.6 tag attempts
  without rewriting those tags.

## [1.0.6] - 2026-05-23

- Normalizes the release workflow to conservative GitHub Actions versions after
  the v1.0.5 tag still produced empty-job release workflow failures before
  artifact publication.
- Keeps the explicit `workflow_dispatch` release fallback, split bounded
  release verification, PR #61 shared-ingestion implementation, CivicCore
  v1.2.0 release wheel pin, and Longmont end-to-end proof unchanged.
- Supersedes the failed, unpublished v1.0.1, v1.0.2, v1.0.3, v1.0.4, and
  v1.0.5 tag attempts without rewriting those tags.

## [1.0.5] - 2026-05-23

- Adds an explicit `workflow_dispatch` release fallback after the v1.0.4 tag
  push produced immediate no-job GitHub Actions failures for `release.yml`
  before artifact publication.
- Keeps the split, bounded release verification steps from v1.0.4 so the
  workflow provides step-level evidence for product tests, release-provenance
  tests, docs/placeholder/Ruff gates, frontend build, public browser QA,
  artifacts, attestation, and publication.
- Keeps the PR #61 shared-ingestion implementation, CivicCore v1.2.0 release
  wheel pin, and Longmont end-to-end proof unchanged.
- Supersedes the failed, unpublished v1.0.1, v1.0.2, v1.0.3, and v1.0.4 tag
  attempts without rewriting those tags.

## [1.0.4] - 2026-05-23

- Splits the CivicCode release workflow verification from one monolithic
  `verify-release.sh` step into explicit bounded test, documentation,
  placeholder-import, Ruff, frontend-build, and public-browser-QA steps after
  the v1.0.3 tag run also wedged before artifact publication.
- Preserves the same release verification coverage proven locally by
  `bash scripts/verify-release.sh` while making the GitHub release workflow
  produce step-level evidence and fail at the specific bounded gate.
- Keeps the PR #61 shared-ingestion implementation, CivicCore v1.2.0 release
  wheel pin, and Longmont end-to-end proof unchanged.
- The v1.0.4 tag attempt produced immediate no-job GitHub Actions failures for
  `release.yml` before artifact publication; v1.0.5 replaces it without
  rewriting the tag.

## [1.0.3] - 2026-05-23

- Hardens the CivicCode release workflow after the v1.0.2 tag attempt wedged
  in GitHub Actions without publishing a release.
- Adds a job-level timeout plus a shell-level `timeout 90m` wrapper around the
  release-verification command so future release runs fail visibly instead of
  remaining indefinitely in progress.
- Keeps the PR #61 shared-ingestion implementation, CivicCore v1.2.0 release
  wheel pin, and Longmont end-to-end proof unchanged.
- The v1.0.3 tag attempt also wedged before artifact publication; v1.0.4
  replaces it without rewriting the tag.

## [1.0.2] - 2026-05-23

- Replaced the CivicCore shared-ingestion commit-archive dependency with the
  published CivicCore v1.2.0 release wheel for the city-core release train.
- Preserves the PR #61 shared-ingestion implementation and Longmont
  end-to-end proof. The v1.0.2 tag attempt did not publish a release because
  the GitHub Actions release-verification step wedged before artifact
  publication.
- Supersedes the failed, unpublished v1.0.1 tag attempt without rewriting the
  v1.0.1 tag.

## [1.0.0] - 2026-05-23

- Repointed active-branch CivicCode to the CivicCore shared-ingestion
  published CivicCore v1.2.0 release wheel instead of the older `v1.1.0` wheel so full PDF parsing, chunking, and embedding come from
  CivicCore.
- Added the staff-only `/api/v1/civiccode/staff/imports/shared-pdf` path for
  ingesting a municipal code PDF through CivicCore and structuring the result
  into CivicCode title/chapter/section/version records.
- Switched CivicCode embedding calls to the CivicCore ingestion embedder and
  made PostgreSQL semantic ranking use shared CivicCore `document_chunks`
  pgvector rows instead of CivicCode-local section embedding storage.
- Added `scripts/prove-longmont-shared-ingestion.py`,
  `scripts/prove-longmont-civiccore-chunk-params.py`, and
  `scripts/prove-longmont-section-fidelity.py` plus
  `docs/qa/civiccode-longmont-shared-ingestion-proof-2026-05-23.md` with
  full Longmont PDF proof: 2,931 shared chunks, 2,931 embedded rows, 1,995
  structured sections, shared pgvector search, and local Ollama cited Q&A.
  The force-reingest proof records the exact input basis: 1,604 pages,
  12,394,756 source bytes, 2,931 chunks, `chunk_size=500`,
  `chunk_overlap=50`, and 768-dimensional embeddings; the dual-run script
  reproduces `chunk_size=900` / `chunk_overlap=90` as 1,789 chunks and
  `chunk_size=500` / `chunk_overlap=50` as 2,931 chunks from the same PDF.
  The section-fidelity proof reports 0 empty bodies, 0 header/footer-polluted
  bodies, and a `4.12.040` side-by-side source/structured sample with the full
  public-records paragraph.
- Promoted CivicCode to `1.0.0` after independent release-gate re-audit #5
  cleared PR #61 at `bfaffc01` with 0 Blocker, 0 Critical, and 0 Major
  findings.
- Added source-bounded local Ollama answer generation for citation-grounded
  questions. AI output remains non-authoritative, cited, and
  staff-review-required; deterministic citation extraction remains the fallback.
- Added the React/Vite/TypeScript resident app at `/civiccode/app`, served by
  FastAPI and verified against live search and cited-answer API calls.
- Replaced the local hash-bucket search stand-in with configured Ollama
  embeddings and, in this follow-up, removed the CivicCode-local section
  embedding store so runtime semantic retrieval depends on shared CivicCore
  `document_chunks`. The search test suite now proves a zero-literal-overlap
  retrieval through local `nomic-embed-text` and a disposable
  `pgvector/pgvector:pg17` database when those runtimes are available.
- Added adversarial tests and evidence for bad input, missing/stale records,
  public/staff boundary failures, spoofed staff headers, unavailable Ollama
  fallback behavior, live Ollama, route inventory, staff browser QA,
  Docker/PostgreSQL installed-stack smoke, backup/restore, suite custom
  module-selection, and source-attributed Portland Title 13 municipal data
  import/search/Q&A proof.
- Updated package, verifier, documentation, and artifact version surfaces to
  `1.0.0` for the PR #61 release-gate-cleared CivicCode release.
- Kept earlier v0.1.x and v0.5.0 releases documented as historical
  pre-final-gate evidence rather than current release truth.

## [0.5.0 recovery update] - 2026-05-11

### Changed

- feat(deps): bump civiccore pin to v1.1.0 for the shared staff auth helper release.

## [0.5.0] - 2026-05-10

- Demoted the false v1.0.0 release label after the external CivicSuite audit found this module is a recovery/foundation module, not a canonical spec-complete v1 product.
- Preserved the useful recovery work while resetting the public package version to 0.5.0.
- Kept the CivicCore v1.0.0 wheel dependency and pinned it with SHA256 for release integrity.
- Supersedes the prior public v1.0.0 posture; do not treat v1.0.0 as production-ready or spec-complete.

All notable changes to CivicCode are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Added the first real CivicCode React/Vite/TypeScript frontend at `/civiccode/app`, served by FastAPI from the built package assets and wired to the live search and cited-answer APIs.
- Added source-bounded local Ollama answer generation for citation-grounded questions. AI output remains non-authoritative, cited, and staff-review-required; deterministic citation extraction remains the fallback when local Ollama is not configured.
- Added semantic retrieval metadata for public search plus a new Alembic migration for PostgreSQL pgvector embedding storage (`civiccode_0011_semantic_search`).
- Expanded browser QA to exercise the React app at desktop/mobile widths with live `/api/v1/civiccode/search` and `/api/v1/civiccode/questions/answer` network calls.
- Added a source-attributed Portland municipal-code fixture test that imports,
  searches, and answers against real adopted code text while keeping the
  evidence bounded as fixture proof rather than full city-corpus proof.

### Changed

- Updated `scripts/verify-release.sh` to run `npm ci`, TypeScript checks, and the Vite production build before browser QA.

## [0.6.0] - 2026-05-21

### Corrected

- Corrected the false v1.0.0 release label after the independent CivicSuite release-integrity audit found CivicCode does not meet the Section 2 FINISHED and SHIPPING bar.
- Set the honest current label to v0.6.0 and superseded the mistaken v1.0.0 posture without deleting the historical record.
- Current classification: functional-partial: real backend exists; the post-0.6.0 active branch is adding AI, React frontend, semantic search, installer/run evidence, and public-use gate proof before any future v1.0.0 claim.
- CivicCode must not be described as finished, shipping, city-ready, product-ready, or public-use ready until a future independent audit signs off against the full Section 2 gate.

### Fixed

- Fixed public search rendering for staff-approved related-material results so
  resident searches return cited navigation aids instead of a server error when
  the result points back to a source code section.
- Fixed records-ready export mobile wrapping for long citation/source metadata.
- Fixed the Docker demo staff smoke path by documenting and wiring the local
  Docker bridge CIDR into the trusted-header configuration.
- Fixed Docker/PostgreSQL backup-restore rehearsal targeting by adding
  `--compose-project-name` support to the verifier and wrapper scripts.

### Changed

- Marked the published `v1.0.0` label as recovered after PR #51 merged to
  `main` with green GitHub CI and local release-recovery evidence.
- Updated `scripts/verify-release.sh` to prefer native Unix `python3` before
  Windows launchers and to run CivicCore release-provenance reinstall checks in
  an isolated temporary virtualenv.
- Added current public/staff browser QA and clean Docker/PostgreSQL
  backup-restore proof under `docs/qa/` for the recovery pass.

## [1.0.0 false/recovered label] - 2026-05-07

### Changed

- Published the CivicCode v0.5.0 label after the active-module release lock
  scope read, CivicSuiteUnifiedSpec section 11 gap check, CivicCore v1.0.0
  alignment, durable operational-state runtime, staff/public browser QA
  evidence, and adversarial mock-city codifier validation path. The label is
  provisional during the later suite-wide release-recovery pass.
- Updated current release/version surfaces, release verification artifact names,
  and security/manual copy for the v1.0.0 gate while preserving v0.1.17 and
  v0.1.18 as historical pre-gate provenance references.
- Made the real Docker pgvector migration smoke skip with an actionable Docker
  Desktop instruction when the local Docker daemon is unavailable, while
  preserving the live migration proof when Docker is running.
- Added the downstream `civiccode.section_resolution.v1` contract for
  CivicZone, CivicLegal, CivicAccess, and CivicComms, plus adversarial
  legal-determination refusal coverage for that boundary.
- Added the resident `/civiccode/answer` cited-answer page and broadened public
  legal-determination refusal handling so property-specific prompts route to
  staff instead of rendering misleading search results.
- Added staff handoff resolution after codified adopted text is created,
  including durable handoff-resolution fields and warning suppression for
  resolved codifications.

### Added

- Reproducible Playwright staff browser QA harness for CI, covering staff access
  pages and mock-city staff workspaces with skip-link, main-region, console,
  horizontal-overflow, and actionable-fix readability checks.
- CO-4 Tier 1 retrofit ledger for `v0.1.17` and `v0.1.18`, marking both
  releases as historical pre-gate/no-attestation/do-not-promote without
  changing public release notes, tags, or assets.
- Sigstore attestation release workflow for future `v*` tags. The workflow
  builds wheel/sdist artifacts, writes schema-v1 `release-attestation.json`,
  signs it with GitHub Actions OIDC through cosign, verifies it before
  publication, and publishes the attestation bundle beside the release assets.
- CivicCore-backed release-provenance wrapper and attestation builder scripts so
  CivicCode consumes the shared suite provenance gate instead of maintaining a
  local tag-object verifier.
- Adversarial Sigstore release-provenance fixture suite covering missing schema,
  wrong workflow identity, artifact-hash mismatch, unexpected OIDC issuer,
  transparency-log outage, tag-target mismatch, workflow identity drift, and
  trust-root rotation.

### Changed

- Staff lifecycle write endpoints now require staff headers before mutating
  title, chapter, section, or section-version records.
- Staff headers are now validated through CivicCore trusted-header helpers and
  must arrive from loopback for local mock runs or
  `CIVICCODE_STAFF_TRUSTED_PROXY_CIDRS` in shared environments.
- Configured staff principal/role header names now flow through CivicCore's
  trusted-header validator instead of being blocked by default header prechecks.
- Browser QA now covers authenticated mobile empty and populated staff states,
  and the verify workflow runs on `sprint/**` branch pushes as well as `main`
  and pull requests.
- Release provenance workflows now install helper code and fixtures from the
  CivicCore `v1.0` tag instead of mutable `main`.
- Source distribution builds now exclude `.tmp-*`, cache, and generated
  interpreter artifact directories.
- Public section lookup warning payloads now expose resident-safe CivicClerk
  stale-code guidance without staff-only event IDs or failure details.
- Staff actionable-fix copy now renders as readable block callouts on mobile
  instead of long pill controls.
- Source distribution builds now include Docker demo files, and release
  workflows install the CivicCore v1.0 wheel used by the package.
- Updated the active CivicCore dependency and current install/provenance docs to
  the published CivicCore v1.0 baseline, `v1.0.0`, without changing
  CivicCode's v0.1.18 release status.
- Release provenance gate now treats Git tags as pointers and verifies the
  Sigstore attestation, bundle, exact workflow identity, artifact hashes, target
  commit, and target tree before publication.
- Release-signing runbook now documents the unachievable GitHub tag-signature
  target, the v0.1.17/v0.1.18 historical state, exact clean-machine
  verification commands, and the no-destructive-correction boundary.

## [0.1.18] - 2026-05-04

### Added

- Durable operational state storage for CivicClerk handoffs, local imports, and
  codifier sync runs when `CIVICCODE_SOURCE_REGISTRY_DB_URL` is configured,
  preserving retry queue records, replay records, and delta cursor records on
  the Docker/PostgreSQL product path.
- Staff operator API for `/api/v1/civiccode/staff/operational-state`, returning
  current handoff, import, and sync readiness from existing operational records
  with actionable fixes for missing state or queued retry work.
- Alembic revision `civiccode_0009_operational_state` for shared operational
  state records.

### Changed

- Failed handoffs/imports/syncs now leave durable operator recovery records, and
  every import/sync/handoff run leaves replay evidence without adding vendor
  credentials, outbound calls, live LLM calls, or auto-codification.

## [0.1.17] - 2026-05-04

### Added

- Durable codifier sync source storage when `CIVICCODE_SOURCE_REGISTRY_DB_URL`
  is configured, preserving source configuration, schedule, host-validation
  result, last attempted/successful run, next-run cursor, last import job,
  circuit-breaker state, and delta-plan history across process restarts.
- Alembic revision `civiccode_0008_codifier_sync` for Docker/PostgreSQL
  codifier sync source and delta-plan records.
- Operations runbook for the rare GitHub PR merge/close `502` path, including
  commit-SHA, tag, and release verification steps before manual closure.

### Changed

- Staff codifier sync list and run endpoints now read source state from the
  configured database on the Docker/PostgreSQL product path while preserving the
  in-memory store for lightweight local mode.

## [0.1.16] - 2026-05-04

### Added

- Durable local import job storage when `CIVICCODE_SOURCE_REGISTRY_DB_URL` is
  configured, preserving job status, counts, provenance, failure details,
  source IDs, and completion timestamps across process restarts.
- Alembic revision `civiccode_0007_import_jobs` for Docker/PostgreSQL import
  job records.

### Changed

- Staff import list, detail, provenance, retry, and codifier-sync paths now read
  import jobs from the configured database on the Docker/PostgreSQL product
  path while preserving the in-memory store for lightweight local mode.

## [0.1.15] - 2026-05-04

### Added

- Durable CivicClerk ordinance handoff and handoff audit-event storage when
  `CIVICCODE_SOURCE_REGISTRY_DB_URL` is configured.
- Alembic revision `civiccode_0006_handoffs` for Docker/PostgreSQL handoff
  records and handoff audit-event records.

### Changed

- CivicClerk ordinance/adoption handoff intake now survives process restarts on
  the Docker/PostgreSQL product path while preserving the in-memory store for
  lightweight local mode.
- Affected-section warning lists now read handoff records in created-time order
  instead of depending on memory insertion order.

## [0.1.14] - 2026-05-04

### Added

- Durable staff interpretation-note and plain-language summary storage when
  `CIVICCODE_SOURCE_REGISTRY_DB_URL` is configured.
- Alembic revision `civiccode_0005_staff_summaries` for staff notes, staff
  workbench audit events, summary records, and summary audit events.

### Changed

- Staff note creation, summary draft creation, summary approval, and their audit
  event listings now survive process restarts on the Docker/PostgreSQL product
  path while preserving the in-memory store for lightweight local mode.

## [0.1.13] - 2026-05-04

### Added

- Durable section/version lifecycle storage for title, chapter, section, and
  section-version records when `CIVICCODE_SOURCE_REGISTRY_DB_URL` is configured.
- Alembic revision `civiccode_0004_section_lifecycle` for the Docker/PostgreSQL
  product path.

### Changed

- CivicCode's Docker/PostgreSQL path now keeps adopted code structure and
  current version flags after process restarts instead of relying only on demo
  reseeding.

## [0.1.12] - 2026-05-04

### Added

- Durable `popular_question_records` storage for staff-approved resident
  discovery aids when `CIVICCODE_SOURCE_REGISTRY_DB_URL` is configured.
- Alembic revision `civiccode_0003_popular_questions` for the Docker/PostgreSQL
  product path, with migration tests that verify the new head revision and
  restored table set.

### Changed

- Popular-question creation and public listing now use the configured database
  repository on the Docker path while preserving the in-memory store for
  lightweight local mode.

## [0.1.11] - 2026-05-03

### Added

- Staff-approved popular-question discovery aids that link only to cited adopted
  code and publish as public navigation aids, not legal determinations.
- Public related-material endpoint and section-page rendering for explicit
  public cross-references without exposing staff-only notes.
- City of Brookfield demo seed popular question and related-material references
  so the Docker demo shows the resident discovery workflow immediately.

### Changed

- Public lookup home and section pages now include actionable empty states for
  popular questions and related materials.

## [0.1.10] - 2026-05-03

### Added

- Docker/PostgreSQL backup-restore rehearsal helper for the Compose product
  path. The helper runs `pg_dump`, restores into a temporary database, verifies
  restored application tables, writes a manifest with checksum, and drops the
  temporary restore database by default.
- Windows PowerShell and Bash launchers for repeatable operator rehearsal:
  `scripts/start_docker_backup_restore_rehearsal.ps1` and
  `scripts/start_docker_backup_restore_rehearsal.sh`.

## [0.1.9] - 2026-05-03

### Added

- Docker Compose product path with PostgreSQL 17 plus pgvector, migration
  startup, health checks, source-registry persistence, and opt-in City of
  Brookfield demo seed data through `CIVICCODE_DEMO_SEED=1`.
- `Dockerfile`, `docker-compose.yml`, `docker.env.example`, and
  `scripts/docker-demo-smoke.sh` for a repeatable local product demo.
- Runtime demo seed middleware that populates public lookup, staff code
  workspace, approved-summary, staff-note, and CivicClerk handoff warning data
  without outbound vendor calls.

### Changed

- Promoted Alembic, SQLAlchemy, and `psycopg2-binary` to runtime dependencies so
  the packaged Docker app can run migrations and PostgreSQL-backed source
  registry persistence outside the dev extra.

## [0.1.8] - 2026-05-03

### Changed

- Aligned CivicCode with the published `civiccore v0.22.0` release wheel.
- Reused CivicCore's shared sync source-list health projection in codifier sync
  source responses while preserving the existing CivicCode `operator_status`
  shape for current staff clients.
- Bumped release verification and current-facing docs to CivicCode v0.1.8.

## [0.1.7] - 2026-05-03

### Added

- Staff-controlled codifier live-sync foundation with readiness configuration,
  schedule validation, SSRF-safe host checks, delta request planning, local
  payload sync runs, and CivicCore circuit-breaker health copy.
- Staff API endpoints under `/api/v1/civiccode/staff/sync/codifier-sources`
  for configuring codifier sources, listing operator health, and running one
  local payload through the existing import path.
- Focused tests for cron/host validation, delta cursors, circuit breaker
  behavior, staff authorization, and the no-automatic-codification boundary.

### Changed

- Bumped release verification and current-facing docs to CivicCode v0.1.7.
- Updated product copy from "live codifier sync not available" to the current
  truth: a sync foundation is available, but bundled vendor credentials,
  automatic ordinance codification, live LLM calls, and legal determinations
  remain out of scope.

## [0.1.6] - 2026-05-03

### Added

- Reusable mock-city codifier contract suite covering Municode, American Legal
  Publishing, Code Publishing Company, and General Code source interfaces.
- `scripts/run_mock_city_environment_suite.py` writes a secret-free JSON report
  and verifies CivicCode codifier imports without outbound vendor calls.
- Mock-city environment report reuses CivicCore municipal IdP and
  backup-retention contracts so future modules can follow the same pattern.

### Changed

- Bumped release verification and current-facing docs to CivicCode v0.1.6.
- Aligned CivicCode with the published `civiccore v0.21.0` wheel so the
  reusable mock-city contracts resolve from a published CivicCore release.

## [0.1.5] - 2026-05-02

### Added

- Staff code lifecycle workspace at `/staff/code` with access-required, empty,
  readiness-snapshot, section-card, draft-summary, and pending-codification states.
- Staff workspace payload now surfaces current adopted version counts, source
  readiness, plain-language summary blockers, staff note counts, and CivicClerk
  handoff warnings in one operator-facing page.

### Changed

- Bumped release verification and current-facing docs to CivicCode v0.1.5.
- Added store read helpers for staff workspace aggregation without exposing
  staff-only data on public endpoints.

## [0.1.4] - 2026-05-02

### Changed

- Corrected the current-release user manual status so the packaged documentation matches the staff source registry workspace release line.

## [0.1.3] - 2026-05-02

### Added

- Staff source registry workspace at `/staff/sources` with empty, access-required,
  source-card, stale-source, and failed-source states for code administrators.

### Changed

- Staff source create, transition, list, and detail APIs now require the trusted
  staff header seam before exposing staff-only source notes or mutating the
  registry.

## [0.1.2] - 2026-05-02

### Added

- Production-depth source registry persistence slice with
  `CIVICCODE_SOURCE_REGISTRY_DB_URL`, durable source metadata/status/staff-note
  records, and Alembic revision `civiccode_0002_sources`.

### Changed

- Align CivicCode's CivicCore dependency, CI install wheel, documentation, health contract, and release gate with the published `civiccore v0.19.0` release wheel so the module can join the current CivicSuite shared-platform line before the next product-depth slice.

## [0.1.1] - 2026-04-28

### Changed

- Align CivicCode's exact CivicCore dependency, CI install wheel, documentation, health contract, and release gate with `civiccore==0.3.0`.

## [0.1.0] - 2026-04-27

### Added

- Initial scaffold for the future `CivicSuite/civiccode` module.
- Professional documentation baseline, landing page, contribution/support/security docs, issue templates, PR template, and docs verification gate.
- Milestone 0 operating contract in `AGENTS.md`.
- Milestone 0 reconciliation report, ADR queue, milestone plan, and CivicCore placeholder-import CI gate.
- CivicCode implementation plan broken into PR-sized runtime chunks from foundation through v0.1.0 release.
- CivicCode implementation plan cross-checked against the original Module Catalog v1 extract, preserving codifier imports, resident/staff Q&A, administrative materials, popular questions, conflict detection, and CivicClerk handoff requirements under the current Apache 2.0 suite decision.
- Milestone 1 runtime foundation: installable package, FastAPI app shell, `/` and `/health` endpoints, exact `civiccore==0.2.0` dependency pin, pytest CI gate, and documentation updated to state that code-answer behavior is not available yet.
- Milestone 2 canonical schema foundation: CivicCore-first Alembic migration chain, separate `alembic_version_civiccode` table, schema-aware migration guard, canonical SQLAlchemy metadata, and ten `civiccode.*` foundation tables.
- Milestone 3 official source registry foundation: source vocabulary endpoint, source create/list/read/transition APIs, official-source provenance enforcement, public/staff source visibility split, source-state matrix, and actionable stale/failed-source messages.
- Milestone 4 section/version foundation: title/chapter/section creation APIs, immutable section-version records, current and historical section lookup, related non-code material references, pending-law refusal, overlapping-date ambiguity checks, and amendment history.
- Milestone 5 search and permalink foundation: public-safe search endpoint, exact section-number lookup through search, phrase search over adopted text, related public material result types, actionable empty search state, stable section permalink endpoint, and leakage guardrails.
- Milestone 6 citation contract foundation: deterministic citation object, section/version/source/effective-date fields, canonical URL, information-not-determination classification, and structured refusals for missing, stale, or contradictory source situations.
- Milestone 7 citation-grounded Q&A foundation: deterministic question-answer endpoint, exact citation requirement, single-result search resolution, legal-determination refusal, uncited-question refusal, stale-source refusal, and `llm_provider=not_used` guardrail.
- Milestone 8 staff workbench foundation: staff-only interpretation-note endpoints, trusted staff header seam, staff Q&A context with `staff_only_do_not_publish`, staff workbench audit events, and public-surface leakage tests for lookup, search, and Q&A.
- Milestone 9 plain-language summaries foundation: staff draft/approval workflow, approved-only public summary endpoint, non-authoritative `non_authoritative_explanation` labeling, authoritative code text kept visible beside summaries, adopted-version guardrails, and summary audit events.
- Milestone 10 CivicClerk handoff foundation: ordinance/adoption event intake, meeting/agenda provenance preservation, pending codification warnings on affected lookups, likely conflict detection, failed-handoff visibility, and guardrails proving pending ordinance language is not adopted law.
- Milestone 11 public code lookup surface: resident-facing `/civiccode` "Read code" pages for search, section detail, citations, approved summaries, pending codification warnings, stale-source warnings, actionable empty states, and legal-advice refusal routing.
- Milestone 12 import and connector hardening: staff-only local import jobs for CSV/file-drop bundles and official HTML extract fixtures, idempotent re-import behavior, actionable failed-import records, retry support, provenance report endpoints, imported-tree verification, and no required outbound dependency for local import.
- Milestone 13 accessibility and export hardening: records-ready export API and HTML page for adopted sections, source/version/citation/retrieval metadata in export payloads, semantic headings and labels, print-friendly output, stale-source export refusals, and CivicAccess integration notes without a shipped CivicAccess runtime dependency.

### Not Shipped

- No live LLM calls.
- No legal-determination behavior.
- No bundled vendor credentials, live LLM calls, Redis/Celery worker
  requirement, CivicAccess runtime dependency, legal determinations, or
  automatic ordinance codification yet; staff notes remain staff-only.
