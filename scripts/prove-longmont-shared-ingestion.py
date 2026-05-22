from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from civiccode.import_connectors import ImportConnectorRepository, job_to_dict  # noqa: E402
from civiccode.citation_contract import build_citation_payload  # noqa: E402
from civiccode.qa_harness import QuestionRequestContext, build_grounded_answer  # noqa: E402
from civiccode.section_lifecycle import SectionLifecycleRepository  # noqa: E402
from civiccode.shared_ingestion import build_longmont_import_from_shared_ingestion_sync  # noqa: E402
from civiccode.source_registry import SourceRegistryRepository, source_to_public_dict  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prove full Longmont PDF ingestion through CivicCore into CivicCode."
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
    parser.add_argument("--actor", default="shared-ingestion-proof@longmont.example.gov")
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        default=None,
        help="Search query to prove. May be supplied more than once.",
    )
    parser.add_argument(
        "--question",
        default="What does the Longmont code say about public access to procurement documents?",
    )
    parser.add_argument(
        "--answer-section-number",
        default=None,
        help="Also prove a direct-section Q&A lookup for this section; organic Q&A always uses the top search result.",
    )
    parser.add_argument(
        "--force-reingest",
        action="store_true",
        help="Delete the existing Longmont CivicCore document for this source/hash before ingesting.",
    )
    args = parser.parse_args()
    if not args.db_url:
        raise SystemExit("Set --db-url or CIVICCODE_SOURCE_REGISTRY_DB_URL before running proof.")

    os.environ.setdefault("CIVICCODE_EMBEDDING_MODE", "ollama")
    shared_import = build_longmont_import_from_shared_ingestion_sync(
        pdf_path=args.pdf,
        db_url=args.db_url,
        actor=args.actor,
        force_reingest=args.force_reingest,
    )
    source_store = SourceRegistryRepository(db_url=args.db_url)
    section_store = SectionLifecycleRepository(db_url=args.db_url)
    import_store = ImportConnectorRepository(
        source_store=source_store,
        section_store=section_store,
        db_url=args.db_url,
    )
    job = import_store.run_import(shared_import.payload, actor=args.actor)
    queries = args.queries or [
        "public access to procurement documents",
        "rules for emergency purchases",
        "bid protest appeal",
        "disposal of surplus city property",
        "city manager purchasing authority",
    ]
    searches = []
    for query in queries:
        search_payload = section_store.search(query)
        searches.append(
            {
                "query": query,
                "count": search_payload["count"],
                "semantic_search": search_payload["semantic_search"],
                "top_results": search_payload["results"][:3],
            }
        )
    organic_section = _first_section_number(searches[0])
    answer_payload = build_grounded_answer(
        QuestionRequestContext(question=args.question, section_number=organic_section),
        search=section_store.search,
        build_citation=lambda section_number, as_of=None: _build_citation(
            section_store=section_store,
            source_store=source_store,
            section_number=section_number,
            as_of=as_of,
        ),
    )
    output: dict[str, Any] = {
        "proof": shared_import.proof,
        "import_job": job_to_dict(job),
        "searches": searches,
        "answer": {
            "question": args.question,
            "status": answer_payload.get("status"),
            "matched_section_number": answer_payload.get("matched_section_number"),
            "answer": answer_payload.get("answer"),
            "citations": answer_payload.get("citations", [])[:3],
            "llm_provider": answer_payload.get("llm_provider"),
            "llm_error": answer_payload.get("llm_error"),
            "mode": "organic_top_search_result",
        },
    }
    if args.answer_section_number:
        direct_payload = build_grounded_answer(
            QuestionRequestContext(question=args.question, section_number=args.answer_section_number),
            search=section_store.search,
            build_citation=lambda section_number, as_of=None: _build_citation(
                section_store=section_store,
                source_store=source_store,
                section_number=section_number,
                as_of=as_of,
            ),
        )
        output["direct_section_answer"] = {
            "question": args.question,
            "status": direct_payload.get("status"),
            "matched_section_number": direct_payload.get("matched_section_number"),
            "answer": direct_payload.get("answer"),
            "citations": direct_payload.get("citations", [])[:3],
            "llm_provider": direct_payload.get("llm_provider"),
            "llm_error": direct_payload.get("llm_error"),
            "mode": "direct_section_override",
        }
    print("CIVICCODE-LONGMONT-SHARED-INGESTION-PROOF")
    print(json.dumps(output, indent=2, default=str))
    return 0


def _first_section_number(search_payload: dict[str, Any]) -> str | None:
    results = search_payload.get("top_results") or search_payload.get("results") or []
    for result in results:
        if result.get("section_number"):
            return str(result["section_number"])
    return None


def _build_citation(
    *,
    section_store: SectionLifecycleRepository,
    source_store: SourceRegistryRepository,
    section_number: str,
    as_of,
) -> dict[str, Any]:
    context = section_store.citation_context(section_number, as_of=as_of)
    source = source_to_public_dict(source_store.get(context["version"]["source_id"]))
    return build_citation_payload(
        section=context["section"],
        version=context["version"],
        title=context["title"],
        chapter=context["chapter"],
        source=source,
        as_of=as_of.isoformat() if as_of else None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
