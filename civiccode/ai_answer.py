"""Local-LLM answer generation for CivicCode."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


class CivicCodeAIError(RuntimeError):
    """Raised when the configured local LLM cannot produce a bounded answer."""


@dataclass(frozen=True, slots=True)
class LocalLLMConfig:
    provider: str
    base_url: str
    model: str
    timeout_seconds: float


def load_local_llm_config() -> LocalLLMConfig | None:
    """Return local Ollama config when AI answering is enabled."""
    mode = os.environ.get("CIVICCODE_AI_MODE", "").strip().lower()
    base_url = os.environ.get("CIVICCODE_OLLAMA_URL", "").strip()
    if mode not in {"ollama", "local_ollama"} and not base_url:
        return None
    return LocalLLMConfig(
        provider="ollama",
        base_url=(base_url or "http://127.0.0.1:11434").rstrip("/"),
        model=os.environ.get("CIVICCODE_OLLAMA_MODEL", "gemma4:e4b").strip() or "gemma4:e4b",
        timeout_seconds=float(os.environ.get("CIVICCODE_OLLAMA_TIMEOUT_SECONDS", "20")),
    )


def build_llm_prompt(*, question: str, citation: dict[str, Any]) -> str:
    """Build a source-bounded prompt that forbids legal determinations."""
    return (
        "You are CivicCode, a municipal code assistant. Answer only from the cited "
        "municipal code text below. Do not decide whether a person, property, or "
        "fact pattern complies with the law. Do not add uncited rules. Keep the "
        "answer concise, cite the exact section, and state that staff review is "
        "required for interpretations.\n\n"
        f"Question: {question}\n\n"
        f"Citation: {citation['citation_text']}\n"
        f"Authoritative text: {citation['body_text']}\n\n"
        "Answer:"
    )


def generate_local_llm_answer(
    *,
    question: str,
    citation: dict[str, Any],
    config: LocalLLMConfig | None = None,
) -> dict[str, Any]:
    """Call a local Ollama runtime and return a staff-reviewable answer."""
    resolved = config or load_local_llm_config()
    if resolved is None:
        raise CivicCodeAIError(
            "Local LLM answering is not configured. Set CIVICCODE_AI_MODE=ollama "
            "and CIVICCODE_OLLAMA_URL for the city runtime."
        )

    prompt = build_llm_prompt(question=question, citation=citation)
    body = json.dumps(
        {
            "model": resolved.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1},
        }
    ).encode("utf-8")
    request = Request(
        f"{resolved.base_url}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=resolved.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise CivicCodeAIError(
            "Local LLM call failed. Confirm Ollama is running locally, the model is "
            "pulled, and the CivicCode container can reach CIVICCODE_OLLAMA_URL."
        ) from exc

    answer = str(payload.get("response", "")).strip()
    if not answer:
        raise CivicCodeAIError(
            "Local LLM returned an empty response. Retry after checking the Ollama model."
        )
    return {
        "answer": answer,
        "llm_provider": resolved.provider,
        "llm_model": resolved.model,
        "ai_review_required": True,
        "ai_authority": "non_authoritative_staff_review_required",
        "prompt_contract": "single_citation_source_bounded_no_legal_determination",
    }
