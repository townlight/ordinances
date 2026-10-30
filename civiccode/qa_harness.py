"""Citation-grounded Q&A helpers for CivicCode."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Any, Callable

from civiccode.ai_answer import CivicCodeAIError, generate_local_llm_answer
from civiccode.citation_contract import refusal


SECTION_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+){1,4}\b")
LEGAL_DETERMINATION_PATTERNS = (
    "am i allowed",
    "can i",
    "may i",
    "is it legal",
    "is this legal",
    "do i need a permit",
    "will i be fined",
    "is this a violation",
    "at my address",
    "at 123",
)
QUESTION_STOPWORDS = {
    "about",
    "code",
    "does",
    "section",
    "what",
}


@dataclass(frozen=True, slots=True)
class QuestionRequestContext:
    """Normalized input for deterministic question answering."""

    question: str
    section_number: str | None = None
    as_of: date | None = None


def looks_like_legal_determination(question: str) -> bool:
    normalized = " ".join(question.lower().split())
    return any(pattern in normalized for pattern in LEGAL_DETERMINATION_PATTERNS)


def extract_section_number(question: str) -> str | None:
    match = SECTION_NUMBER_RE.search(question)
    return match.group(0) if match else None


def legal_determination_refusal() -> dict[str, Any]:
    return refusal(
        "CivicCode cannot decide whether a specific person, property, or fact pattern complies with the code.",
        "Ask staff for a determination. You can still ask what an adopted section says or provide an exact section number.",
        "legal_determination",
    )


def no_citation_refusal(question: str) -> dict[str, Any]:
    return refusal(
        f"No single adopted code section could be cited for question: {question!r}.",
        "Ask with an exact section number or use narrower terms that match adopted code text.",
        "no_citation",
    )


def ambiguous_citation_refusal(question: str, count: int) -> dict[str, Any]:
    return refusal(
        f"{count} adopted code sections matched question: {question!r}.",
        "Ask with an exact section number so CivicCode can cite one authoritative section.",
        "ambiguous_citation",
    )


def build_grounded_answer(
    context: QuestionRequestContext,
    *,
    search: Callable[[str], dict[str, Any]],
    build_citation: Callable[[str, date | None], dict[str, Any]],
    use_local_llm: bool = True,
    generate_answer: Callable[..., dict[str, Any]] = generate_local_llm_answer,
) -> dict[str, Any]:
    """Answer only when one adopted section and citation can ground the response."""
    if looks_like_legal_determination(context.question):
        return legal_determination_refusal()

    section_number = context.section_number or extract_section_number(context.question)
    if section_number is None:
        code_results = _search_code_results(context.question, search)
        if not code_results:
            return no_citation_refusal(context.question)
        if len(code_results) > 1:
            return ambiguous_citation_refusal(context.question, len(code_results))
        section_number = code_results[0]["section_number"]

    citation_payload = build_citation(section_number, context.as_of)
    if citation_payload.get("status") != "ok":
        return citation_payload

    citation = citation_payload["citation"]
    deterministic_answer = (
        "The cited section says: "
        f"{citation['body_text']} "
        f"Source: {citation['citation_text']}. "
        "This is not a legal determination."
    )
    payload = {
        "status": "ok",
        "question": context.question,
        "matched_section_number": section_number,
        "answer": deterministic_answer,
        "citations": [citation],
        "classification": "information_not_determination",
        "legal_determination": "not_provided",
        "code_answer_behavior": "citation_grounded",
        "llm_provider": "not_configured",
        "ai_review_required": False,
        "ai_authority": "deterministic_citation_extract",
        "review_note": "City staff remain responsible for legal interpretations and determinations.",
    }
    if not use_local_llm:
        payload["llm_provider"] = "not_requested"
        return payload
    try:
        ai_payload = generate_answer(question=context.question, citation=citation)
    except CivicCodeAIError as exc:
        payload["llm_error"] = {
            "message": str(exc),
            "fix": (
                "Start the local Ollama runtime, pull the configured model, or retry "
                "with deterministic citation extraction while staff review the source."
            ),
        }
        return payload

    payload.update(ai_payload)
    payload["answer"] = (
        f"{ai_payload['answer']} Source: {citation['citation_text']}. "
        "This is not a legal determination."
    )
    return payload


def _search_code_results(
    question: str,
    search: Callable[[str], dict[str, Any]],
) -> list[dict[str, Any]]:
    direct = _code_results(search(question))
    if direct:
        return direct

    deduped: dict[str, dict[str, Any]] = {}
    for token in _query_tokens(question):
        for result in _code_results(search(token)):
            deduped[result["section_number"]] = result
    return list(deduped.values())


def _code_results(search_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        result
        for result in search_payload["results"]
        if result.get("result_type") == "code_section" and result.get("section_number")
    ]


def _query_tokens(question: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", question.lower())
        if len(token) > 3 and token not in QUESTION_STOPWORDS
    ]
