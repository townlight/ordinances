# CivicCode Longmont Browser QA - 2026-05-22

Status: active-branch evidence for independent audit; not a release claim.

Runtime:

- URL: `http://127.0.0.1:8137/civiccode/app`
- Database: PostgreSQL/pgvector proof database with Longmont shared-ingestion corpus.
- Embeddings: `nomic-embed-text` through local Ollama.
- Q&A model: `gemma4:e4b` through local Ollama.

Browser coverage:

| Viewport | Initial | Search Success | Answer Success | Error State | Console | Failed Requests | Focus |
|---|---|---|---|---|---|---|---|
| Desktop 1440x950 | `desktop-initial.png` | `desktop-search-success.png` | `desktop-answer-success.png` | `desktop-error-state.png` | none | none | tab focus reached input |
| Mobile 390x844 | `mobile-initial.png` | `mobile-search-success.png` | `mobile-answer-success.png` | `mobile-error-state.png` | none | none | tab focus reached input |

Network proof:

- `GET /api/v1/civiccode/search?q=public%20access%20to%20procurement%20documents` returned HTTP 200.
- `POST /api/v1/civiccode/questions/answer` returned HTTP 200.

User-visible proof:

- Search result list included `4.12.040 - Public access to procurement documents`.
- Answer view displayed `Staff review is required for interpretations`.
- Blank search displayed actionable copy: `Enter a section number or plain-language term before searching.`

Evidence files:

- `docs/qa/civiccode-longmont-browser-qa-2026-05-22/summary.json`
- `docs/qa/civiccode-longmont-browser-qa-2026-05-22/desktop-initial.png`
- `docs/qa/civiccode-longmont-browser-qa-2026-05-22/desktop-search-success.png`
- `docs/qa/civiccode-longmont-browser-qa-2026-05-22/desktop-answer-success.png`
- `docs/qa/civiccode-longmont-browser-qa-2026-05-22/desktop-error-state.png`
- `docs/qa/civiccode-longmont-browser-qa-2026-05-22/mobile-initial.png`
- `docs/qa/civiccode-longmont-browser-qa-2026-05-22/mobile-search-success.png`
- `docs/qa/civiccode-longmont-browser-qa-2026-05-22/mobile-answer-success.png`
- `docs/qa/civiccode-longmont-browser-qa-2026-05-22/mobile-error-state.png`

Known evidence limits:

- With semantic retrieval enabled, arbitrary nonsense terms can still return nearest-neighbor results; this run captured the actionable blank-query error state instead of mislabeling vector-search behavior as empty-state coverage.
- Full public-use readiness still requires independent audit before any release tag.
