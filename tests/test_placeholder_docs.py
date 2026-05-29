"""Contract tests for CivicCode documentation using real-wire hash examples."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_civiccode_docs_do_not_publish_placeholder_sha_examples() -> None:
    offenders = []
    for path in [ROOT / "README.md", ROOT / "USER-MANUAL.md"]:
        text = path.read_text(encoding="utf-8")
        if "sha256:abc123" in text:
            offenders.append(str(path))

    assert offenders == []
