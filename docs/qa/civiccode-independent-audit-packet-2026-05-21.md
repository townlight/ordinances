# CivicCode Independent Audit Packet - 2026-05-21

Status: request for independent audit review only. This is not release clearance.

## Scope Lock

- Active release lock: CivicCode only.
- Target: future v1.0.0 only after the full Definition of Done and independent audit.
- Current honest version: v0.6.0.
- Branch: `work/civiccode-product-completion`.
- Head at packet refresh: pending new commit after semantic search, data, and staff-surface audit fixes.
- Queued modules are not part of this work.

## Branch Changes Since `origin/main`

- `6523a62 feat: add civiccode local ai and react app foundation`
- `f72e790 test: add civiccode release proof evidence`
- `da7e10e docs: record civiccode suite installer selection proof`
- `054e87a docs: remove stale civiccode v1 overclaim wording`
- `d2bf477 test: add civiccode real municipal data proof`

## Evidence Map

| Gate area | Evidence |
|---|---|
| Local AI | `docs/qa/civiccode-live-ollama-proof-2026-05-21/summary.md`; `ollama-answer-proof.json` shows local Ollama answer, cited output, staff-review requirement, and non-authoritative boundary. |
| Frontend | React/Vite/TypeScript app served at `/civiccode/app`; `docs/qa/civiccode-react-app-browser-qa-2026-05-21/summary.md`; full verifier browser QA includes live API search/answer scenarios. |
| Semantic search / pgvector | `civiccode/semantic_search.py`; migration `civiccode_0011_semantic_search.py`; `tests/test_milestone_5_search_permalinks.py` proves configured Ollama embeddings, persisted pgvector rows, live pgvector ranking, and zero-literal-overlap retrieval when the local runtimes are available. |
| Real municipal data | `civiccode/real_municipal_fixtures.py`; `civiccode/fixtures/portland/code/`; `tests/test_real_municipal_data_fixture.py`; Portland Title 13 proof covers two official chapter sources, five adopted sections, and package-local provenance artifacts. |
| Staff/public routes | `docs/qa/civiccode-route-inventory-2026-05-21/summary.md` and `routes.json`; 55 routes inventoried. |
| Staff-surface protection | `docker-compose.yml` binds the published API port to loopback and trusts only loopback by default; `scripts/docker-demo-smoke.sh` now verifies forged `X-CivicCode-*` staff headers on the published demo port fail with HTTP 403; `tests/test_release_adversarial_boundaries.py` covers the shipped Compose trust boundary. |
| Staff browser QA | `docs/qa/civiccode-staff-browser-qa-2026-05-21/summary.md`; 16 staff scenarios recorded. |
| Installed stack | `docs/qa/civiccode-installed-stack-proof-2026-05-21/summary.md`; successful `*-3` logs cover Docker/PostgreSQL smoke and backup/restore rehearsal. |
| Suite installer selection | `docs/qa/civiccode-suite-installer-selection-proof-2026-05-21/summary.md`; custom profile resolves CivicCore + CivicClerk + CivicCode and `verify-installer-plan.py` passed. |
| Adversarial behavior | `tests/test_release_adversarial_boundaries.py`; covers bad input, missing/stale records, public/staff boundary, spoofed staff headers, unavailable Ollama fallback, and no auto-determination behavior. |
| Documentation honesty | README, CHANGELOG, USER-MANUAL, docs index, and QA docs keep CivicCode at v0.6.0 and state that release clearance depends on independent audit. |

## Verification Run

Command:

```powershell
bash scripts/verify-release.sh
```

Observed result:

- Version surface check: PASS.
- Product tests: `207 passed`.
- Release-provenance tooling test against published CivicCore: `1 passed`.
- Documentation gate: PASS.
- Placeholder import gate: PASS.
- Ruff: PASS.
- React frontend: `npm ci`, TypeScript, and Vite build all PASS.
- Public browser QA: 12 scenarios PASS, including desktop/mobile public pages and React app live API scenarios.
- Build artifacts: `civiccode-0.6.0.tar.gz`, `civiccode-0.6.0-py3-none-any.whl`, and `SHA256SUMS.txt` created.
- Final line: `VERIFY-RELEASE: PASSED`.

Additional targeted command:

```powershell
python -m pytest tests\test_release_adversarial_boundaries.py tests\test_docker_demo_runtime.py tests\test_docker_backup_restore_rehearsal_helper.py -q
```

Observed result: `15 passed`.

Additional Docker command:

```powershell
$project='civiccode_staff_surface_fix'
$env:CIVICCODE_PORT='18067'
docker compose -p $project up -d --build
bash -lc 'CIVICCODE_SMOKE_BASE_URL=http://127.0.0.1:18067 scripts/docker-demo-smoke.sh'
docker compose -p $project down -v
```

Observed result: `DOCKER-DEMO-SMOKE: PASSED`; the smoke includes the forged-staff-header 403 check on the published demo port.

## Known Boundaries For Auditor

- No v1.0.0 tag or release has been created from this branch.
- This packet is a request for independent audit, not self-clearance.
- CivicCode remains at v0.6.0 until the independent audit clears the full Definition of Done.
- The real municipal data proof uses a bounded Portland Title 13 corpus with two official chapter sources and five adopted sections; it does not claim a complete city corpus or live codifier sync.
- Local Ollama proof was captured against a local runtime and does not make AI output authoritative.
- The default Docker Compose path does not expose a certified staff shell through the published port; staff access requires a trusted, header-stripping staff-shell proxy.
- Suite truth PR #170 is separate scoped recovery work and had an unrelated installer-cleanroom lifecycle failure in CivicRecords login; this CivicCode branch does not attempt to fix that.
- Historical scratch files are present in the local worktree and are intentionally not part of this branch.

## Audit Request

Please audit the actual code and evidence against the CivicCode module-release Definition of Done. Treat passing scripts, generated artifacts, and this packet as evidence to verify, not as clearance. If any Blocker or Critical remains, CivicCode must stay v0.6.0 and no v1.0.0 tag should be created.
