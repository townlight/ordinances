<a id="civiccode-tier-1-retrofit-ledger"></a>

# Townlight Code Tier 1 Retrofit Ledger

Status: CO-4 ledger, live-release scan current as of 2026-05-05.

This ledger records the CO-4 decisions for the Townlight Code releases named in the
Townlight finish directive. It does not rewrite history and does not alter
public release notes, tags, or assets. The correction action taken here is a
repo-controlled ledger plus documentation truth update.

Structured source of truth:
[`docs/ops/tier1-retrofit-ledger.json`](tier1-retrofit-ledger.json).

## Rules

- `v0.1.17` and `v0.1.18` are historical pre-gate releases.
- Neither release has Sigstore `release-attestation.json` or
  `release-attestation.json.bundle` public release assets.
- Neither release may be promoted as an attested provenance baseline.
- The active Townlight Core platform dependency now points to the first attested
  Townlight Core v1 baseline, `v1.0.0`.

## Entries

| Tag | Published | Git ref type | Target commit | Ledger status | Attestation | Rule |
| --- | --- | --- | --- | --- | --- | --- |
| `v0.1.17` | 2026-05-04T16:49:03Z | annotated tag object | `a1f414a9cd4e9e3398da9cc8e1f44f80c5d269ed` | Pre-gate, no attestation | None | Do not promote as baseline. |
| `v0.1.18` | 2026-05-04T17:11:13Z | annotated tag object | `e061d262e1fc78875e72c28a809dd07a00f7b798` | Pre-gate, no attestation | None | Do not promote as baseline. |

## Verification

```bash
python scripts/check-tier1-ledger.py
python scripts/check-tier1-ledger.py --live
```

The live check confirms each public release page exposes exactly the release
assets named by the ledger and no attestation assets.
