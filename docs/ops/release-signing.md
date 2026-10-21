# Release Signing and Provenance

Townlight Code releases do not rely on a secret signing key on one maintainer's
workstation. The release trust artifact is a versioned
`release-attestation.json` plus `release-attestation.json.bundle`, signed by
Sigstore/cosign from the GitHub Actions release workflow's OIDC identity.

Release provenance is a pre-flight gate, not post-publication forensics. A
failing gate produces no release assets. There is no dev-process exemption, no
localhost identity exception, and no "fix it in the next release" path.

## Current Signing Model

Git tags are release pointers. They are not the trust root. GitHub's release
page can show a "Verified" badge for the target commit even when the tag object
is lightweight or unsigned, so the strengthened gate verifies the Sigstore
attestation instead of trusting the release-page badge.

The acceptable Townlight Code release shape is:

1. Push a `v*` tag only after the release branch has merged through GitHub.
2. Run the release workflow in `.github/workflows/release.yml`.
3. Run the adversarial fixture suite before building release assets.
4. Build the wheel, source distribution, and `SHA256SUMS.txt`.
5. Build canonical schema-v1 `release-attestation.json` naming the tag ref,
   target commit, target tree, workflow identity, and artifact hashes.
6. Sign the attestation with `cosign sign-blob` using GitHub Actions OIDC.
7. Verify the attestation, bundle, tag target, target tree, exact workflow
   identity, OIDC issuer, and artifact hashes before publication.
8. Publish the GitHub Release only after the pre-flight gate passes.
9. Run the post-publication provenance workflow as a secondary check.

Clean-machine verification for a future attested release:

```bash
cosign verify-blob release-attestation.json \
  --bundle release-attestation.json.bundle \
  --certificate-identity "https://github.com/CivicSuite/civiccode/.github/workflows/release.yml@refs/tags/vX.Y.Z" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

sha256sum -c SHA256SUMS.txt
python scripts/verify-release-provenance.py "vX.Y.Z" \
  --repo "CivicSuite/civiccode" \
  --attestation release-attestation.json \
  --bundle release-attestation.json.bundle \
  --artifacts-dir .
```

The certificate identity is exact per repo and per tag. Do not widen it to an
organization-level wildcard. Any future wildcard must carry a written
auditor-facing justification.

## Attestation Contract

Townlight Code consumes the canonical Townlight Core release-provenance helper and
schema-v1 attestation contract. Product runtime tests run against the published,
Sigstore-attested `civiccore v1.0.0` dependency before the provenance tooling
phase installs the Townlight Core `v1.0` tag for the shared fixture set.

The attestation schema is versioned and canonicalized before signing. A valid
attestation must name:

- schema version,
- repository,
- tag name, tag ref type, and tag ref SHA,
- target commit and target tree,
- workflow identity and workflow run ID,
- artifact filenames, sizes, and SHA-256 hashes.

The gate verifies that the attestation claims match GitHub's live tag ref and
the local artifact bytes. A mismatch fails closed.

## Adversarial Fixture Suite

The canonical fixture suite lives in Townlight Core and is mirrored here for local
tooling tests. The gate must reject every failure fixture with a specific
auditor-facing error and accept the known-good fixture.

Current fixtures:

- `00_known_good_sigstore_attestation.json`: accepts a valid schema-v1
  Sigstore-attested release.
- `10_missing_attestation_schema.json`: rejects schema-less attestations.
- `20_wrong_workflow_identity.json`: rejects signatures from the wrong
  workflow identity.
- `30_mismatched_artifact_hash.json`: rejects artifact bytes that do not match
  attestation hashes.
- `40_unexpected_oidc_issuer.json`: rejects signatures from an unexpected OIDC
  issuer.
- `50_transparency_log_unavailable.json`: fails closed when transparency-log
  verification is unavailable.
- `60_tag_target_mismatch.json`: rejects attestations whose tag target does
  not match the live ref.
- `70_workflow_rename_identity_drift.json`: rejects workflow rename or path
  drift unless the expected identity is updated deliberately.
- `80_trust_root_rotation.json`: fails closed on untrusted or rotated trust
  roots until the trust policy is reviewed.

New production defect classes must be added here before any destructive
correction is requested.

## Failure Modes and Policy

### Trust-Root Rotation

Sigstore/Fulcio trust roots may rotate. The gate fails closed when the bundle no
longer chains to the configured trust root. Remediation is a policy update with
auditor review, not a release override.

### Transparency-Log Availability

Online verification depends on Rekor transparency-log access. A release may not
publish if Rekor verification is unavailable. For procurement review in
disconnected environments, auditors verify against the stored bundle and the
published release evidence package; if offline verification cannot establish
the expected identity and inclusion proof, the review records an unverifiable
result rather than accepting by inference.

### Workflow Identity Drift

Renaming `.github/workflows/release.yml`, moving the repo, or changing the tag
ref changes the certificate identity. That is treated as a release-policy
change. The exact identity in the release notes and gate configuration must be
updated in the same reviewed PR.

### Bootstrap Trust

Sigstore verification requires trust in Sigstore's public roots and GitHub's
OIDC issuer. The public verification command names the expected issuer and
workflow identity explicitly so outside auditors can reproduce the trust
decision from a clean machine.

### Artifact Mutation After Signing

Artifact hashes are part of the attestation. If a wheel, source distribution,
or checksum manifest changes after signing, the gate rejects the release.

## Historical v0.1.17 and v0.1.18 State

The v0.1.17 and v0.1.18 releases predate the Sigstore attestation model and are
not corrected by deleting or recreating tags. CO-4 records both releases as
historical pre-gate artifacts in
[`docs/ops/tier1-retrofit-ledger.md`](tier1-retrofit-ledger.md). They must not
be promoted as attested provenance baselines.

### v0.1.17 First Correction Framing

The first v0.1.17 correction was performed against an unachievable target:
"GitHub-verified signed annotated tag object." GitHub native release creation
does not produce such a tag object. The auditor authorized that target without
confirming feasibility; the swarm executed in good faith against the available
target; the corrected model now uses an achievable Sigstore attestation target.
This is not recorded as a swarm execution failure.

### Current v0.1.18 Ledger Statement

Historical pre-gate artifact: `v0.1.18`.

Auditor-verifiable facts:

- GitHub tag ref `refs/tags/v0.1.18` points at annotated tag object
  `d82660282fa48193fd437f033c28bec687fb380c`.
- That tag object targets commit
  `e061d262e1fc78875e72c28a809dd07a00f7b798`.
- The target commit is GitHub-verified.
- The tag object itself is not GitHub-verified:
  `verification.verified=false`, `verification.reason=unsigned`.
- The release does not include a Sigstore `release-attestation.json` and
  `release-attestation.json.bundle`.

Expected current gate behavior:

```bash
python scripts/verify-release-provenance.py v0.1.18 --repo CivicSuite/civiccode
```

The command fails closed because live release verification now requires an
attestation and bundle.

The same CO-4 rule applies to `v0.1.17`: the release remains available only as
historical pre-gate material and is not an attested provenance baseline.

## Post-Publication Verification

`.github/workflows/release-provenance.yml` is a secondary check. It downloads
the published attestation, bundle, wheel, source distribution, and checksum
manifest from the GitHub Release, then runs the same gate. It is not a
substitute for the pre-flight gate in `.github/workflows/release.yml`.

## Non-Goals

- No local maintainer GPG key is required for normal release signing.
- No placeholder identity such as `scott@localhost` may appear in release
  commits, taggers, attestations, or release notes.
- No existing v0.1.17 or v0.1.18 release notes may be edited without explicit
  per-release authorization.
- No historical release may be deleted or retagged without explicit
  per-release destructive-action authorization.
