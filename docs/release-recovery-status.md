# Townlight Code Release Recovery Status

Date: 2026-05-09
Repo: `Townlight/townlight_code`

## Current Verdict

`v1.0.0` exists as a published package/release label. The release-recovery
branch was reviewed through PR #51, merged to `main`, and confirmed with green
GitHub CI after merge. Local runtime, browser, Docker, documentation, and
release verification gates have also been rerun in the recovery workspace.

## Recovery Gates

| Gate | Current status | Evidence |
| --- | --- | --- |
| Public product-ready claim recovery | Passing on main | PR #51 merged to `main`; GitHub `verify-docs` passed after merge, and current docs point to this recovery status. |
| Runtime install proof | Passing on main | `scripts/verify-release.sh` builds artifacts and runs Townlight Core release-provenance reinstall checks in an isolated temporary virtualenv. |
| Native WSL/Linux proof | Passing on main | WSL run selected `.venv-wsl/bin/python3`, reported platform `linux`, and completed `VERIFY-RELEASE: PASSED`. |
| Security scan | Passing on main | Tracked-file secret scan returned no matches after the staff-note test marker rename. |
| Docs-source enforcement | Passing on main | `scripts/verify-docs.sh` blocks stale current-product-line claims; regression tests cover the gate. |
| Mock-vs-production labeling | Passing on main | Existing docs distinguish local mocks, codifier sync foundation, no live LLM, no legal advice, and no automatic codification. |
| Browser/user-flow QA | Passing on main | Fresh browser QA checked 10 public resident scenarios and 16 staff scenarios with no console errors, page errors, or horizontal overflow; see `docs/qa/townlight_code-current-public-staff-browser-qa.md`. |
| Docker demo runtime | Passing on main | Clean Compose project `townlight_code_recovery_verify` built the image, started PostgreSQL, served the seeded app, and passed `scripts/docker-demo-smoke.sh`. |
| Docker/PostgreSQL backup-restore | Passing on main | Clean Compose project `townlight_code_recovery_verify` passed `pg_dump`, temporary restore database creation, `pg_restore`, restored application table verification, and cleanup. |
| GitHub CI | Passing on main | PR #51 `verify-docs` check passed before merge; merge commit `aead64d4e704bf2d061f1d88f544752b06ac62f9` is on `main`. |

## Current Evidence

- Product test suite: `192 passed`.
- Full release gate: `VERIFY-RELEASE: PASSED`, including version surfaces,
  product tests, isolated Townlight Core release-provenance test, docs gate,
  placeholder import gate, ruff, build artifacts, and SHA256 generation.
- Browser QA: 10 public resident scenarios and 16 staff scenarios passed with
  no console messages, no page errors, no horizontal overflow, and keyboard
  focus reaching skip links.
- Docker proof: clean Compose smoke and backup/restore rehearsal passed for
  `townlight_code_recovery_verify`.

## Sign-Off Boundary

This recovery status does not rewrite the existing `1.0.0` package version or
pretend the original tag was created after these recovery checks. It changes
the public posture: the recovered Townlight Code `v1.0.0` code path is verified on
`main` through PR #51, local release gates, browser QA, Docker smoke, and
backup/restore rehearsal.
