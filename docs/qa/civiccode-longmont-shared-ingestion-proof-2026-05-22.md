# CivicCode Longmont Shared-Ingestion Proof - 2026-05-22

Status: evidence for independent audit; not a release claim.

Command:

```powershell
$env:CIVICCODE_SOURCE_REGISTRY_DB_URL='postgresql+psycopg2://civiccode@localhost:33140/civiccode'
$env:OLLAMA_BASE_URL='http://localhost:11434'
$env:CIVICCODE_OLLAMA_EMBEDDING_URL='http://localhost:11434'
$env:CIVICCODE_EMBEDDING_MODE='ollama'
$env:CIVICCODE_AI_MODE='ollama'
$env:CIVICCODE_OLLAMA_URL='http://localhost:11434'
$env:CIVICCODE_OLLAMA_MODEL='gemma4:e4b'
$env:CIVICCODE_OLLAMA_TIMEOUT_SECONDS='300'
$env:CIVICCODE_SEMANTIC_SCORE_FLOOR='0.58'
python scripts\prove-longmont-shared-ingestion.py `
  --db-url $env:CIVICCODE_SOURCE_REGISTRY_DB_URL `
  --force-reingest `
  --answer-section-number 4.12.040 `
  --question "What does Section 4.12.040 say about public access to procurement documents?"
```

Corpus:

- `C:\Users\scott\OneDrive\Desktop\Claude\longmont-code-corpus\Longmont, CO Code of Ordinances.pdf`
- File size: `12394756` bytes.
- CivicCore document id: `b636cbfa-8555-4b7a-9226-a38868e555e9`.
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
Ordinance No. O-2025-83, enacted December 16, 2025.
```

CivicCode structuring output:

- Sources created/reused by import job: `0 created / 1 reused`.
- Titles: `14`.
- Chapters: `195`.
- Sections: `1443`.
- Versions: `1443`.
- First structured section: `1.12.010 - Designated`.
- Source URL: `https://library.municode.com/co/longmont/codes/code_of_ordinances`.

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
| `public access to procurement documents` | `5` | `4.12.280 - City procurement records` (`0.656692`); `4.12.010 - Purpose` (`0.6338`); `4.12.040 - Public access to procurement documents` (`0.630508`) |
| `rules for emergency purchases` | `5` | `2.20.170 - Rules and regulations governing city property` (`0.658082`); `4.12.180 - Responsibility of offerors` (`0.654005`); `11.12.010 - Authorized when` (`0.63646`) |
| `bid protest appeal` | `4` | `4.12.400 - Protest of solicitation or award` (`0.71742`); `4.12.390 - Finality of decision` (`0.653361`); `15.02.040 - Common review procedures` (`0.617039`) |
| `disposal of surplus city property` | `5` | `10.50.080 - Appeal` (`0.696358`); `10.50.010 - Definitions` (`0.690831`); `14.12.020 - Service established` (`0.673018`) |
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

Local LLM cited Q&A proof:

- Question: `What does Section 4.12.040 say about public access to procurement documents?`
- Matched section: `4.12.040`.
- LLM provider: `ollama`.
- LLM error: `null`.
- Answer excerpt:

```text
The provided text only lists the section title, "4.12.040. Public access to
procurement documents," and immediately follows it with the beginning of
Section 4.12.050.

Staff review is required for interpretations. Source: Title 4 (Title 4),
Chapter 4.12 (Chapter 4.12), Section 4.12.040 (Public access to procurement
documents), version Longmont Code codified through December 2025, effective
2025-12-31. This is not a legal determination.
```

Citation:

```text
Title 4 (Title 4), Chapter 4.12 (Chapter 4.12), Section 4.12.040
(Public access to procurement documents), version Longmont Code codified
through December 2025, effective 2025-12-31
```

Known evidence limits:

- The fresh `--force-reingest` run completed on this machine and proves full-corpus ingestion, 768-dimensional shared pgvector chunk embeddings, CivicCode structuring, five-query semantic search, and local Ollama cited Q&A from one run.
- The committed dual-run script reproduced the chunk-count reconciliation: CivicCore `900/90` produced `1789` chunks and CivicCode PR #61 `500/50` produced `2931` chunks from the same PDF through the same CivicCore `ingest_file()` path.
- This is not a v1.0.0 release claim.
- Independent audit is still required before any release tag.
