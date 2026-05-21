"""Deterministic semantic retrieval helpers for CivicCode."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import re
from typing import Iterable


VECTOR_DIMENSIONS = 16


@dataclass(frozen=True, slots=True)
class SemanticDocument:
    id: str
    text: str


def embed_text(text: str) -> list[float]:
    """Build a small stable embedding for local/offline semantic retrieval tests."""
    vector = [0.0] * VECTOR_DIMENSIONS
    for token in _tokens(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = digest[0] % VECTOR_DIMENSIONS
        sign = 1.0 if digest[1] % 2 == 0 else -1.0
        vector[bucket] += sign * (1.0 + min(len(token), 12) / 12.0)
    length = math.sqrt(sum(value * value for value in vector))
    if length == 0:
        return vector
    return [round(value / length, 6) for value in vector]


def rank_documents(query: str, documents: Iterable[SemanticDocument]) -> list[dict[str, float | str]]:
    """Rank documents by cosine similarity against the stable local embedding."""
    query_vector = embed_text(query)
    query_tokens = set(_tokens(query))
    ranked: list[dict[str, float | str]] = []
    for document in documents:
        document_tokens = set(_tokens(document.text))
        overlap = len(query_tokens & document_tokens) / max(len(query_tokens), 1)
        score = _cosine(query_vector, embed_text(document.text))
        blended = (score * 0.55) + (overlap * 0.45)
        if overlap > 0 or blended >= 0.62:
            ranked.append({"id": document.id, "score": round(blended, 6)})
    return sorted(ranked, key=lambda item: float(item["score"]), reverse=True)


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2]


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=False))
