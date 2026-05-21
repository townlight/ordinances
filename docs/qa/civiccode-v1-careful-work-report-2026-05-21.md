# CivicCode v1.0.0 Careful Work Report

Date: 2026-05-21

## Scope

Promote CivicCode from the v0.5.0 recovery label to the active v1.0.0 public-use
module release line.

## Careful-Work Checklist

1. Callers/consumers read: `CivicSuiteUnifiedSpec.md`, `ACTIVE_RELEASE_QUEUE.md`,
   CivicCode README/manual/changelog/security/docs index, `scripts/verify-release.sh`,
   release-recovery docs, route table, tests, and suite installer metadata.
2. Runtime context traced: FastAPI app exposes resident routes, staff routes,
   API routes, Docker Compose runtime, PostgreSQL migrations, and backup/restore
   rehearsal helper.
3. Pattern search performed: version, release-truth, CivicCore pin, recovery,
   staff, legal-advice, citation, CivicClerk handoff, and public-use markers.
4. Data contract changed: package/version contract moved from `0.5.0` to
   `1.0.0`; `/health` now reports CivicCode `1.0.0`; build artifacts are
   `civiccode-1.0.0`.
5. Blast radius: release truth, tests that assert version payloads, docs,
   security policy, package metadata, release verifier, Docker package build,
   and browser QA evidence.
6. Changed files re-read after editing: version surfaces, release verifier,
   current QA summary, and tests.
7. Full path narrated: `pyproject.toml` and `civiccode/__init__.py` feed the app
   version; `/health` exposes it; tests assert it; `scripts/verify-release.sh`
   builds and checks `civiccode-1.0.0` artifacts.
8. New state consumed/rendered: `1.0.0` is consumed by tests, rendered in
   `/health`, reflected in docs/security/manual/index surfaces, and built into
   release artifacts.
9. Self-audit: local verifier, browser QA, Docker smoke, and backup/restore were
   rerun; the first Docker attempt failed due an occupied host port and was
   rerun on host port `18052` with successful smoke and restore proof.

## Verification

- `bash scripts/verify-release.sh` passed after version/test updates.
- `node scripts/browser-staff-surfaces-qa.cjs` passed across 16 staff states.
- Inline Playwright resident matrix passed across 10 public states.
- `docker compose -p civiccode_v1_debug up -d --build` passed with
  `CIVICCODE_PORT=18052`.
- `CIVICCODE_SMOKE_BASE_URL=http://127.0.0.1:18052 bash scripts/docker-demo-smoke.sh`
  passed.
- `python scripts/check_docker_backup_restore_rehearsal.py --run-id civiccode-v1-public-use-verify-3 --compose-project-name civiccode_v1_debug --strict`
  passed.
