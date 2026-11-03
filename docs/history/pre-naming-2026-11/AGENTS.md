<a id="civiccode-operating-contract"></a>

# Townlight Code Operating Contract

This repository implements the future Townlight Code module: municipal code and
ordinance access for Townlight.

## Priority order

1. User experience.
2. Documentation, QA, and tests.
3. Code.

## Current state

This repo has completed Milestone 13 accessibility and export hardening. It has an
installable Python package, a FastAPI app shell, `/` and `/health`, an exact
published `civiccore v1.0.0` release-wheel dependency, canonical SQLAlchemy metadata, and Alembic
migrations for the `civiccode` schema. It also has staff/public source registry
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

- `townlight/townlight/docs/CivicSuiteUnifiedSpec.md`, especially section 11.
- `townlight/townlight/docs/roadmap/civiccode-next-module-plan.md`.
- `townlight/townlight/specs/01_catalog.md`, Townlight Code section.
- Suite ADRs in `townlight/townlight/docs/architecture/`.

<a id="civiccore-placeholder-warning"></a>

## Townlight Core placeholder warning

Do not import from planned Townlight Core placeholder packages unless that package
has shipped in a versioned Townlight Core release. Placeholder imports can appear to
work because empty packages exist, but relying on them is a defect.

<a id="civiccode-non-negotiables"></a>

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

## Milestones

Milestone 0 is reconciliation only:

1. Read upstream spec and ADRs.
2. Add `docs/RECONCILIATION.md`.
3. Queue ADRs for open questions.
4. Add `docs/MILESTONES.md`.
5. Keep docs verification green.
6. Do not add runtime code.

Milestone 14 implementation has landed. Townlight Code v0.5.0 is a published label
under suite-wide release-recovery review, not a fresh product-ready claim until
the recovery gates re-earn that status. Townlight Core v1.0.0 dependency alignment,
downstream section resolution, cited resident Q&A, and Townlight Meetings handoff
codification closeout are the current release boundary.

## Prohibitions

- Do not promote planned behavior as shipped.
- Do not create a second source of truth for the suite spec.
- Do not import from unreleased Townlight Core placeholders.
- Do not add frontend code without browser QA evidence.
- Do not say done without verification output.
- Do not edit umbrella compatibility docs from this repo.
