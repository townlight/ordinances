<a id="townlight_code-operating-contract"></a>

# Townlight Code Operating Contract

## Governing contract and candidate identity

Scott's bounded completion contract governs. Legacy skills, automatic delegation,
milestone/review loops and generic extra gates require explicit invocation.
Preserve actual product requirements, required CI/release checks, security/data
safeguards and installed acceptance. Reuse unaffected evidence with its limits.

Current distribution: `townlight-code` 1.0.9; principal import:
`townlight_code`. Shared dependency: `townlight-core==1.3.0.dev2`. Use the exact
coordinated source pins and local candidate wheels in the README; never fabricate
renamed historical release URLs. Source tests do not establish installed acceptance
or publication. The original [agent contract](docs/history/pre-naming-2026-11/AGENTS.md)
is retained as history, not current session authorization.

The candidate supports fresh branded databases and fresh profiles only. Preserve
existing data and refuse unmarked legacy initialization; no in-place upgrade or
old import shim is provided. The sole approved old active identifier is
`%LOCALAPPDATA%\CivicSuite` for that profile path only. Other retained old active
identifiers require Scott's approval in the single exception registry. Preserve
historical identities, third-party attribution and standalone CivicCast.

This repository implements Townlight Code: municipal code and
ordinance access for Townlight.

## Priority order

1. User experience.
2. Documentation, QA, and tests.
3. Code.

## Current state

The prepared candidate includes accessibility and export hardening. It has an
installable Python package, a FastAPI app shell, `/` and `/health`, an exact
local `townlight-core==1.3.0.dev2` candidate dependency, canonical SQLAlchemy metadata, and Alembic
migrations for the `townlight_code` schema. It also has staff/public source registry
APIs, title/chapter/section/version lifecycle APIs, public-safe search, stable
section permalinks, deterministic citation/refusal objects, and a deterministic
citation-grounded Q&A harness that does not use live LLM calls. It also has
staff-only interpretation-note endpoints, staff Q&A context marked
`staff_only_do_not_publish`, staff workbench audit events, and staff-approved
plain-language summaries labeled `non_authoritative_explanation`. It also has
Townlight Meetings ordinance/adoption handoff intake with pending codification warnings
and likely conflict signals. It also has staff-only local import jobs for
CSV/file-drop bundles and official HTML extract fixtures, idempotent re-import,
failed-import visibility, retry, imported-tree verification, and provenance
report endpoints. It also has records-ready JSON and HTML exports for adopted
sections with source, version, citation, retrieval, accessibility, and
legal-boundary metadata.

Do not promote Townlight Code as a legal-advice product. Live LLM and live codifier
sync workflows remain planned until their milestones land. Staff notes remain
staff-only. Plain-language summaries are not law. Pending ordinance language is
not adopted law and handoff intake is not automatic ordinance codification.

## Upstream truth

Read these before any milestone work:

- `townlight/townlight/docs/TownlightUnifiedSpec.md`, especially section 11.
- `townlight/townlight/docs/roadmap/townlight_code-next-module-plan.md`.
- `townlight/townlight/specs/01_catalog.md`, Townlight Code section.
- Suite ADRs in `townlight/townlight/docs/architecture/`.

<a id="townlight_core-placeholder-warning"></a>

## Core dependency boundary

Inspect the pinned implementation rather than assuming historical placeholder
status. Keep the existing dependency-boundary checker and do not add unused
consumers. Empty or unavailable interfaces must still fail the owning checks.

<a id="townlight_code-non-negotiables"></a>

## Townlight Code non-negotiables

These must become tests before runtime behavior ships:

- Exact citations: every code answer cites title/chapter/section/subsection.
- No legal advice: resident-facing answers route legal interpretation to staff.
- Source precedence: official codifier/source text beats summaries and notes.
- Version context: answers know the effective date of the section being cited.
- Ambiguity refusal: missing, stale, or contradictory source text causes a
  helpful refusal, not a guess.
- Plain-language boundary: summaries are labeled non-authoritative.
- Audit trail: imports, summaries, answers, and section changes are recorded.
- Air-gap posture: local runtime only; no required outbound calls.

## Current completion boundary

The candidate retains source/version resolution, cited resident Q&A, staff-only
notes and Meetings adoption/codification handoff contracts. Complete the approved
naming change and affected checks; installed Code → Meetings proposal/adoption
acceptance remains required for the coordinated Windows candidate. Older milestone
labels are historical context, not a new ready/released claim.

## Prohibitions

- Do not promote planned behavior as shipped.
- Do not create a second source of truth for the suite spec.
- Do not import from unreleased Townlight Core placeholders.
- Do not add frontend code without browser QA evidence.
- Do not say done without verification output.
- Do not edit umbrella compatibility docs from this repo.
