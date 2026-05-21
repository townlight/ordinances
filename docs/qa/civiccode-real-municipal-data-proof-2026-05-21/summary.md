# CivicCode Real Municipal Data Proof - 2026-05-21

Status: PASS for source-attributed fixture proof only.

Source used:

- City of Portland code page: `https://www.portland.gov/code/13/40/020`
- Section: `13.40.020`, Backyard Livestock
- Retrieved for fixture: `2026-05-21T18:30:00Z`
- Source note: page records Ordinance 192002 effective January 10, 2025.

Command:

```powershell
python -m pytest -q tests/test_real_municipal_data_fixture.py tests/test_release_adversarial_boundaries.py tests/test_milestone_5_search_permalinks.py tests/test_milestone_7_citation_grounded_qa.py
```

Observed result:

- `24 passed`
- The staff local-bundle import endpoint accepted the official web extract fixture.
- The source registry retained the Portland source URL and `is_official=true`.
- Public search for `domestic fowl` resolved to section `13.40.020`.
- The cited-answer endpoint returned a citation with the Portland source URL.
- The answer preserved the non-authoritative legal boundary text.

Boundary:

This proves CivicCode can ingest one source-attributed municipal-code fixture,
search it, and produce a cited, non-authoritative answer through the existing
local-bundle import path. It is not a full city corpus, not a live codifier
sync, not public-use clearance, and not an independent audit sign-off.
