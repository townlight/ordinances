"""Embedding-backed retrieval helpers for CivicCode."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


VECTOR_DIMENSIONS = 768
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"


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
        or DEFAULT_OLLAMA_URL,
        model=os.environ.get("CIVICCODE_OLLAMA_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        timeout_seconds=float(os.environ.get("CIVICCODE_OLLAMA_EMBEDDING_TIMEOUT_SECONDS", "30")),
    )


def embed_texts(texts: list[str], config: EmbeddingConfig | None = None) -> list[list[float]]:
    """Embed text through a real Ollama embedding model."""
    resolved = config or embedding_config_from_env()
    if resolved is None:
        raise SemanticSearchError(
            "CivicCode embedding search is not configured. Set CIVICCODE_EMBEDDING_MODE=ollama "
            "and CIVICCODE_OLLAMA_EMBEDDING_MODEL to an embedding-capable local model."
        )
    body = json.dumps({"model": resolved.model, "input": texts}).encode("utf-8")
    request = Request(
        f"{resolved.base_url.rstrip('/')}/api/embed",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=resolved.timeout_seconds) as response:
            payload: dict[str, Any] = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SemanticSearchError(
            f"Ollama embedding request failed with HTTP {exc.code}: {detail}"
        ) from exc
    except (TimeoutError, URLError, OSError) as exc:
        raise SemanticSearchError(f"Ollama embedding request failed: {exc}") from exc

    embeddings = payload.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        raise SemanticSearchError("Ollama embedding response did not include one embedding per input.")
    normalized: list[list[float]] = []
    for embedding in embeddings:
        if not isinstance(embedding, list) or not all(isinstance(value, int | float) for value in embedding):
            raise SemanticSearchError("Ollama embedding response contained a malformed vector.")
        vector = [float(value) for value in embedding]
        if len(vector) != VECTOR_DIMENSIONS:
            raise SemanticSearchError(
                f"Expected {VECTOR_DIMENSIONS}-dimension embeddings from {resolved.model}, got {len(vector)}."
            )
        normalized.append(_normalize(vector))
    return normalized


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
