# CivicCode Longmont Shared-Ingestion Proof - 2026-05-22

Status: evidence for independent audit; not a release claim.

Force-reingest command:

```powershell
$env:CIVICCODE_SOURCE_REGISTRY_DB_URL='postgresql+psycopg2://civiccode@localhost:33141/civiccode'
$env:OLLAMA_BASE_URL='http://localhost:11434'
$env:CIVICCODE_OLLAMA_EMBEDDING_URL='http://localhost:11434'
$env:CIVICCODE_EMBEDDING_MODE='ollama'
$env:CIVICCODE_AI_MODE='ollama'
$env:CIVICCODE_OLLAMA_URL='http://localhost:11434'
$env:CIVICCODE_OLLAMA_MODEL='gemma4:e4b'
$env:CIVICCODE_OLLAMA_TIMEOUT_SECONDS='300'
$env:CIVICCODE_SEMANTIC_SCORE_FLOOR='0.58'
$env:CIVICCODE_SHARED_INGEST_CHUNK_SIZE='500'
$env:CIVICCODE_SHARED_INGEST_CHUNK_OVERLAP='50'
python scripts\prove-longmont-shared-ingestion.py --db-url $env:CIVICCODE_SOURCE_REGISTRY_DB_URL --force-reingest
```

Corpus:

- `C:\Users\scott\OneDrive\Desktop\Claude\longmont-code-corpus\Longmont, CO Code of Ordinances.pdf`
- File size: `12394756` bytes.
- CivicCore document id: `000d9f60-ebfe-402e-9918-1fbf48898e6f`.
- CivicCore document status: `completed`.

Shared CivicCore ingestion output:

- Parser page count: `1604`.
- Stored chunk text characters, including configured overlap: `4661856`.
- Chunking parameters: `chunk_size=500`, `chunk_overlap=50`.
- Queryable `document_chunks` rows: `2931`.
- Embedded chunk rows: `2931`.
- Sample chunk index: `0`.
- Sample chunk page: `1`.
- Sample vector dimensionality: `768`.
- Sample chunk text:

```text
SUPPLEMENT NO. 8
March 2026
CODE OF ORDINANCES
City of
LONGMONT, COLORADO
Looseleaf Supplement
This Supplement contains all ordinances deemed advisable to be included at this time
through:
Ordinance No. O-2025-83, enacted December 16, 2025. See the Code Comparative Table for further information. Remove Old Pages Insert
```

CivicCode structuring output:

- Sources created/reused by import job: `0 created / 1 reused`.
- Titles: `14`.
- Chapters: `207`.
- Sections: `1995`.
- Versions: `1995`.
- First structured section: `1.04.000 - Title; citation`.
- Source URL: `https://library.municode.com/co/longmont/codes/code_of_ordinances`.

Section-body fidelity proof:

Command:

```powershell
python scripts\prove-longmont-section-fidelity.py
```

Output from the committed script, using the same Longmont PDF source:

- Full side-by-side output: `docs/qa/civiccode-longmont-section-fidelity-proof-2026-05-22.txt`.
- Structured sections: `1995`.
- Empty bodies: `0`.
- Too-short bodies under the proof threshold: `8`.
- Header/footer-polluted bodies: `0`.
- `4.12.040` source excerpt and structured body both contain the full public-records paragraph.
- `4.12.040` `body_excerpt_found_in_source`: `true`.
- `4.12.040` `header_footer_polluted`: `false`.
- `4.12.040` `too_short`: `false`.

The eight too-short bodies are short in the source text as extracted, not empty-section drops; they remain listed in the script output for audit review. The proof does not treat the section count alone as fidelity evidence.

Dual CivicCore chunk-parameter proof:

Command:

```powershell
python scripts\prove-longmont-civiccore-chunk-params.py --db-url $env:CIVICCODE_SOURCE_REGISTRY_DB_URL
```

Output from the committed script, same PDF, same CivicCore `ingest_file()` path,
same run id `20260522171542`:

| Label | Chunk size | Overlap | Document chunks | Chunk rows | Embedded rows | Pages | Vector dim |
|---|---:|---:|---:|---:|---:|---:|---:|
| `civiccore-original-proof` | `900` | `90` | `1789` | `1789` | `1789` | `1604` | `768` |
| `civiccode-pr61-proof` | `500` | `50` | `2931` | `2931` | `2931` | `1604` | `768` |

This demonstrates the 1,789 vs. 2,931 chunk-count difference with live
ingestion, not a documentation assertion.

Semantic search proof:

Queries exercised by the proof script:

1. `public access to procurement documents`
2. `rules for emergency purchases`
3. `bid protest appeal`
4. `disposal of surplus city property`
5. `city manager purchasing authority`

Top results from the same force-reingest proof run:

| Query | Count | Top results |
|---|---:|---|
| `public access to procurement documents` | `5` | `4.12.170 - Cancellation of invitations for bids or requests for proposals` (`0.656692`); `4.12.010 - Purpose` (`0.6338`); `4.12.040 - Public access to procurement documents` (`0.630508`) |
| `rules for emergency purchases` | `5` | `2.20.170 - Rules and regulations governing city property` (`0.658082`); `4.12.180 - Responsibility of offerors` (`0.654005`); `11.12.010 - Authorized when` (`0.63646`) |
| `bid protest appeal` | `5` | `4.12.400 - Protest of solicitation or award` (`0.71742`); `4.12.390 - Finality of decision` (`0.653361`); `15.02.040 - Common review procedures` (`0.617039`) |
| `disposal of surplus city property` | `5` | `10.50.050 - Disposition of lost or abandoned property` (`0.696358`); `10.50.010 - Definitions` (`0.690831`); `14.12.020 - Service established` (`0.673018`) |
| `city manager purchasing authority` | `5` | `4.12.070 - Authority and duties` (`0.736773`); `4.12.095 - Execution of intergovernmental agreements` (`0.670086`); `4.12.140 - Small or micro purchases` (`0.658042`) |

Search metadata:

```json
{
  "enabled": true,
  "embedding_provider": "ollama:nomic-embed-text",
  "pgvector_runtime": "postgresql_pgvector",
  "ranked_document_count": 5
}
```

Low-relevance guard: PostgreSQL semantic search filters shared chunk matches
below `CIVICCODE_SEMANTIC_SCORE_FLOOR` (`0.58` for this proof) before mapping
chunks back to CivicCode sections.

Organic local LLM cited Q&A proof:

- Question: `What does the Longmont code say about public access to procurement documents?`
- Mode: `organic_top_search_result`.
- Matched section: `4.12.170`.
- LLM provider: `ollama`.
- LLM error: `null`.
- Answer excerpt:

```text
The city must publish a notice of cancellation on the electronic solicitation
system, or otherwise make it available to all businesses solicited. This notice
must identify the solicitation and explain the reason for cancellation or
rejection (4.12.170).

Staff review is required for interpretations. Source: Title 4 (Title 4),
Chapter 4.12 (Purchasing), Section 4.12.170 (Cancellation of invitations for
bids or requests for proposals), version Longmont Code codified through
December 2025, effective 2025-12-31. This is not a legal determination.
```

The organic example is intentionally not hand-pinned. It shows the current
search-to-answer path selects `4.12.170` for this query while `4.12.040` is the
third ranked semantic result.

Direct section lookup example:

Command:

```powershell
python scripts\prove-longmont-shared-ingestion.py `
  --db-url $env:CIVICCODE_SOURCE_REGISTRY_DB_URL `
  --answer-section-number 4.12.040 `
  --question "What does Section 4.12.040 say about public access to procurement documents?"
```

- Mode: `direct_section_override`.
- Matched section: `4.12.040`.
- LLM provider: `ollama`.
- LLM error: `null`.
- Answer excerpt:

```text
Procurement documents are public records to the extent provided in C.R.S. title
24, article 72, and are available to the public as provided in that statute
(4.12.040). However, parties submitting bids or proposals may designate certain
portions as confidential, proprietary, or trade secret information. If a
disclosure request is made, the city must notify the submitting party, who then
has two business days to advise the city whether it objects to the disclosure of
the designated information. The city must comply with applicable law relating to
public open records (4.12.040).
```

Known evidence limits:

- The fresh `--force-reingest` run completed on this machine and proves full-corpus ingestion, 768-dimensional shared pgvector chunk embeddings, CivicCode structuring, five-query semantic search, and organic local Ollama cited Q&A from one run.
- The direct `4.12.040` answer is an explicit direct-section lookup example, not the organic search-to-answer proof.
- The committed dual-run script reproduced the chunk-count reconciliation: CivicCore `900/90` produced `1789` chunks and CivicCode PR #61 `500/50` produced `2931` chunks from the same PDF through the same CivicCore `ingest_file()` path.
- This is not a v1.0.0 release claim.
- Independent audit is still required before any release tag.
