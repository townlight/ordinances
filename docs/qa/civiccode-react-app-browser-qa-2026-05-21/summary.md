# CivicCode React App Browser QA - 2026-05-21

Scope: active CivicCode product-completion branch, not a release-clearance claim.

Command:

```bash
CIVICCODE_PUBLIC_BROWSER_QA_ARTIFACT_DIR=docs/qa/civiccode-react-app-browser-qa-2026-05-21 node scripts/browser-public-surfaces-qa.cjs
```

Result: PASS.

Evidence:

| Scenario | Viewport | Proof |
|---|---:|---|
| public home | desktop/mobile | rendered, skip link focus, no console errors, no horizontal overflow |
| public search empty/results | mobile/desktop | rendered actionable empty and success states |
| public cited answer | desktop/mobile | rendered cited answer and legal-boundary copy |
| public refusal | mobile | rendered legal-advice refusal with staff contact path |
| section detail/export | desktop/mobile | rendered section detail and records-ready export states |
| React app search/answer | desktop | rendered `/civiccode/app`, executed live `/api/v1/civiccode/search` and `/api/v1/civiccode/questions/answer` calls, showed cited answer |
| React app empty/error | mobile | rendered actionable empty-input error with no console errors |

Screenshots are stored in this folder. Console errors: 0. Page errors: 0. Horizontal overflow: false for every scenario.
