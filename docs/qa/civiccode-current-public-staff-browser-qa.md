# CivicCode v1.0.0 Public And Staff Browser QA

Date: 2026-05-21

## Scope

Fresh browser verification for the CivicCode v1.0.0 public-use release
candidate after promoting candidate package truth from v0.5.0:

- public resident lookup/search/answer/detail/export surfaces,
- staff code/source/import/sync surfaces,
- access-required, empty, populated, cited-answer, refusal, and export states.

## Public Resident Surfaces

Target: `node scripts/browser-public-surfaces-qa.cjs`, which starts local
`uvicorn civiccode.main:app` with `CIVICCODE_DEMO_SEED=true`.

Scenarios checked:

- `/civiccode` at desktop and mobile widths.
- `/civiccode/search` empty-search state at mobile width.
- `/civiccode/search?q=backyard%20chickens` at desktop width.
- `/civiccode/answer?q=What%20does%20section%206.12.040%20say%3F&section_number=6.12.040` at desktop and mobile widths.
- `/civiccode/search?q=Should%20I%20sue%20my%20neighbor%20over%20chickens%3F` at mobile width.
- `/civiccode/sections/6.12.040` at desktop and mobile widths.
- `/civiccode/sections/6.12.040/export` at mobile width.

Result: PASS.

Evidence:

- HTTP status matched expected status for all 10 scenarios.
- Each page rendered exactly one `main#content`.
- Each page exposed a skip link and keyboard focus reached it with Tab.
- Browser console warnings/errors: 0.
- Page errors: 0.
- Horizontal overflow: 0 scenarios.
- Screenshots refreshed under `docs/qa/current-public-browser-qa/`.

## Staff Operator Surfaces

Target: `node scripts/browser-staff-surfaces-qa.cjs` with fresh local servers.

Scenarios checked:

- Staff code workspace access-required and empty mobile states.
- Staff source registry access-required and empty mobile states.
- Staff import ledger access-required and empty mobile states.
- Staff sync health access-required and empty mobile states.
- Populated staff code workspace at desktop and mobile widths.
- Populated staff source registry at desktop and mobile widths.
- Populated staff import ledger at desktop and mobile widths.
- Populated staff sync health at desktop and mobile widths.

Result: PASS.

Evidence:

- HTTP status matched expected status for all 16 scenarios.
- Each page rendered exactly one `main#content`.
- Each page exposed a skip link and keyboard focus reached it with Tab.
- Browser console warnings/errors: 0.
- Page errors: 0.
- Horizontal overflow: 0 scenarios.
- Screenshots refreshed under `docs/qa/current-staff-browser-qa/`.

## Verification Commands

- `python -m pytest -q tests/test_milestone_11_public_lookup_surface.py tests/test_milestone_13_accessibility_export_hardening.py`
- `python -m pytest -q tests/test_docker_demo_runtime.py tests/test_docker_backup_restore_rehearsal_helper.py`
- `python -m pytest -q --ignore=tests/test_release_provenance_gate.py`
- `python -m ruff check .`
- `bash scripts/verify-docs.sh`
- `bash scripts/verify-release.sh`
- `CIVICCODE_BROWSER_QA_ARTIFACT_DIR=docs/qa/current-staff-browser-qa node scripts/browser-staff-surfaces-qa.cjs`
- `CIVICCODE_PUBLIC_BROWSER_QA_ARTIFACT_DIR=docs/qa/current-public-browser-qa node scripts/browser-public-surfaces-qa.cjs`
- `CIVICCODE_PORT=18052 docker compose -p civiccode_v1_debug up -d --build`
- `CIVICCODE_SMOKE_BASE_URL=http://127.0.0.1:18052 bash scripts/docker-demo-smoke.sh`
- `python scripts/check_docker_backup_restore_rehearsal.py --run-id civiccode-v1-public-use-verify-3 --compose-project-name civiccode_v1_debug --strict`
- `docker compose -p civiccode_v1_debug down -v`

All verification commands passed in the current session.

## Docker/PostgreSQL Recovery Proof

The clean Docker proof used a separate Compose project, `civiccode_v1_debug`,
and removed that project's containers, network, and volume after verification.
Port `18052` was used because another local stack already owned host port
`8000`; the container still listened on its normal internal port `8000`.

Results:

- Docker image build: PASS.
- PostgreSQL health dependency: PASS.
- Seeded public lookup smoke: PASS.
- Seeded staff workspace smoke: PASS.
- `pg_dump` backup: PASS.
- Temporary restore database creation: PASS.
- `pg_restore` restore: PASS.
- Restored application table verification: PASS.
- Temporary restore database cleanup: PASS.

The rehearsal manifest and restore verification were written under
`.docker-backup-restore-rehearsal/civiccode-v1-public-use-verify-3/`.
