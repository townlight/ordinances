"""CivicCode domain ranking helpers backed by CivicCore embeddings."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import math
import os
from concurrent.futures import ThreadPoolExecutor

from civiccore.ingest.embedder import embed_batch


VECTOR_DIMENSIONS = 768
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_OLLAMA_URL = "http://localhost:11434"


class SemanticSearchError(RuntimeError):
    """Raised when a configured embedding provider cannot build learned vectors."""


@dataclass(frozen=True, slots=True)
class SemanticDocument:
    id: str
    version_id: str
    text: str


@dataclass(frozen=True, slots=True)
class SearchEmbedding:
    section_id: str
    section_version_id: str
    embedding_model: str
    embedding: list[float]
    source_text_checksum: str


@dataclass(frozen=True, slots=True)
class EmbeddingConfig:
    mode: str
    base_url: str
    model: str
    timeout_seconds: float


def embedding_config_from_env() -> EmbeddingConfig | None:
    """Return the configured learned-vector provider, or None when unavailable."""
    mode = os.environ.get("CIVICCODE_EMBEDDING_MODE", "").strip().lower()
    if mode not in {"ollama", "local_ollama"}:
        return None
    return EmbeddingConfig(
        mode="ollama",
        base_url=os.environ.get("CIVICCODE_OLLAMA_EMBEDDING_URL")
        or os.environ.get("CIVICCODE_OLLAMA_URL")
        or os.environ.get("OLLAMA_BASE_URL")
        or DEFAULT_OLLAMA_URL,
        model=os.environ.get("CIVICCODE_OLLAMA_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        timeout_seconds=float(os.environ.get("CIVICCODE_OLLAMA_EMBEDDING_TIMEOUT_SECONDS", "30")),
    )


def embed_texts(texts: list[str], config: EmbeddingConfig | None = None) -> list[list[float]]:
    """Embed text through CivicCore's shared Ollama embedding provider."""
    resolved = config or embedding_config_from_env()
    if resolved is None:
        raise SemanticSearchError(
            "CivicCode embedding search is not configured. Set CIVICCODE_EMBEDDING_MODE=ollama "
            "and CIVICCODE_OLLAMA_EMBEDDING_MODEL to an embedding-capable local model."
        )
    try:
        embeddings = _run_civiccore_embed_batch(
            texts,
            model=resolved.model,
            base_url=resolved.base_url,
        )
    except Exception as exc:  # pragma: no cover - exact provider errors vary by Ollama runtime
        raise SemanticSearchError(f"CivicCore embedding request failed: {exc}") from exc
    if len(embeddings) != len(texts):
        raise SemanticSearchError("CivicCore embedding response did not include one embedding per input.")
    normalized: list[list[float]] = []
    for embedding in embeddings:
        if not isinstance(embedding, list) or not all(isinstance(value, int | float) for value in embedding):
            raise SemanticSearchError("CivicCore embedding response contained a malformed vector.")
        vector = [float(value) for value in embedding]
        if len(vector) != VECTOR_DIMENSIONS:
            raise SemanticSearchError(
                f"Expected {VECTOR_DIMENSIONS}-dimension embeddings from {resolved.model}, got {len(vector)}."
            )
        normalized.append(_normalize(vector))
    return normalized


def _run_civiccore_embed_batch(
    texts: list[str],
    *,
    model: str,
    base_url: str,
) -> list[list[float]]:
    coroutine = embed_batch(texts, model=model, base_url=base_url)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(lambda: asyncio.run(coroutine)).result()


def rank_embeddings(
    query_embedding: list[float],
    document_embeddings: list[SearchEmbedding],
) -> list[dict[str, float | str]]:
    """Rank persisted learned vectors by cosine similarity."""
    query = _normalize(query_embedding)
    ranked = [
        {
            "id": item.section_id,
            "version_id": item.section_version_id,
            "score": round(_cosine(query, item.embedding), 6),
            "embedding_model": item.embedding_model,
        }
        for item in document_embeddings
    ]
    return sorted(ranked, key=lambda item: float(item["score"]), reverse=True)


def _normalize(vector: list[float]) -> list[float]:
    length = math.sqrt(sum(value * value for value in vector))
    if length == 0:
        return vector
    return [value / length for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=False))
