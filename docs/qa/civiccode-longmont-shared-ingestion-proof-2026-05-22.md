# CivicCode Longmont Shared-Ingestion Proof - 2026-05-22

Status: evidence for independent audit; not a release claim.

Command:

```powershell
$env:CIVICCODE_SOURCE_REGISTRY_DB_URL='postgresql+psycopg2://civiccode@localhost:33139/civiccode'
$env:OLLAMA_BASE_URL='http://localhost:11434'
$env:CIVICCODE_OLLAMA_EMBEDDING_URL='http://localhost:11434'
$env:CIVICCODE_EMBEDDING_MODE='ollama'
$env:CIVICCODE_AI_MODE='ollama'
$env:CIVICCODE_OLLAMA_URL='http://localhost:11434'
$env:CIVICCODE_OLLAMA_MODEL='gemma4:e4b'
$env:CIVICCODE_OLLAMA_TIMEOUT_SECONDS='180'
$env:CIVICCODE_SEMANTIC_SCORE_FLOOR='0.58'
python scripts\prove-longmont-shared-ingestion.py --db-url $env:CIVICCODE_SOURCE_REGISTRY_DB_URL --force-reingest
```

Corpus:

- `C:\Users\scott\OneDrive\Desktop\Claude\longmont-code-corpus\Longmont, CO Code of Ordinances.pdf`
- File size: `12394756` bytes.
- CivicCore document id: `e608fd38-38c3-42e2-8a51-ad57c8f874e6`.
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

- Sources created/reused on force-reingest proof run: `1 created / 0 reused`.
- Sources reused on post-fix Q&A rerun against the same completed corpus: `1`.
- Titles: `14`.
- Chapters: `195`.
- Sections: `1443`.
- Versions: `1443`.
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
- Matched section: `4.12.280`.
- LLM provider: `ollama`.
- LLM error: `null`.
- Answer excerpt:

```text
Based on the provided text, the section discusses the retention and disposal of
records, stating that all procurement records "will be retained and disposed of
by the city in accordance with the applicable records retention guidelines and
schedules approved by the city council" (4.12.310. B). The text does not
specify the rules for public access to these documents.

Staff review is required for interpretations. Source: Title 4 (Title 4),
Chapter 4.12 (Chapter 4.12), Section 4.12.280 (City procurement records),
version Longmont Code codified through December 2025, effective 2025-12-31.
This is not a legal determination.
```

Citation:

```text
Title 4 (Title 4), Chapter 4.12 (Chapter 4.12), Section 4.12.280
(City procurement records), version Longmont Code codified
through December 2025, effective 2025-12-31
```

Known evidence limits:

- The fresh `--force-reingest` run completed on this machine and proves full-corpus ingestion, 768-dimensional shared pgvector chunk embeddings, CivicCode structuring, and five-query semantic search. A follow-up rerun against the same completed corpus, after fixing the proof-script result selector, proves local Ollama cited Q&A.
- Older CivicCore evidence that listed 1,789 chunks used `chunk_size=900` / `chunk_overlap=90`; it remains valid for that CivicCore parameter set but must not be cited as the current CivicCode PR #61 proof count.
- This is not a v1.0.0 release claim.
- Independent audit is still required before any release tag.
