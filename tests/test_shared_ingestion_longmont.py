from __future__ import annotations

from civiccode import semantic_search
from types import SimpleNamespace

import pytest

from civiccode.shared_ingestion import (
    SharedIngestionError,
    _dedupe_overlapping_chunk_text,
    _extract_sections,
    _validate_pdf_path,
    _async_db_url,
)


def test_longmont_section_extractor_structures_sections_from_pdf_text() -> None:
    text = """
    CHAPTER4.12. PURCHASING*
    Sec. 4.12.010. Purpose.
    This chapter establishes rules for purchasing goods and services for the city.
    Sec. 4.12.020. Application.
    The purchasing rules apply to departments and officers unless another law controls.
    CHAPTER13.40. ANIMALS
    Sec. 13.40.040. Large livestock.
    Large livestock may be kept only under the limits stated in this chapter.
    """

    sections = _extract_sections(text)

    assert [item["number"] for item in sections] == ["4.12.010", "4.12.020", "13.40.040"]
    assert sections[0]["heading"] == "Purpose"
    assert sections[0]["chapter_name"] == "Purchasing"
    assert "purchasing goods and services" in sections[0]["body"]


def test_db_url_conversion_prefers_asyncpg_for_shared_ingestion() -> None:
    assert (
        _async_db_url("postgresql+psycopg2://user:pass@host/db")
        == "postgresql+asyncpg://user:pass@host/db"
    )
    assert (
        _async_db_url("postgresql://user:pass@host/db")
        == "postgresql+asyncpg://user:pass@host/db"
    )


def test_semantic_search_delegates_embeddings_to_civiccore(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    async def fake_embed_batch(texts, *, model, base_url, batch_size=8):
        calls.append(
            {
                "texts": texts,
                "model": model,
                "base_url": base_url,
                "batch_size": batch_size,
            }
        )
        return [[1.0] + [0.0] * 767 for _ in texts]

    monkeypatch.setenv("CIVICCODE_EMBEDDING_MODE", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    monkeypatch.setattr(semantic_search, "embed_batch", fake_embed_batch)

    embeddings = semantic_search.embed_texts(["public procurement"])

    assert len(embeddings) == 1
    assert len(embeddings[0]) == 768
    assert calls == [
        {
            "texts": ["public procurement"],
            "model": "nomic-embed-text",
            "base_url": "http://ollama:11434",
            "batch_size": 8,
        }
    ]


def test_shared_pdf_path_must_stay_inside_allowlisted_corpus(tmp_path, monkeypatch) -> None:
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    good_pdf = allowed / "code.pdf"
    bad_pdf = outside / "code.pdf"
    good_pdf.write_text("allowed", encoding="utf-8")
    bad_pdf.write_text("outside", encoding="utf-8")
    monkeypatch.setenv("CIVICCODE_SHARED_INGEST_ALLOWED_DIR", str(allowed))

    assert _validate_pdf_path(good_pdf) == good_pdf.resolve()
    with pytest.raises(SharedIngestionError) as exc:
        _validate_pdf_path(bad_pdf)

    assert exc.value.status_code == 403
    assert "outside the allowed CivicCode corpus" in exc.value.message


def test_chunk_text_reconstruction_removes_overlap_duplication() -> None:
    chunks = [
        SimpleNamespace(page_number=1, chunk_index=0, content_text="Sec. 1.01.010. Purpose. Alpha beta gamma."),
        SimpleNamespace(page_number=1, chunk_index=1, content_text="Alpha beta gamma. Sec. 1.01.020. Scope. Delta."),
    ]

    merged = _dedupe_overlapping_chunk_text(chunks)

    assert merged.count("Alpha beta gamma.") == 1
    assert "Sec. 1.01.020. Scope." in merged
