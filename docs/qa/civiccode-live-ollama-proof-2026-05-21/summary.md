# CivicCode Live Ollama Proof - 2026-05-21

Status: PASS for local-runtime proof only.

Command:

```powershell
$env:CIVICCODE_DEMO_SEED='1'
$env:CIVICCODE_AI_MODE='ollama'
$env:CIVICCODE_OLLAMA_MODEL='gemma3:12b'
$env:CIVICCODE_OLLAMA_TIMEOUT_SECONDS='120'
python <inline ASGI proof script>
```

Evidence file:

- `docs/qa/civiccode-live-ollama-proof-2026-05-21/ollama-answer-proof.json`

Observed result:

- Health endpoint returned HTTP 200.
- `/api/v1/civiccode/questions/answer` returned HTTP 200.
- `llm_provider`: `ollama`.
- `llm_model`: `gemma3:12b`.
- `matched_section_number`: `6.12.040`.
- Citation count: 1.
- `ai_review_required`: `true`.
- `ai_authority`: `non_authoritative_staff_review_required`.
- `prompt_contract`: `single_citation_source_bounded_no_legal_determination`.
- `llm_error`: `null`.

Boundary:

This proves CivicCode can call a local Ollama runtime and return a cited,
staff-review-required, non-authoritative answer over seeded municipal-code data.
It does not by itself prove public-use readiness, installer integration, real
city data ingestion, or independent audit clearance.
