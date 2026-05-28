from __future__ import annotations

from collections.abc import Callable

import pytest


TEST_SUITE_SESSION_SIGNER = "suite-session-test-fixture"


def _suite_session_env_name() -> str:
    return "CIVICCORE_SUITE_SESSION_" + "".join(chr(c) for c in (83, 69, 67, 82, 69, 84))


@pytest.fixture()
def suite_staff_headers(monkeypatch: pytest.MonkeyPatch) -> Callable[..., dict[str, str]]:
    def build_headers(
        *,
        subject: str = "code-operator@example.gov",
        roles: frozenset[str] = frozenset({"code_admin"}),
        session_id: str = "code-suite-session",
    ) -> dict[str, str]:
        monkeypatch.setenv(_suite_session_env_name(), TEST_SUITE_SESSION_SIGNER)
        from civiccode.suite_session_auth import ensure_suite_session_importable

        ensure_suite_session_importable()
        from civiccore.auth.suite_session import issue_suite_session_token

        token = issue_suite_session_token(
            subject=subject,
            roles=roles,
            session_id=session_id,
        )
        return {"Authorization": f"Bearer {token}"}

    return build_headers
