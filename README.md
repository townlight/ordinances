> **Townlight Beta 1 release:** [signed Windows installer, exact owned source, documentation and acceptance](https://github.com/townlight/townlight/releases/tag/townlight-beta-1). [Online manual](https://townlight.github.io/manuals/code.html). This retained manual edition describes the accepted candidate before publication; distribution has changed, component versions and signed bytes have not.

# Townlight Code

**Townlight Beta 1** · Existing component versions retained · AGPL-3.0-only

Code imports and preserves municipal code sources, supplies exact citations and version history, and connects proposed legislation to Meetings. Authorized staff separately record adoption evidence and codification.

## Start here

Staff should use the operating manual. Administrators should read first-run, configuration and recovery before changing a deployment. Developers should read the exact API/schema reference and matching source companion. This edition accompanies Townlight Beta 1; use the release link above for the signed candidate and exact source/documentation archives.

- [Operating manual](docs/beta-1/manuals/code.html) · [Printable PDF](docs/beta-1/pdf/Townlight-Code-Manual-Beta-1.pdf) · [Editable Word manual](docs/beta-1/docx/Townlight-Code-Manual-Beta-1.docx)
- [API and data dictionary](docs/beta-1/api/code.html) · [OpenAPI JSON](docs/beta-1/api/code-openapi.json)
- [Product and suite directory](docs/beta-1/index.html) · [Terms and full license](docs/beta-1/terms.html)

## Exact version and candidate

| Identity | Value |
| --- | --- |
| Public documentation identity | Townlight Beta 1 |
| Installer version | 1.6.0.1 |
| Product component | civiccode 1.0.8 |
| Native desktop source version | 1.6.0-1 |
| Candidate MSI SHA256 | `98bcdef11ebdf5c767f620c904ff49f85115fde3b5c23f62703b111e645aaf86` |
| Corresponding-source SHA256 | `84a23e1297e42d17b16cfc9e51b2dd78bc46414c0de8ad7ebd2466c1a409d06b` |
| Current owned software license | AGPL-3.0-only |
| Supported acceptance profile | Windows x64 fresh install; inspections-preview; separate Station configuration |


“Townlight Beta 1” identifies this coordinated beta delivery. It does not renumber the installer, native binary, Python packages or historical receipts. Component versions may differ. This documentation is a later companion to unchanged signed bytes, not a rebuilt installer. Historical release pages and manuals describe their own versions and are not the download instructions for this private candidate.

## What staff can do

- **Import a source:** Inspect the complete bundle JSON for jurisdiction, section identifiers, source/effective dates, original name and hashes before selecting Import. Import submits directly; inspect the saved import and provenance afterward. There is no separate preview/confirmation step.
- **Find the exact section:** Search the topic and open the cited section. Check the requested as-of date and version. Keep explanatory wording separate from the retained source text.
- **Inspect provenance:** Read import history, original source and section history. Export the exact cited source when it is needed for a staff workpaper or Records evidence.
- **Connect a proposal:** Create the existing Code–Meetings connection for the actual proposal and agenda context. Retain the connection identifier and keep pending text distinct from adopted code.
- **Record adoption:** Record the actual authorized meeting decision with its adoption context. An unrelated motion, packet or draft minutes does not establish that the proposal was adopted.
- **Codify separately:** Review the adopted text and affected sections, then record the distinct codification closeout. Preserve prior versions and the link to adoption evidence.
- **Share the right version:** Select permitted source evidence downstream. If visibility or source content changes, resolve the mismatch and select current evidence rather than accepting a stale cached citation.

## Operating procedures and examples

The operating manual now includes these existing procedures, with synthetic inputs, readback and limits. Follow the actual app boundary identified there; a standalone source capability is not automatically a desktop screen.

- [Cited questions summaries and local synchronization](docs/beta-1/manuals/code.html#cited-questions-summaries-and-local-synchronization).
- [Ask against an actual retained section](docs/beta-1/manuals/code.html#ask-against-an-actual-retained-section).
- [Draft and approve an explanatory summary](docs/beta-1/manuals/code.html#draft-and-approve-an-explanatory-summary).
- [Operate the existing local codifier contract](docs/beta-1/manuals/code.html#operate-the-existing-local-codifier-contract).

## Architecture and data

### Runtime and storage

The accepted package targets **Windows x64 fresh installation**. Its native shell uses **Rust 2021, Tauri 2 and Microsoft WebView2**; browser assets are JavaScript built with **Vite 8.1.6**. This describes the native desktop frontend; Station has a separate React operator, specified below or in its product manual. Canonical business workflows use bundled **CPython 3.13.5, FastAPI, Pydantic, SQLAlchemy and Alembic**, with **PostgreSQL 17 / PostGIS** and managed original files. The installed runtime tested here contains FastAPI 0.162.0. Package minimum Python requirements can differ from the bundled executable; the metadata reference preserves both. No stack rewrite is implied by the beta label.

The native transport is fixed to loopback `127.0.0.1:15480`; PostgreSQL uses the configured local runtime port (default `15432`). Optional local model service defaults to `127.0.0.1:15434`. Those are deployment defaults, not internet endpoints. The runtime has health, module and readiness endpoints; readiness is stronger than process existence. The task queue is the existing local Core task infrastructure, not an assertion that a separate Redis service is required for this desktop composition.

The default native profile is `%LOCALAPPDATA%\CivicSuite`; the historical directory name remains part of compatibility. Do not rename it to Townlight. A configured `TOWNLIGHT_PROFILE_ROOT` must be absolute. Local configuration and secrets live under that profile; protected managed files and database state must be backed up coherently. Source/runtime identity is distinct from a product’s display label.

### Data and consistency

Source registry entries; import jobs and originals; sections and versions; effective-date citations; questions, notes and summaries; Meetings connections; adoption and codification closeout.

Versioned saves use expected prior revision identifiers where defined. Reopen and reconcile on conflict. Exact exports and handoffs use source IDs, current visibility, revision and SHA256. Review belongs to the saved revision and does not transfer silently to edited text. Database changes use the owning product’s migrations; a request or readiness check is not an authorization to mutate schema.

### Capacity and platform statements

This beta has synthetic single-profile workflow evidence. It does not have a published benchmark for concurrent staff capacity, minimum RAM/CPU, large-source limits or a field SLA. Do not turn a developer machine’s specification into a supported minimum. Installer size is 2,092,122,112 bytes before installation; allow additional disk for extracted runtime, database, originals, exports, media and backups. Select equipment/storage after sizing those actual workloads.

The exact [runtime payload lock](docs/beta-1/reference/runtime-payload-lock.json) records pinned files, sizes and hashes. The [component metadata](docs/beta-1/reference/component-metadata.json) records shipped dependency declarations. These references are more precise than a manually copied dependency list. Third-party and historical license notices must accompany their matching payloads.


| Data contract | Description |
| --- | --- |
| Input | A complete supported source bundle, source and effective dates, original file hashes and actual meeting adoption evidence. |
| Retained records | Source registry entries; import jobs and originals; sections and versions; effective-date citations; questions, notes and summaries; Meetings connections; adoption and codification closeout. |
| Output | Cited code text and history, exact exports, staff explanations with source references and an explicit adoption/codification trail. |
| Connections | Receives Meetings decision evidence. Supplies permitted cited material to Records, Zoning, Permitting and Inspections. Planning’s selected installed evidence providers are Meetings and Zoning; no separate direct Code connection is implied. |


## Setup and operation

1. Obtain the identified signed private candidate and its corresponding-source companion from the beta coordinator. The landing pages in this documentation are not an installer download service.
2. On the intended fresh Windows test installation, verify the MSI hash and publisher signature before installing. Preserve unrelated profiles and recovery material. This candidate has fresh-install acceptance; historical in-place upgrades are unverified.
3. Launch Townlight under the intended named Windows account. Choose the storage folders. Select **Townlight Inspections candidate** (`inspections-preview`) for all eight desktop products. A narrower default selection will not expose all workspaces.
4. Enter the city profile, time zone and contacts. Create the first named local administrator, sign in and choose protected backup storage. **Continue without local AI** is valid for the deterministic workflows.
5. Run Health Check and wait for readiness. Open Townlight. In System Health select **Finish Records Migration** to activate the canonical Python/PostgreSQL runtime. Do not fabricate migration receipts or seed accounts.
6. Create named staff through Settings. Import authorized sources using each product’s source library. All examples in this package are synthetic; they are not municipal authority.
7. Provision Station separately if it is part of the beta exercise. Selecting the desktop composition does not start or configure Station. Configure vision explicitly only if automatic photo drafting is selected.

## Configuration
### Native deployment configuration

Use Setup, Settings and System Health for supported staff operation. Administrators provision folders, backup storage, named accounts and the city profile. Select `inspections-preview` for the full eight-workspace desktop. Station remains a separate service boundary. Do not use a standalone product’s demo server as a substitute for the installed workspace.

Technical deployments use `TOWNLIGHT_PRODUCT_PROFILE`, `TOWNLIGHT_PROFILE_ROOT`, `DATABASE_URL`, `CIVICSUITE_RUNTIME_PORT`, `PORTAL_MODE` and the runtime-managed secret files. Treat database URLs and native session proofs as secrets. The installed native domain runtime explicitly refuses non-loopback binding. `PORTAL_MODE=private` is the accepted posture; changing it does not by itself commission an internet portal, authentication provider or reverse proxy.

The isolated documentation exporter sets a fictional profile and unusable synthetic database origin only to read schemas; those values are not deployment configuration. Keep deployment values in the intended process/account scope. An already-running process does not automatically inherit later environment edits.

## API usage
### Native command example

The following JavaScript belongs in the existing trusted Townlight frontend/development environment with `invoke` imported from `@tauri-apps/api/core`. It is not a command for an arbitrary web page or an instruction for nontechnical staff. IDs must come from records created in an isolated synthetic exercise.

```javascript
import { invoke } from '@tauri-apps/api/core';
const result = await invoke('code_domain_request', {request: {operation: 'citation', section_number: '18.20.050', as_of: null}});
console.log(result);
```

### Trusted local HTTP example

An administrator/developer can inspect an already-configured isolated runtime from a trusted local process. This PowerShell example reads the signed-in synthetic profile’s existing proof into memory; it does not create a user, seed a session, reveal the proof in output or bypass a permission check. Do not use real city data in development examples. A read response does not prove approval or publication.

```powershell
$profilePath = Join-Path $env:LOCALAPPDATA 'CivicSuite'
$sessionPath = Join-Path $profilePath 'config\local-session.json'
$session = Get-Content -LiteralPath $sessionPath -Raw | ConvertFrom-Json
$headers = @{ 'X-Townlight-Session' = $session.session_hash }
Invoke-RestMethod -Uri 'http://127.0.0.1:15480/desktop/v1/code/sources' -Headers $headers
Remove-Variable session, headers
```

### Complete synthetic source bundle

The [synthetic Code bundle](docs/beta-1/reference/examples/synthetic-code-bundle.json) is the retained fixture used by the beta staff exercise. It includes the complete supported source envelope rather than a shortened pseudo-payload. Keep its fictional source labels. For Planning, wrap it as `{"bundle": BUNDLE, "expected_previous_revision": null}`; for Permitting use `{"bundle": BUNDLE, "expected_revision": null}`. Code and Zoning take their own complete import envelopes. Replace null with the current expected revision when revising an existing source, as the applicable schema requires. These are import examples, not legal authority or permission to load them into a live city profile.

### A synthetic write with subsequent readback

This example demonstrates the existing Meetings HTTP contract in an isolated exercise. It is intentionally fictional. It does not start a service. Its authentication setup is included so it can be run independently under the signed-in synthetic account. If a write times out, inspect current records before repeating it.

```powershell
$profilePath = Join-Path $env:LOCALAPPDATA 'CivicSuite'
$sessionPath = Join-Path $profilePath 'config/local-session.json'
$session = Get-Content -LiteralPath $sessionPath -Raw | ConvertFrom-Json
$headers = @{ 'X-Townlight-Session' = $session.session_hash }
$body = @{
  title = 'Synthetic documentation exercise'
  scheduled_start = '2026-11-05T18:00:00-07:00'
  location = 'Synthetic room'
  meeting_type = 'regular'
} | ConvertTo-Json
$meeting = Invoke-RestMethod -Method Post `
  -Uri 'http://127.0.0.1:15480/desktop/v1/meetings/meetings' `
  -Headers $headers -ContentType 'application/json' -Body $body
Invoke-RestMethod `
  -Uri ('http://127.0.0.1:15480/desktop/v1/meetings/meetings/' + $meeting.id) `
  -Headers $headers
Remove-Variable session, headers
```

This write requires Meetings to be enabled and the signed-in staff role to permit it. It is a cross-suite integration example; for this product’s request models, use the complete technical reference below.

## MCP status

No direct product MCP server is exposed by the accepted Townlight desktop or Station boundary. Do not configure an invented `townlight mcp` command or assume an AI client has staff permissions. The integration surfaces for this beta are native IPC, the documented HTTP APIs, source bundle imports, exact exports and the existing Station CLI.

The bundled transcription code includes a **TextFlowKit MCP adapter** as a separate source capability. It offers job-based `transcribe_media`, `get_transcript`, `list_jobs`, `get_job_status` and `export_transcript`, and additional tools declared in that adapter. It uses stdio first and optional Streamable HTTP, with the MCP SDK as an optional extra. It is not automatically launched, authenticated as Townlight staff or accepted as a Townlight product MCP deployment. This documentation does not add such a service.

For a transcription client already provisioned separately, an illustrative tool call is:

```json
{"name":"get_job_status","arguments":{"job_id":"synthetic-existing-job-id"}}
```

Use a job ID returned by that transcription service. This example does not create a Townlight record or bypass its review/Records handoff. The exact optional adapter tool signatures are supplied in the [MCP source reference](docs/beta-1/reference/mcp.html). Station meeting capture does not become live speech recognition because this optional donor adapter exists.

## Verification and known limits

| Product | Recorded result | Precisely exercised |
| --- | --- | --- |
| Code | PASS | Synthetic official source import, exact citation/history/export; proposal into Meetings, recorded adoption and separately codified version; native connection readback. |


These results come from the identified signed candidate’s fresh normal-profile Sandbox exercise: real native IPC/HTTP/PostgreSQL and selected headless controls. All accounts, source bundles and media were synthetic. The guest install/uninstall and recovery passed, and the owned Sandbox stopped. No host installed application or standalone CivicCast was changed. This documentation task reuses those receipts; it does not claim a new software acceptance run.

The [workflow matrix](docs/beta-1/reference/workflow-matrix.json) identifies raw receipt filenames. The [evidence index](docs/beta-1/reference/sandbox-evidence-index.json) retains their original hashes; raw receipts remain in the private beta handoff rather than being silently republished with the documentation site.

The limits remain: actual city field acceptance and equipment/network commissioning; Station automatic provisioning/SCM commissioning; every UI/role combination; field recognition accuracy; and historical in-place upgrades are not certified. They are not five invented feature requirements. Fresh-install controlled beta handoff remains the accepted scope. This package makes no city-deployment, publication or general-availability claim.

An imported document is not automatically adopted law. Local imports and orchestration do not establish a live agreement with every commercial codifier. Human approval and authoritative source applicability remain necessary.

## Development and repository map

Use the corresponding source for the candidate rather than assuming the public default branch matches it. The source companion contains `installed-owned-source`, product build inputs, desktop Rust/browser sources, locks and `BUILD.md`. It excludes credentials and third-party binary/model payloads. Use the recorded runtime lock when reproducing packaging.

Relevant source contracts:

- `civiccode/source_registry.py`
- `civicsuite_runtime/code_bridge.py`
- `civicsuite_runtime/code_meetings.py`
- `desktop/src-tauri/src/code_client.rs`

The desktop package defines `npm run build`, `npm test`, `npm run test:browser` and its Tauri command. Python products retain their own `pyproject.toml`, tests and migrations; use the matching checkout’s declared dependencies and test configuration. Do not run a sample server against a production profile. This documentation build validates documentation only and reuses the separately identified installed acceptance; it does not claim a new complete application CI run.

## Recovery and support

Save work and use Core’s canonical **Backup Now** before maintenance. That operation stops writers. Preserve the coherent profile/database/document backup and its receipt, then use **Start** to resume. A source export is not a full backup.

Use **Restore Latest Backup** through the supported controls. If the result says **Restore needs service start**, use **Start**, then **Check**, and reopen a known record. Do not repeat restore merely because services need to start. The fresh-profile acceptance verified that a fulfilled request survived restore and a post-backup marker did not.

Keep Station’s dedicated database and media evidence together in its own backup. Core’s native-profile backup must not be assumed to include an external Station data directory. Stop writers during a coordinated backup. Preserve failed media attempts and logs.

On failure, record the time, selected composition, component/installer versions and exact message. Check System Health for stopped, starting, ready or failed dependencies. Use the existing Retry control after readiness; do not create duplicate business records to refresh a stale view. Share only a redacted diagnostic bundle. Preserve secrets, original evidence, recovery material and unrelated installations.

## License and responsible use

Current owned code is AGPL-3.0-only. Preserve full license, matching corresponding source, dependency notices and historical grants. Terms of use do not remove license rights. Source imports do not confer permission to publish third-party material. Review all automatic drafts and use the separate owning-product decision before official action. CivicCast remains independent.

## Earlier documentation

Previous editions are retained under `docs/history/pre-townlight-beta-1/`. They describe their original software and license grants. Use the current Townlight Beta 1 manual for this candidate.
