from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import sys

import os

import pytest

SIBLING_CIVICCORE = Path(__file__).resolve().parents[1].parent / "civiccore"
if SIBLING_CIVICCORE.is_dir() and str(SIBLING_CIVICCORE) not in sys.path:
    sys.path.insert(0, str(SIBLING_CIVICCORE))
if SIBLING_CIVICCORE.is_dir():
    import civiccore
    import civiccore.auth

    civiccore_path = str(SIBLING_CIVICCORE / "civiccore")
    civiccore_auth_path = str(SIBLING_CIVICCORE / "civiccore" / "auth")
    if civiccore_path not in civiccore.__path__:
        civiccore.__path__.append(civiccore_path)
    if civiccore_auth_path not in civiccore.auth.__path__:
        civiccore.auth.__path__.append(civiccore_auth_path)


TEST_SUITE_SESSION_SIGNER = "suite-session-test-fixture"


def _suite_session_env_name() -> str:
    return "CIVICCORE_SUITE_SESSION_SECRET"


def build_suite_staff_headers(
    *,
    subject: str = "clerk@example.gov",
    roles: frozenset[str] = frozenset({"code_admin"}),
    session_id: str = "code-suite-session",
) -> dict[str, str]:
    os.environ[_suite_session_env_name()] = TEST_SUITE_SESSION_SIGNER
    from civiccore.auth.suite_session import issue_suite_session_token

    token = issue_suite_session_token(
        subject=subject,
        roles=roles,
        session_id=session_id,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def suite_staff_headers(monkeypatch: pytest.MonkeyPatch) -> Callable[..., dict[str, str]]:
    def build_headers(
        *,
        subject: str = "code-operator@example.gov",
        roles: frozenset[str] = frozenset({"code_admin"}),
        session_id: str = "code-suite-session",
    ) -> dict[str, str]:
        monkeypatch.setenv(_suite_session_env_name(), TEST_SUITE_SESSION_SIGNER)
        return build_suite_staff_headers(subject=subject, roles=roles, session_id=session_id)

    return build_headers
