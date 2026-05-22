# CivicCode Longmont Shared-Ingestion Proof - 2026-05-22

Status: evidence for independent audit; not a release claim.

Command:

```powershell
$env:CIVICCODE_SOURCE_REGISTRY_DB_URL='postgresql+psycopg2://civiccode@localhost:33134/civiccode'
$env:OLLAMA_BASE_URL='http://localhost:11434'
$env:CIVICCODE_OLLAMA_EMBEDDING_URL='http://localhost:11434'
$env:CIVICCODE_EMBEDDING_MODE='ollama'
$env:CIVICCODE_AI_MODE='ollama'
$env:CIVICCODE_OLLAMA_URL='http://localhost:11434'
$env:CIVICCODE_OLLAMA_MODEL='gemma4:e4b'
$env:CIVICCODE_OLLAMA_TIMEOUT_SECONDS='120'
$env:CIVICCODE_SEMANTIC_SCORE_FLOOR='0.58'
python scripts\prove-longmont-shared-ingestion.py --db-url $env:CIVICCODE_SOURCE_REGISTRY_DB_URL --force-reingest
```

Corpus:

- `C:\Users\scott\OneDrive\Desktop\Claude\longmont-code-corpus\Longmont, CO Code of Ordinances.pdf`
- File size: `12394756` bytes.
- CivicCore document id: `be65e19f-4ecc-447a-b861-034a1584a6e0`.
- CivicCore document status: `completed`.

Shared CivicCore ingestion output:

- Parser page count: `1604`.
- Parsed character count: `4505994`.
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

- Sources created/reused on final proof run: `0 created / 1 reused`.
- Titles: `14`.
- Chapters: `195`.
- Sections: `1445`.
- Versions: `1445`.
- First structured section: `1.12.010 - Designated`.
- Source URL: `https://library.municode.com/co/longmont/codes/code_of_ordinances`.

Semantic search proof:

Queries exercised by the proof script:

1. `public access to procurement documents`
2. `rules for emergency purchases`
3. `bid protest appeal`
4. `disposal of surplus city property`
5. `city manager purchasing authority`

Representative query: `public access to procurement documents`

Top results included:

1. `4.12.280 - City procurement records`, semantic score `0.656692`.
2. `4.12.010 - Purpose`, semantic score `0.6338`.
3. `4.12.040 - Public access to procurement documents`, semantic score `0.630508`.

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

- Question: `What does the Longmont code say about public access to procurement documents?`
- Matched section: `4.12.040`.
- LLM provider: `ollama`.
- LLM error: `null`.
- Answer excerpt:

```text
Section 4.12.040 is titled "Public access to procurement documents."

(Title 4, Chapter 4.12, Section 4.12.040)

Staff review is required for interpretations.
```

Citation:

```text
Title 4 (Title 4), Chapter 4.12 (Chapter 4.12), Section 4.12.040
(Public access to procurement documents), version Longmont Code codified
through December 2025, effective 2025-12-31
```

Known evidence limits:

- This proves full-corpus ingestion, shared pgvector chunk search, CivicCode structuring, and local Ollama cited Q&A on this machine.
- Chunk-count reconciliation was rerun directly against the current CivicCore parser/chunker for the same 12,394,756-byte PDF. It returned 1,604 pages, 4,505,994 parsed characters, and 2,931 chunks with `chunk_size=500` / `chunk_overlap=50`; older evidence that listed 1,789 chunks is stale or from a non-identical run and is not used as current CivicCode proof.
- This is not a v1.0.0 release claim.
- Independent audit is still required before any release tag.
