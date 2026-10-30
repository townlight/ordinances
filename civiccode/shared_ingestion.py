"""CivicCode municipal-code structuring over CivicCore shared ingestion."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime
import os
from pathlib import Path
import re
import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from civiccode.import_connectors import _empty_counts


LONGMONT_SOURCE_ID = "longmont-co-code-ordinances-2025"
LONGMONT_SOURCE_NAME = "Longmont, CO Code of Ordinances"
LONGMONT_VERSION_LABEL = "Longmont Code codified through December 2025"
LONGMONT_EFFECTIVE_START = date(2025, 12, 31)
_SECTION_RE = re.compile(
    r"(?:^|\n)\s*Sec\.\s*(?P<number>\d{1,2}(?:\.\d{1,3}){2,4})\.\s+"
    r"(?P<heading>[A-Z][A-Za-z0-9 ,;:'\"()/&\\\-\n]{2,180})\.",
    re.MULTILINE,
)
_CHAPTER_RE_TEMPLATE = r"CHAPTER\s*{chapter}\.?\s+(?P<name>[A-Z][A-Z0-9 ,;:'\"()/&\\-]{{2,120}})"
_SECTION_SYMBOL_RE = r"(?:\u00a7)"
_RUNNING_TITLE_NAMES = (
    "BUSINESS TAXES, LICENSES AND REGULATIONS",
    "HEALTH AND SAFETY",
    "LAND DEVELOPMENT CODE",
    "LONGMONT CODE",
    "REVENUE AND FINANCE",
)
_RUNNING_LINE_RE = re.compile(
    (
        r"^(?:"
        rf"[A-Z][A-Z &]+ {_SECTION_SYMBOL_RE} \d{{1,2}}\.\d{{2}}(?:\.\d{{3}})?|"
        rf"{_SECTION_SYMBOL_RE} \d{{1,2}}\.\d{{2}}(?:\.\d{{3}}){{0,2}}(?: LONGMONT(?: CODE)?)?|"
        r"LONGMONT CODE|"
        r"(?:Supp\. No\. \d+\s+)?CD\d+:\d+(?:\.\d+)?(?: CODE)?|"
        r"Supp\. No\. \d+|"
        + "|".join(re.escape(title) for title in _RUNNING_TITLE_NAMES)
        + r")$"
    )
)
class SharedIngestionError(ValueError):
    """Shared ingestion failure with an operator-facing fix path."""

    def __init__(self, message: str, fix: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.message = message
        self.fix = fix
        self.status_code = status_code

    def detail(self) -> dict[str, str]:
        return {"message": self.message, "fix": self.fix}


@dataclass(frozen=True, slots=True)
class SharedIngestionImport:
    """A CivicCore-ingested document plus a CivicCode local-bundle payload."""

    payload: dict[str, Any]
    proof: dict[str, Any]


async def build_longmont_import_from_shared_ingestion(
    *,
    pdf_path: str | Path,
    db_url: str,
    actor: str,
    force_reingest: bool = False,
) -> SharedIngestionImport:
    """Ingest the full Longmont PDF through CivicCore, then structure sections for CivicCode."""

    resolved_pdf = _validate_pdf_path(pdf_path)
    if not resolved_pdf.exists():
        raise SharedIngestionError(
            f"PDF '{resolved_pdf}' was not found.",
            "Provide the full path to the Longmont Code of Ordinances PDF and retry.",
            status_code=404,
        )
    chunk_size = int(os.environ.get("CIVICCODE_SHARED_INGEST_CHUNK_SIZE", "500"))
    chunk_overlap = int(os.environ.get("CIVICCODE_SHARED_INGEST_CHUNK_OVERLAP", "50"))
    _ensure_civiccore_schema(db_url)
    async_url = _async_db_url(db_url)
    engine = create_async_engine(async_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            from civiccore.ingest import Document, DocumentChunk, compute_file_hash, ingest_file

            source = await _get_or_create_data_source(session, actor=actor)
            file_hash = await asyncio.to_thread(compute_file_hash, resolved_pdf)
            document = (
                await session.execute(
                    select(Document).where(
                        Document.source_id == source.id,
                        Document.file_hash == file_hash,
                    )
                )
            ).scalar_one_or_none()
            if force_reingest and document is not None:
                await _delete_existing_document(session, document_id=document.id)
                document = None
            if document is None:
                document = await ingest_file(
                    session=session,
                    file_path=resolved_pdf,
                    source_id=source.id,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
            chunks = (
                await session.execute(
                    select(DocumentChunk)
                    .where(DocumentChunk.document_id == document.id)
                    .order_by(DocumentChunk.chunk_index)
                )
            ).scalars().all()
            if document.chunk_count and not chunks:
                raise SharedIngestionError(
                    "CivicCore reported chunks but none were queryable.",
                    "Check the shared ingestion database tables and rerun the import.",
                    status_code=500,
                )
            payload = _build_civiccode_payload(
                pdf_path=resolved_pdf,
                document=document,
                chunks=chunks,
            )
            proof = _build_proof(
                document=document,
                chunks=chunks,
                payload=payload,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                force_reingest=force_reingest,
            )
            return SharedIngestionImport(payload=payload, proof=proof)
    finally:
        await engine.dispose()


def build_longmont_import_from_shared_ingestion_sync(
    *,
    pdf_path: str | Path,
    db_url: str,
    actor: str,
    force_reingest: bool = False,
) -> SharedIngestionImport:
    """Synchronous wrapper for scripts and tests."""

    return asyncio.run(
        build_longmont_import_from_shared_ingestion(
            pdf_path=pdf_path,
            db_url=db_url,
            actor=actor,
            force_reingest=force_reingest,
        )
    )


def _ensure_civiccore_schema(db_url: str) -> None:
    from civiccore.migrations.runner import upgrade_to_head

    prior = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = db_url
    try:
        upgrade_to_head()
    finally:
        if prior is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prior


async def _get_or_create_data_source(session, *, actor: str):
    from civiccore.ingest import DataSource, SourceType

    existing = (
        await session.execute(select(DataSource).where(DataSource.name == LONGMONT_SOURCE_NAME))
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    actor_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, actor.strip().lower() or "civiccode-shared-ingestion")
    await _ensure_civiccore_actor(session, actor_uuid=actor_uuid, actor=actor)
    source = DataSource(
        name=LONGMONT_SOURCE_NAME,
        source_type=SourceType.MANUAL_DROP,
        connection_config={
            "module": "civiccode",
            "corpus": "longmont-code-corpus",
            "retrieval_method": "civiccore_shared_pdf_ingest",
        },
        created_by=actor_uuid,
    )
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return source


async def _ensure_civiccore_actor(session, *, actor_uuid: uuid.UUID, actor: str) -> None:
    existing = await session.execute(sa.text("SELECT id FROM public.users WHERE id = :id"), {"id": actor_uuid})
    if existing.first() is not None:
        return
    await session.execute(
        sa.text(
            """
            INSERT INTO public.users
                (id, email, hashed_password, is_active, is_superuser, is_verified, full_name, role)
            VALUES
                (:id, :email, 'civiccode-shared-ingestion-local-only', true, false, true,
                 'CivicCode Shared Ingestion', 'staff')
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": actor_uuid, "email": _actor_email(actor)},
    )
    await session.commit()


async def _delete_existing_document(session, *, document_id) -> None:
    from civiccore.ingest import Document, DocumentChunk

    await session.execute(sa.delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    await session.execute(sa.delete(Document).where(Document.id == document_id))
    await session.commit()


def _validate_pdf_path(pdf_path: str | Path) -> Path:
    resolved_pdf = Path(pdf_path).resolve()
    allowed_roots = _allowed_pdf_roots()
    if not any(resolved_pdf == root or root in resolved_pdf.parents for root in allowed_roots):
        roots = ", ".join(str(root) for root in allowed_roots)
        raise SharedIngestionError(
            f"PDF '{resolved_pdf}' is outside the allowed CivicCode corpus directories.",
            f"Move the file under one of these directories and retry: {roots}",
            status_code=403,
        )
    return resolved_pdf


def _allowed_pdf_roots() -> list[Path]:
    roots: list[Path] = []
    configured = os.environ.get("CIVICCODE_SHARED_INGEST_ALLOWED_DIRS") or os.environ.get(
        "CIVICCODE_SHARED_INGEST_ALLOWED_DIR"
    )
    if configured:
        roots.extend(Path(value).resolve() for value in configured.split(os.pathsep) if value.strip())
    roots.append((Path(__file__).resolve().parents[2] / "longmont-code-corpus").resolve())
    roots.append((Path(__file__).resolve().parents[1] / "fixtures").resolve())
    return roots


def _actor_email(actor: str) -> str:
    value = actor.strip().lower()
    if "@" in value:
        return value[:320]
    return "civiccode-shared-ingestion@example.gov"


def _build_civiccode_payload(
    *,
    pdf_path: Path,
    document,
    chunks: list,
) -> dict[str, Any]:
    full_text = _structuring_text_from_source(pdf_path=pdf_path, chunks=chunks)
    extracted_sections = _extract_sections(full_text)
    if not extracted_sections:
        raise SharedIngestionError(
            "No municipal code sections were found in the CivicCore-ingested text.",
            "Confirm the PDF text layer is readable, then rerun ingestion.",
            status_code=422,
        )
    titles: dict[str, dict[str, Any]] = {}
    chapters: dict[str, dict[str, Any]] = {}
    sections: list[dict[str, Any]] = []
    versions: list[dict[str, Any]] = []
    for index, item in enumerate(extracted_sections, start=1):
        number_parts = item["number"].split(".")
        title_number = number_parts[0]
        chapter_part = number_parts[1]
        chapter_number = f"{title_number}.{chapter_part}"
        title_id = f"longmont-title-{title_number}"
        chapter_id = f"longmont-chapter-{chapter_number.replace('.', '-')}"
        section_id = f"longmont-section-{item['number'].replace('.', '-')}"
        version_id = f"{section_id}-current"
        titles.setdefault(
            title_id,
            {
                "title_id": title_id,
                "title_number": title_number,
                "title_name": f"Title {title_number}",
                "sort_order": int(title_number),
            },
        )
        chapters.setdefault(
            chapter_id,
            {
                "chapter_id": chapter_id,
                "title_id": title_id,
                "chapter_number": chapter_number,
                "chapter_name": item["chapter_name"],
                "sort_order": _sort_key(chapter_number),
            },
        )
        sections.append(
            {
                "section_id": section_id,
                "chapter_id": chapter_id,
                "section_number": item["number"],
                "section_heading": item["heading"],
                "sort_order": index,
            }
        )
        versions.append(
            {
                "version_id": version_id,
                "section_id": section_id,
                "source_id": LONGMONT_SOURCE_ID,
                "version_label": LONGMONT_VERSION_LABEL,
                "body": item["body"],
                "effective_start": LONGMONT_EFFECTIVE_START,
                "status": "adopted",
                "is_current": True,
            }
        )
    return {
        "job_id": "import_longmont_shared_civiccore_pdf",
        "connector_type": "official_html_extract",
        "source": {
            "source_id": LONGMONT_SOURCE_ID,
            "name": LONGMONT_SOURCE_NAME,
            "publisher": "City of Longmont, Colorado",
            "source_type": "official_file_drop",
            "source_category": "municipal_code",
            "source_url": "https://library.municode.com/co/longmont/codes/code_of_ordinances",
            "file_reference": str(pdf_path),
            "retrieved_at": datetime.now(UTC),
            "retrieval_method": "civiccore_shared_pdf_ingest",
            "checksum": document.file_hash,
            "source_owner": "City Clerk",
            "is_official": True,
            "status": "active",
            "staff_notes": "Full Longmont Code PDF parsed by CivicCore shared ingestion.",
        },
        "titles": sorted(titles.values(), key=lambda item: item["sort_order"]),
        "chapters": sorted(chapters.values(), key=lambda item: item["sort_order"]),
        "sections": sections,
        "versions": versions,
        "provenance": {
            "retrieval_method": "civiccore_shared_pdf_ingest",
            "document_id": str(document.id),
            "document_chunk_count": document.chunk_count,
            "fixture_name": "Longmont, CO Code of Ordinances.pdf",
            "full_corpus": True,
        },
    }


def _extract_sections(full_text: str) -> list[dict[str, str]]:
    full_text = _trim_non_code_appendices(full_text)
    normalized = _normalize_text(full_text)
    matches = list(_SECTION_RE.finditer(normalized))
    sections: list[dict[str, str]] = []
    section_indexes: dict[str, int] = {}
    for index, match in enumerate(matches):
        number = match.group("number")
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        body = normalized[match.end() : end].strip()
        if len(body) < 40:
            continue
        chapter_number = ".".join(number.split(".")[:2])
        candidate = {
            "number": number,
            "heading": _clean_heading(match.group("heading")),
            "chapter_name": _chapter_name(normalized, start, chapter_number),
            "body": f"{number}. {_clean_heading(match.group('heading'))}.\n\n{body}",
        }
        if number in section_indexes:
            existing_index = section_indexes[number]
            if len(candidate["body"]) > len(sections[existing_index]["body"]):
                sections[existing_index] = candidate
            continue
        section_indexes[number] = len(sections)
        sections.append(candidate)
    return sections


def _trim_non_code_appendices(text: str) -> str:
    final_code_anchor = max(text.rfind("Sec. 20.20.080."), text.rfind("CHAPTER 20.20."))
    if final_code_anchor == -1:
        return text
    markers = (
        "\nCODE COMPARATIVE TABLE",
        "\nCODE INDEX",
        "\nINDEX\n",
    )
    cut_points = [
        index
        for marker in markers
        if (index := text.find(marker, final_code_anchor)) != -1
    ]
    if not cut_points:
        return text
    return text[: min(cut_points)]


def _structuring_text_from_source(*, pdf_path: Path, chunks: list) -> str:
    if pdf_path.suffix.lower() == ".pdf" and pdf_path.exists():
        try:
            return _extract_pdf_column_text(pdf_path)
        except Exception:
            return _dedupe_overlapping_chunk_text(chunks)
    return _dedupe_overlapping_chunk_text(chunks)


def _extract_pdf_column_text(pdf_path: Path) -> str:
    try:
        return _extract_pdf_block_text(pdf_path)
    except Exception:
        return _extract_pdf_word_column_text(pdf_path)


def _extract_pdf_block_text(pdf_path: Path) -> str:
    import fitz

    page_texts: list[str] = []
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            page_text = _extract_page_block_text(page)
            if _is_longmont_toc_or_intro_page(page_text):
                continue
            page_texts.append(page_text)
    return "\n\n".join(page_texts)


def _extract_page_block_text(page) -> str:
    blocks = [
        block
        for block in page.get_text("blocks")
        if len(block) >= 7 and block[6] == 0 and 45 < float(block[1]) < page.rect.height - 45
    ]
    ordered = sorted(
        blocks,
        key=lambda block: (
            0 if ((float(block[0]) + float(block[2])) / 2) < (page.rect.width / 2) else 1,
            float(block[1]),
            float(block[0]),
        ),
    )
    page_text = "\n\n".join(str(block[4]).strip() for block in ordered if str(block[4]).strip())
    return _strip_page_toc_preamble(page_text)


def _strip_page_toc_preamble(page_text: str) -> str:
    chapter_match = re.search(r"(?:^|\n)\s*CHAPTER\s+\d{1,2}\.\d{2}\.", page_text)
    if not chapter_match:
        return page_text
    preamble = page_text[: chapter_match.start()]
    has_toc_like_sections = len(_SECTION_RE.findall(preamble)) >= 2
    has_code_body_markers = "(Code " in preamble or "Ord. No." in preamble
    if has_toc_like_sections and not has_code_body_markers:
        return page_text[chapter_match.start() :].lstrip()
    return page_text


def _extract_pdf_word_column_text(pdf_path: Path) -> str:
    import pdfplumber

    page_texts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = _extract_page_column_text(page)
            if _is_longmont_toc_or_intro_page(page_text):
                continue
            page_texts.append(page_text)
    return "\n\n".join(page_texts)


def _extract_page_column_text(page) -> str:
    words = page.extract_words(
        x_tolerance=1,
        y_tolerance=3,
        keep_blank_chars=False,
        use_text_flow=False,
    )
    split_x = (page.width / 2) - 19
    columns: list[list[str]] = [[], []]
    for _, line_words in _group_words_by_line(
        [
            word
            for word in words
            if 45 < float(word["top"]) < page.height - 45
        ]
    ):
        for segment in _split_line_segments(line_words):
            column_index = 0 if _segment_center(segment) < split_x else 1
            columns[column_index].append(
                " ".join(str(word["text"]) for word in sorted(segment, key=lambda item: float(item["x0"])))
            )
    return "\n\n".join("\n".join(lines) for lines in columns if lines)


def _group_words_by_line(words: list[dict[str, Any]]) -> list[tuple[float, list[dict[str, Any]]]]:
    grouped: list[tuple[float, list[dict[str, Any]]]] = []
    for word in sorted(words, key=lambda item: (round(float(item["top"]) / 3) * 3, float(item["x0"]))):
        top = round(float(word["top"]) / 3) * 3
        if not grouped or abs(grouped[-1][0] - top) > 3:
            grouped.append((top, [word]))
        else:
            grouped[-1][1].append(word)
    return grouped


def _split_line_segments(words: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    segments: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    prior_x1: float | None = None
    for word in sorted(words, key=lambda item: float(item["x0"])):
        x0 = float(word["x0"])
        if current and prior_x1 is not None and x0 - prior_x1 > 45:
            segments.append(current)
            current = []
        current.append(word)
        prior_x1 = float(word["x1"])
    if current:
        segments.append(current)
    return segments


def _segment_center(words: list[dict[str, Any]]) -> float:
    return (min(float(word["x0"]) for word in words) + max(float(word["x1"]) for word in words)) / 2


def _is_longmont_toc_or_intro_page(page_text: str) -> bool:
    compact = " ".join(page_text.split())
    if not compact:
        return True
    intro_markers = (
        "ADOPTING ORDINANCE",
        "ORDINANCE O-2022-35",
        "THE COUNCIL OF THE CITY OF LONGMONT",
        "Page Numbering",
        "History Notes",
        "Source Materials",
        "Numbering System",
        "Chapter and Section Numbering",
    )
    if any(marker in compact for marker in intro_markers):
        return True
    section_header_count = len(re.findall(r"\bSec\. \d{1,2}\.\d{2}\.\d{3}\.", page_text))
    code_history_count = compact.count("(Code ") + compact.count("Ord. No.")
    return section_header_count >= 4 and code_history_count == 0


def _dedupe_overlapping_chunk_text(chunks: list) -> str:
    pages: dict[int, list] = {}
    unpaged: list[str] = []
    for chunk in chunks:
        page_number = getattr(chunk, "page_number", None)
        if page_number is None:
            unpaged.append(str(chunk.content_text))
            continue
        pages.setdefault(int(page_number), []).append(chunk)
    page_texts: list[str] = []
    for page_number in sorted(pages):
        page_chunks = sorted(pages[page_number], key=lambda item: item.chunk_index)
        page_texts.append(_merge_chunk_texts([str(chunk.content_text) for chunk in page_chunks]))
    if unpaged:
        page_texts.append(_merge_chunk_texts(unpaged))
    return "\n\n".join(page_texts)


def _merge_chunk_texts(texts: list[str]) -> str:
    merged = ""
    for text in texts:
        cleaned = text.strip()
        if not cleaned:
            continue
        if not merged:
            merged = cleaned
            continue
        overlap = _suffix_prefix_overlap(merged, cleaned)
        separator = "" if overlap else "\n\n"
        merged = f"{merged}{separator}{cleaned[overlap:]}"
    return merged


def _suffix_prefix_overlap(left: str, right: str) -> int:
    max_len = min(len(left), len(right), 2000)
    for size in range(max_len, 10, -1):
        if left[-size:] == right[:size]:
            return size
    return 0


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = text.replace("\u0e07", " ")
    text = re.sub(r"([A-Za-z])-\n\s*([a-z])", r"\1\2", text)
    text = _strip_running_lines(text)
    text = _strip_running_fragments(text)
    text = _repair_known_word_jams(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _strip_running_lines(text: str) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and _RUNNING_LINE_RE.match(stripped):
            continue
        kept.append(line)
    return "\n".join(kept)


def _strip_running_fragments(text: str) -> str:
    text = re.sub(
        rf"\s+{_SECTION_SYMBOL_RE}\s*\d{{1,2}}\.\d{{2}}(?:\.\d{{3}}){{0,2}}\s+[A-Z][A-Z &,]{{3,}}(?=\s|$)",
        " ",
        text,
    )
    text = re.sub(
        rf"\s+[A-Z][A-Z &,]{{3,}}\s+{_SECTION_SYMBOL_RE}\s*\d{{1,2}}\.\d{{2}}(?:\.\d{{3}}){{0,2}}(?=\s|$)",
        " ",
        text,
    )
    for title in _RUNNING_TITLE_NAMES:
        text = re.sub(
            rf"\s+{_SECTION_SYMBOL_RE}\s*\d{{1,2}}\.\d{{2}}(?:\.\d{{3}}){{0,2}}\s+{re.escape(title)}\s+",
            " ",
            text,
        )
        text = re.sub(
            rf"\s+{re.escape(title)}\s+{_SECTION_SYMBOL_RE}\s*\d{{1,2}}\.\d{{2}}(?:\.\d{{3}}){{0,2}}\s+",
            " ",
            text,
        )
    text = re.sub(r"\s+(?:Supp\. No\. \d+\s+)?CD\d+:\d+(?:\.\d+)?(?: CODE)?(?=\s|$)", " ", text)
    text = re.sub(r"\s+\[The next page is CD\d+:\d+(?:\.\d+)?\]\s+", " ", text)
    return text


def _repair_known_word_jams(text: str) -> str:
    replacements = {
        "procurementdocuments": "procurement documents",
        "electronictransmissions": "electronic transmissions",
        "intergovernmentalagreements": "intergovernmental agreements",
        "professionalservices": "professional services",
    }
    for bad, good in replacements.items():
        text = re.sub(bad, good, text, flags=re.IGNORECASE)
    return text


def _clean_heading(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip(" .;:-")
    return cleaned[:180] or "Reserved"


def _chapter_name(text: str, offset: int, chapter_number: str) -> str:
    window = text[max(0, offset - 2500) : offset]
    pattern = re.compile(_CHAPTER_RE_TEMPLATE.format(chapter=re.escape(chapter_number)))
    matches = list(pattern.finditer(window))
    if not matches:
        return f"Chapter {chapter_number}"
    raw = matches[-1].group("name")
    raw = re.split(r"\n|Sec\.|\d{1,2}\.\d{2}\.\d{3}", raw, maxsplit=1)[0]
    return _clean_heading(raw.title())


def _sort_key(value: str) -> int:
    pieces = value.split(".")
    return int(pieces[0]) * 1000 + int(pieces[1])


def _build_proof(
    *,
    document,
    chunks: list,
    payload: dict[str, Any],
    chunk_size: int,
    chunk_overlap: int,
    force_reingest: bool,
) -> dict[str, Any]:
    sample = chunks[0] if chunks else None
    vector = sample.embedding if sample is not None else None
    counts = _empty_counts()
    counts.update(
        {
            "titles_created": len(payload["titles"]),
            "chapters_created": len(payload["chapters"]),
            "sections_created": len(payload["sections"]),
            "versions_created": len(payload["versions"]),
        }
    )
    return {
        "civiccore_document_id": str(document.id),
        "civiccore_document_status": document.ingestion_status.value
        if hasattr(document.ingestion_status, "value")
        else str(document.ingestion_status),
        "civiccore_file_type": document.file_type,
        "civiccore_file_size": document.file_size,
        "civiccore_document_chunk_count": document.chunk_count,
        "civiccore_document_metadata": document.metadata_ or {},
        "civiccore_page_count": (document.metadata_ or {}).get("page_count"),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "force_reingest": force_reingest,
        "queryable_chunk_rows": len(chunks),
        "embedded_chunk_rows": sum(1 for chunk in chunks if chunk.embedding is not None),
        "parsed_character_count": sum(len(str(chunk.content_text)) for chunk in chunks),
        "sample_chunk_index": sample.chunk_index if sample else None,
        "sample_chunk_page": sample.page_number if sample else None,
        "sample_chunk_text": sample.content_text[:320] if sample else None,
        "sample_vector_dim": len(vector) if vector is not None else None,
        "civiccode_counts": counts,
        "first_section": payload["sections"][0] if payload["sections"] else None,
        "source_id": LONGMONT_SOURCE_ID,
    }


def _async_db_url(db_url: str) -> str:
    if db_url.startswith("postgresql+asyncpg://"):
        return db_url
    if db_url.startswith("postgresql+psycopg2://"):
        return db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    return db_url


__all__ = [
    "LONGMONT_SOURCE_ID",
    "SharedIngestionError",
    "SharedIngestionImport",
    "build_longmont_import_from_shared_ingestion",
    "build_longmont_import_from_shared_ingestion_sync",
]
