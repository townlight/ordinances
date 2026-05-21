# CivicCode Independent Audit Packet - 2026-05-21

Status: ready for independent audit review, not ready for v1.0.0 tagging.

## Scope Lock

- Active release lock: CivicCode only.
- Target: v1.0.0 only after the full Definition of Done and independent audit.
- Current honest version: v0.6.0.
- Branch: `finish/civiccode-v1-real-product`.
- Head at packet creation: `d2bf477`.
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
| Semantic search / pgvector | `civiccode/semantic_search.py`; migration `civiccode_0011_semantic_search.py`; search responses include semantic retrieval metadata. |
| Real municipal data | `civiccode/real_municipal_fixtures.py`; `tests/test_real_municipal_data_fixture.py`; `docs/qa/civiccode-real-municipal-data-proof-2026-05-21/summary.md`. |
| Staff/public routes | `docs/qa/civiccode-route-inventory-2026-05-21/summary.md` and `routes.json`; 55 routes inventoried. |
| Staff browser QA | `docs/qa/civiccode-staff-browser-qa-2026-05-21/summary.md`; 16 staff scenarios recorded. |
| Installed stack | `docs/qa/civiccode-installed-stack-proof-2026-05-21/summary.md`; successful `*-3` logs cover Docker/PostgreSQL smoke and backup/restore rehearsal. |
| Suite installer selection | `docs/qa/civiccode-suite-installer-selection-proof-2026-05-21/summary.md`; custom profile resolves CivicCore + CivicClerk + CivicCode and `verify-installer-plan.py` passed. |
| Adversarial behavior | `tests/test_release_adversarial_boundaries.py`; covers bad input, missing/stale records, public/staff boundary, spoofed staff headers, unavailable Ollama fallback, and no auto-determination behavior. |
| Documentation honesty | README, CHANGELOG, USER-MANUAL, docs index, and QA docs keep CivicCode at v0.6.0 and explicitly deny finished/shipping/city-ready/public-use status until independent audit clears it. |

## Verification Run

Command:

```powershell
bash scripts/verify-release.sh
```

Observed result:

- Version surface check: PASS.
- Product tests: `202 passed`.
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
python -m pytest -q tests/test_real_municipal_data_fixture.py tests/test_release_adversarial_boundaries.py tests/test_milestone_5_search_permalinks.py tests/test_milestone_7_citation_grounded_qa.py
```

Observed result: `24 passed`.

## Known Boundaries For Auditor

- No v1.0.0 tag or release has been created from this branch.
- This packet is a request for independent audit, not self-clearance.
- CivicCode remains at v0.6.0 until the independent audit clears the full Definition of Done.
- The real municipal data proof uses one source-attributed official code fixture; it does not claim a complete city corpus or live codifier sync.
- Local Ollama proof was captured against a local runtime and does not make AI output authoritative.
- Suite truth PR #170 is separate scoped recovery work and had an unrelated installer-cleanroom lifecycle failure in CivicRecords login; this CivicCode branch does not attempt to fix that.
- Historical scratch files are present in the local worktree and are intentionally not part of this branch.

## Audit Request

Please audit the actual code and evidence against the CivicCode v1.0.0 Definition of Done. Treat passing scripts, generated artifacts, and this packet as evidence to verify, not as clearance. If any Blocker or Critical remains, CivicCode must stay v0.6.0 and no v1.0.0 tag should be created.
