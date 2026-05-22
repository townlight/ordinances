# CivicCode Staff Browser QA - 2026-05-21

Status: PASS.

Command:

```powershell
$env:CIVICCODE_BROWSER_QA_ARTIFACT_DIR='docs/qa/civiccode-staff-browser-qa-2026-05-21'
node scripts/browser-staff-surfaces-qa.cjs
```

Coverage:

- 16 staff browser scenarios.
- Mobile access-required states for `/staff/code`, `/staff/sources`, `/staff/imports`, and `/staff/sync`.
- Mobile empty states for all four staff surfaces.
- Desktop and mobile populated states for all four staff surfaces.
- Staff-header auth boundary checked through expected HTTP 403 states.
- Skip-link/focus target checked for every scenario.
- Actionable fix-path block checked where required.
- Horizontal overflow checked at mobile widths.
- Console warnings/errors checked.
- Page errors checked.

Observed result:

- All 16 scenarios passed.
- Console errors: 0.
- Page errors: 0.
- Horizontal overflow: false for every scenario.
- First focus: skip link for every scenario.

Boundary:

This is browser evidence for the current server-rendered staff workspaces. It
does not replace API authorization tests, installed-stack proof, or independent
audit clearance.
