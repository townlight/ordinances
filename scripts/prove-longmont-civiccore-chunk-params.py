from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
from typing import Any
import uuid

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


PARAMETER_SETS = (
    {"label": "civiccore-original-proof", "chunk_size": 900, "chunk_overlap": 90},
    {"label": "civiccode-pr61-proof", "chunk_size": 500, "chunk_overlap": 50},
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest the Longmont PDF through civiccore.ingest.ingest_file twice "
            "to prove chunk-count differences come from chunking parameters."
        )
    )
    parser.add_argument(
        "--pdf",
        default=str(
            Path(__file__).resolve().parents[2]
            / "longmont-code-corpus"
            / "Longmont, CO Code of Ordinances.pdf"
        ),
    )
    parser.add_argument(
        "--db-url",
        default=os.environ.get("CIVICCODE_SOURCE_REGISTRY_DB_URL") or os.environ.get("DATABASE_URL"),
    )
    parser.add_argument("--actor", default="chunk-params-proof@longmont.example.gov")
    parser.add_argument(
        "--run-id",
        default=datetime.now(UTC).strftime("%Y%m%d%H%M%S"),
        help="Unique suffix for the two CivicCore data sources created by this proof.",
    )
    args = parser.parse_args()
    if not args.db_url:
        raise SystemExit("Set --db-url or CIVICCODE_SOURCE_REGISTRY_DB_URL before running proof.")
    output = asyncio.run(
        _run_dual_ingest(
            pdf_path=Path(args.pdf),
            db_url=args.db_url,
            actor=args.actor,
            run_id=args.run_id,
        )
    )
    print("CIVICCORE-LONGMONT-CHUNK-PARAM-PROOF")
    print(json.dumps(output, indent=2, default=str))
    return 0


async def _run_dual_ingest(*, pdf_path: Path, db_url: str, actor: str, run_id: str) -> dict[str, Any]:
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")
    os.environ["DATABASE_URL"] = db_url
    from civiccore.migrations.runner import upgrade_to_head

    upgrade_to_head()
    engine = create_async_engine(_async_db_url(db_url), future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            await _ensure_civiccore_actor(session, actor=actor)
            results = []
            for params in PARAMETER_SETS:
                results.append(
                    await _ingest_one_parameter_set(
                        session=session,
                        pdf_path=pdf_path,
                        actor=actor,
                        run_id=run_id,
                        label=params["label"],
                        chunk_size=params["chunk_size"],
                        chunk_overlap=params["chunk_overlap"],
                    )
                )
            return {
                "pdf": str(pdf_path),
                "pdf_size_bytes": pdf_path.stat().st_size,
                "run_id": run_id,
                "results": results,
            }
    finally:
        await engine.dispose()


async def _ingest_one_parameter_set(
    *,
    session,
    pdf_path: Path,
    actor: str,
    run_id: str,
    label: str,
    chunk_size: int,
    chunk_overlap: int,
) -> dict[str, Any]:
    from civiccore.ingest import DataSource, DocumentChunk, SourceType, ingest_file

    source = DataSource(
        name=f"Longmont chunk parameter proof {run_id} {label}",
        source_type=SourceType.FILE_SYSTEM,
        connection_config={
            "path": str(pdf_path.parent),
            "proof": "civiccode-pr61-c2-dual-ingest",
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
        created_by=_actor_uuid(actor),
    )
    session.add(source)
    await session.commit()
    await session.refresh(source)
    document = await ingest_file(
        session=session,
        file_path=pdf_path,
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
    sample = chunks[0] if chunks else None
    vector = sample.embedding if sample is not None else None
    return {
        "label": label,
        "source_id": str(source.id),
        "document_id": str(document.id),
        "status": document.ingestion_status.value
        if hasattr(document.ingestion_status, "value")
        else str(document.ingestion_status),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "document_chunk_count": document.chunk_count,
        "document_chunks_rows": len(chunks),
        "embedded_chunks_rows": sum(1 for chunk in chunks if chunk.embedding is not None),
        "page_count": (document.metadata_ or {}).get("page_count"),
        "stored_chunk_text_chars": sum(len(str(chunk.content_text)) for chunk in chunks),
        "sample_chunk_index": sample.chunk_index if sample else None,
        "sample_page_number": sample.page_number if sample else None,
        "sample_token_count": sample.token_count if sample else None,
        "sample_vector_dim": len(vector) if vector is not None else None,
        "sample_chunk_text": sample.content_text[:320] if sample else None,
    }


async def _ensure_civiccore_actor(session, *, actor: str) -> None:
    actor_uuid = _actor_uuid(actor)
    existing = await session.execute(sa.text("SELECT id FROM public.users WHERE id = :id"), {"id": actor_uuid})
    if existing.first() is not None:
        return
    await session.execute(
        sa.text(
            """
            INSERT INTO public.users
                (id, email, hashed_password, is_active, is_superuser, is_verified, full_name, role)
            VALUES
                (:id, :email, 'civiccode-longmont-chunk-proof-local-only', true, false, true,
                 'CivicCode Longmont Chunk Proof', 'staff')
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"id": actor_uuid, "email": actor[:320] if "@" in actor else "chunk-params-proof@example.gov"},
    )
    await session.commit()


def _actor_uuid(actor: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, actor.strip().lower() or "chunk-params-proof@example.gov")


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


if __name__ == "__main__":
    raise SystemExit(main())
