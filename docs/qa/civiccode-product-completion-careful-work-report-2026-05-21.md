# CivicCode Careful Work Report

Date: 2026-05-21

## Scope

Record careful-work evidence from the earlier CivicCode completion attempt and
the current v0.6.0 active branch. CivicCode stays at v0.6.0 until the complete
release gate and independent audit sign-off are complete.

## Careful-Work Checklist

1. Callers/consumers read: `CivicSuiteUnifiedSpec.md`, `ACTIVE_RELEASE_QUEUE.md`,
   CivicCode README/manual/changelog/security/docs index, `scripts/verify-release.sh`,
   release-recovery docs, route table, tests, and suite installer metadata.
2. Runtime context traced: FastAPI app exposes resident routes, staff routes,
   API routes, Docker Compose runtime, PostgreSQL migrations, and backup/restore
   rehearsal helper.
3. Pattern search performed: version, release-truth, CivicCore pin, recovery,
   staff, legal-advice, citation, CivicClerk handoff, and public-use markers.
4. Data contract changed in the earlier attempt and was corrected back to the
   honest `0.6.0` label; `/health` now reports CivicCode `0.6.0`, and current
   build artifacts are `civiccode-0.6.0`.
5. Blast radius: release truth, tests that assert version payloads, docs,
   security policy, package metadata, release verifier, Docker package build,
   and browser QA evidence.
6. Changed files re-read after editing: version surfaces, release verifier,
   current QA summary, and tests.
7. Full path narrated: `pyproject.toml` and `civiccode/__init__.py` feed the app
   version; `/health` exposes it; tests assert it; `scripts/verify-release.sh`
   builds and checks `civiccode-0.6.0` artifacts.
8. New state consumed/rendered: `0.6.0` is consumed by tests, rendered in
   `/health`, reflected in docs/manual/index surfaces, and built into release
   artifacts.
9. Self-audit: local verifier, browser QA, Docker smoke, and backup/restore were
   rerun; the first Docker attempt failed due an occupied host port and was
   rerun on host port `18052` with successful smoke and restore proof. The
   staff-surface audit fix was later rerun on host port `18067`; the smoke
   proved forged staff headers on the published demo port return HTTP 403.

## Verification

- `bash scripts/verify-release.sh` passed after version/test updates.
- `node scripts/browser-staff-surfaces-qa.cjs` passed across 16 staff states.
- `scripts/browser-public-surfaces-qa.cjs` passed across 10 public states.
- `docker compose -p civiccode_product_completion_debug up -d --build` passed with
  `CIVICCODE_PORT=18052`.
- `CIVICCODE_SMOKE_BASE_URL=http://127.0.0.1:18052 bash scripts/docker-demo-smoke.sh`
  passed.
- `python scripts/check_docker_backup_restore_rehearsal.py --run-id civiccode-product-completion-verify-3 --compose-project-name civiccode_product_completion_debug --strict`
  passed.
- `CIVICCODE_SMOKE_BASE_URL=http://127.0.0.1:18067 bash scripts/docker-demo-smoke.sh`
  passed against project `civiccode_staff_surface_fix`, including the forged
  staff-header rejection check.
- `bash scripts/verify-release.sh` passed after the staff-surface fix with
  `207 passed` in the product test suite.
