# CivicCode Product Completion UI QA - 2026-05-21

Status: evidence for the active v0.6.0 completion branch only. This is not a
release-clearance artifact.

## Runtime

- Local server: `http://127.0.0.1:8017/civiccode/app`
- Health check: `{"status":"ok","service":"civiccode","version":"0.6.0","civiccore":"1.1.0"}`
- Seed: Portland Title 13 local bundle through `/api/v1/civiccode/staff/imports/local-bundle`

## Browser Checks

| Viewport | Evidence | Result |
|---|---|---|
| Desktop 1365 x 768 | `docs/qa/civiccode-product-completion-desktop-2026-05-21.png` | Search result and cited answer rendered; console had no warning/error records. |
| Mobile 390 x 844 | `docs/qa/civiccode-product-completion-mobile-2026-05-21.png` | Search result rendered with semantic-disabled runtime copy; console had no warning/error records. |

## States Covered

- Loading: exercised through Search and Answer button actions before result panels settled.
- Success: `13.40.020 - Backyard Livestock` search result rendered from the seeded Portland corpus.
- Empty: unseeded search state returned "No public CivicCode results matched that search" with a concrete fix path.
- Error: empty search and empty answer actions returned actionable copy.
- Partial/degraded: local Ollama answer path rendered the partial state with deterministic cited fallback when the LLM call was unavailable.
- Keyboard/focus: interactable order exposes skip link, query input, Search, Answer, pinned section, and examples; focus-visible CSS is present in the app stylesheet.

## Copy Notes

- The masthead no longer claims "Semantic retrieval" or "Local LLM ready" unconditionally.
- Search results now state when semantic retrieval is not configured for the runtime.
- Example queries now target the seeded Portland Title 13 corpus instead of old mock-city section numbers.
