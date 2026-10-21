# GitHub PR Merge 502 Runbook

Townlight Code normally merges release PRs through GitHub after CI passes. If GitHub
returns `502 Bad Gateway` or stale `merge already in progress` responses during
PR merge or close, do not keep retrying blindly.

Use this recovery path:

1. Confirm the PR check run passed: `gh pr checks <pr-number>`.
2. Confirm whether the PR actually merged: `gh pr view <pr-number> --json state,mergedAt,mergeCommit`.
3. Fetch `main` and compare the exact commit: `git fetch origin main --prune`, then `git rev-parse origin/main`.
4. If the verified release commit is already on `origin/main`, run `bash scripts/verify-release.sh` locally from `main`.
5. Create and push the signed or annotated release tag only after the verified commit SHA is on `origin/main`.
6. Confirm the GitHub release assets and SHA256SUMS match the verified build output.
7. If the PR remains open after the commit is on `main`, close it manually with a note that records the verified main SHA, tag, release URL, and CI run.

Do not use this runbook to bypass failed CI, unresolved review, mismatched
commit SHAs, missing release assets, or a failed `verify-release.sh` gate.
