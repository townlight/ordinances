<a id="civiccode-milestones"></a>

# Townlight Code Milestones

This plan is scaffolded from the Townlight unified spec, the Townlight Code
roadmap, and suite ADRs. Runtime code starts only after Milestone 0 is reviewed.

For PR-sized execution details, see
[`docs/IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md).

## Milestone 0 - Reconciliation And Gates

Acceptance criteria:

- Upstream spec, roadmap, catalog, and suite ADRs read.
- `docs/RECONCILIATION.md` records drift and open questions.
- ADR queue exists under `docs/adr/`.
- Docs verification and placeholder-import gates are wired into CI.
- No runtime code exists.

Expected tests/gates: docs gate, placeholder-import gate.

## Milestone 1 - Runtime Foundation

Acceptance criteria:

- FastAPI app shell only.
- `civiccore` dependency pinned to the approved version.
- Health/root endpoints say scaffold/runtime-foundation truth plainly.
- No code-answer behavior yet.

Expected tests/gates: unit/API tests for health/root, docs gate, placeholder gate.

## Milestone 2 - Canonical Schema And Migrations

Acceptance criteria:

- Schema follows ADR-0002 shared Base rule.
- Migrations run after Townlight Core migrations.
- Tables are namespaced under `civiccode`.
- Real Postgres migration smoke test passes.

Expected tests/gates: migration integration, idempotency, docs gate.

## Milestone 3 - Code Source Registry

Acceptance criteria:

- Staff can register official source metadata.
- Source records include publisher, URL/file, retrieved timestamp, and status.
- Missing/stale source states have actionable messages.

Expected tests/gates: API tests, source-state matrix, docs/browser QA if UI exists.

## Milestone 4 - Section Model And Versioning

Acceptance criteria:

- Titles, chapters, sections, subsections, and section versions exist.
- Effective-date lookup is deterministic.
- Historical lookup refuses when date context is missing.

Expected tests/gates: unit matrix, API tests, migration tests.

## Milestone 5 - Search And Section Permalinks

Acceptance criteria:

- Users can search by text and section number.
- Every section has a stable permalink.
- Empty and no-result states are actionable.

Expected tests/gates: API/search tests, browser QA if UI exists.

## Milestone 6 - Citation-Grounded Q&A

Acceptance criteria:

- Every answer cites exact code sections.
- Missing, stale, or ambiguous sources produce helpful refusals.
- Answers never present legal interpretation as final advice.

Expected tests/gates: prompt evals, refusal matrix, no-live-provider-call checks.

## Milestone 7 - Plain-Language Summaries

Acceptance criteria:

- Summaries are explicitly non-authoritative.
- Staff approval is required before publishing.
- Original authoritative text remains visible.

Expected tests/gates: approval workflow tests, copy audit, browser QA.

## Milestone 8 - Staff Interpretation Notes

Acceptance criteria:

- Staff-only notes are access-controlled.
- Public endpoints never leak staff-only content.
- Retention/audit behavior matches ADR decision.

Expected tests/gates: ACL matrix, leakage tests, audit-log tests.

<a id="milestone-9---civicclerk-handoff-intake"></a>

## Milestone 9 - Townlight Meetings Handoff Intake

Acceptance criteria:

- Townlight Code can receive ordinance/adoption events using the accepted contract.
- Pending ordinance language is distinguished from adopted law.
- Failed/stale handoffs are visible and actionable.

Expected tests/gates: contract tests, integration tests, failure-state tests.

## Milestone 11 - Public Code Lookup Surface

Acceptance criteria:

- Public users can find sections and citations.
- Legal-disclaimer/refusal language is visible.
- Desktop/mobile accessibility evidence is captured.

Expected tests/gates: browser QA, accessibility checks, API tests.

## Milestone 12 - Import/Connector Hardening

Acceptance criteria:

- Local CSV/file-drop and official HTML extract fixtures can import source,
  title, chapter, section, and version records.
- Import failures are recoverable and visible through staff APIs.
- Re-importing the same local bundle is idempotent.
- Provenance reports expose source metadata, fixture checksum, and import mode.
- No outbound runtime dependency is required for local import.

Expected tests/gates: connector tests, import fixture tests, air-gap checks.

## Milestone 13 - Accessibility And Export Hardening

Acceptance criteria:

- Public pages and exports meet Townlight Access-ready accessibility expectations.
- Exported code/section packages preserve citation and source provenance.
- Browser QA covers desktop/mobile, focus, contrast, and copy states.

Expected tests/gates: accessibility checks, browser QA, export tests.

## Milestone 14 - v0.1.0 Release

Acceptance criteria:

- All version surfaces synchronized.
- README, manual, landing page, changelog, and compatibility docs are current.
- Release artifacts build and publish.
- Townlight compatibility matrix PR is merged after release.

Expected tests/gates: release verification, docs verification, browser QA,
audit-lite review.
