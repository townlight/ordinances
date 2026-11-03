from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import sys

import os

import pytest

SIBLING_TOWNLIGHT_CORE = Path(__file__).resolve().parents[1].parent / "townlight_core"
if SIBLING_TOWNLIGHT_CORE.is_dir() and str(SIBLING_TOWNLIGHT_CORE) not in sys.path:
    sys.path.insert(0, str(SIBLING_TOWNLIGHT_CORE))
if SIBLING_TOWNLIGHT_CORE.is_dir():
    import townlight_core
    import townlight_core.auth

    townlight_core_path = str(SIBLING_TOWNLIGHT_CORE / "townlight_core")
    townlight_core_auth_path = str(SIBLING_TOWNLIGHT_CORE / "townlight_core" / "auth")
    if townlight_core_path not in townlight_core.__path__:
        townlight_core.__path__.append(townlight_core_path)
    if townlight_core_auth_path not in townlight_core.auth.__path__:
        townlight_core.auth.__path__.append(townlight_core_auth_path)


TEST_SUITE_SESSION_SIGNER = "suite-session-test-fixture"


def _suite_session_env_name() -> str:
    return "TOWNLIGHT_CORE_SUITE_SESSION_SECRET"


def build_suite_staff_headers(
    *,
    subject: str = "clerk@example.gov",
    roles: frozenset[str] = frozenset({"code_admin"}),
    session_id: str = "code-suite-session",
) -> dict[str, str]:
    os.environ[_suite_session_env_name()] = TEST_SUITE_SESSION_SIGNER
    from townlight_core.auth.suite_session import issue_suite_session_token

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
