# CivicCode Route Inventory - 2026-05-21

Route count: 55

| Audience | Methods | Path | Auth | QA status | State coverage |
|---|---|---|---|---|---|
| operator | GET | `/health` | none | api/integration coverage required | API state coverage required |
| public | GET | `/` | none | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/chapters` | staff headers required | api/integration coverage required | API state coverage required |
| public | GET | `/api/v1/civiccode/citations/build` | none | api/integration coverage required | API state coverage required |
| public | GET | `/api/v1/civiccode/popular-questions` | none | api/integration coverage required | API state coverage required |
| public | POST | `/api/v1/civiccode/questions/answer` | none | api/integration coverage required | API state coverage required |
| public | GET | `/api/v1/civiccode/search` | none | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/sections` | staff headers required | api/integration coverage required | API state coverage required |
| public | GET | `/api/v1/civiccode/sections/lookup` | none | api/integration coverage required | API state coverage required |
| public | POST | `/api/v1/civiccode/sections/resolve` | none | api/integration coverage required | API state coverage required |
| public | GET | `/api/v1/civiccode/sections/{section_id}/history` | none | api/integration coverage required | API state coverage required |
| public | GET | `/api/v1/civiccode/sections/{section_id}/permalink` | none | api/integration coverage required | API state coverage required |
| public | GET | `/api/v1/civiccode/sections/{section_id}/summaries` | none | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/sections/{section_id}/versions` | staff headers required | api/integration coverage required | API state coverage required |
| public | GET | `/api/v1/civiccode/sections/{section_number}/related` | none | api/integration coverage required | API state coverage required |
| public | GET | `/api/v1/civiccode/sections/{section_ref}/export` | none | api/integration coverage required | API state coverage required |
| public | GET | `/api/v1/civiccode/sources` | none | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/sources` | staff headers required | api/integration coverage required | API state coverage required |
| public | GET | `/api/v1/civiccode/sources/catalog` | none | api/integration coverage required | API state coverage required |
| public | GET | `/api/v1/civiccode/sources/{source_id}` | none | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/sources/{source_id}/transitions` | staff headers required | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/titles` | staff headers required | api/integration coverage required | API state coverage required |
| public | GET | `/civiccode` | none | covered by current browser harness | loading/success/empty/error/partial for React app; success/empty/error for server-rendered public/staff harnesses |
| public | GET | `/civiccode/answer` | none | covered by current browser harness | loading/success/empty/error/partial for React app; success/empty/error for server-rendered public/staff harnesses |
| public | GET | `/civiccode/app` | none | covered by current browser harness | loading/success/empty/error/partial for React app; success/empty/error for server-rendered public/staff harnesses |
| public | GET | `/civiccode/app/` | none | covered by current browser harness | loading/success/empty/error/partial for React app; success/empty/error for server-rendered public/staff harnesses |
| public |  | `/civiccode/app/assets` | none | covered by current browser harness | loading/success/empty/error/partial for React app; success/empty/error for server-rendered public/staff harnesses |
| public | GET | `/civiccode/search` | none | covered by current browser harness | loading/success/empty/error/partial for React app; success/empty/error for server-rendered public/staff harnesses |
| public | GET | `/civiccode/sections/{section_ref}` | none | covered by current browser harness | loading/success/empty/error/partial for React app; success/empty/error for server-rendered public/staff harnesses |
| public | GET | `/civiccode/sections/{section_ref}/export` | none | covered by current browser harness | loading/success/empty/error/partial for React app; success/empty/error for server-rendered public/staff harnesses |
| staff | GET | `/api/v1/civiccode/staff/audit-events` | staff headers required | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/staff/civicclerk/ordinance-events` | staff headers required | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/staff/civicclerk/ordinance-events/{event_id}/resolve` | staff headers required | api/integration coverage required | API state coverage required |
| staff | GET | `/api/v1/civiccode/staff/imports` | staff headers required | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/staff/imports/local-bundle` | staff headers required | api/integration coverage required | API state coverage required |
| staff | GET | `/api/v1/civiccode/staff/imports/{job_id}` | staff headers required | api/integration coverage required | API state coverage required |
| staff | GET | `/api/v1/civiccode/staff/imports/{job_id}/provenance` | staff headers required | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/staff/imports/{job_id}/retry` | staff headers required | api/integration coverage required | API state coverage required |
| staff | GET | `/api/v1/civiccode/staff/imports/{job_id}/tree` | staff headers required | api/integration coverage required | API state coverage required |
| staff | GET | `/api/v1/civiccode/staff/operational-state` | staff headers required | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/staff/popular-questions` | staff headers required | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/staff/questions/answer` | staff headers required | api/integration coverage required | API state coverage required |
| staff | GET | `/api/v1/civiccode/staff/sections/{section_id}/notes` | staff headers required | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/staff/sections/{section_id}/notes` | staff headers required | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/staff/sections/{section_id}/summaries` | staff headers required | api/integration coverage required | API state coverage required |
| staff | GET | `/api/v1/civiccode/staff/sources` | staff headers required | api/integration coverage required | API state coverage required |
| staff | GET | `/api/v1/civiccode/staff/sources/{source_id}` | staff headers required | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/staff/summaries/{summary_id}/approve` | staff headers required | api/integration coverage required | API state coverage required |
| staff | GET | `/api/v1/civiccode/staff/sync/codifier-sources` | staff headers required | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/staff/sync/codifier-sources` | staff headers required | api/integration coverage required | API state coverage required |
| staff | POST | `/api/v1/civiccode/staff/sync/codifier-sources/{source_id}/run` | staff headers required | api/integration coverage required | API state coverage required |
| staff | GET | `/staff/code` | staff headers required | covered by current browser harness | loading/success/empty/error/partial for React app; success/empty/error for server-rendered public/staff harnesses |
| staff | GET | `/staff/imports` | staff headers required | covered by current browser harness | loading/success/empty/error/partial for React app; success/empty/error for server-rendered public/staff harnesses |
| staff | GET | `/staff/sources` | staff headers required | covered by current browser harness | loading/success/empty/error/partial for React app; success/empty/error for server-rendered public/staff harnesses |
| staff | GET | `/staff/sync` | staff headers required | covered by current browser harness | loading/success/empty/error/partial for React app; success/empty/error for server-rendered public/staff harnesses |
