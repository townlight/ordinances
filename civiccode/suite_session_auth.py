"""CivicCore suite-session adapter for CivicCode staff endpoints."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException


CODE_STAFF_ROLES = frozenset({"code_admin", "staff"})
_DEFAULT_TOKEN_TTL = timedelta(minutes=15)
_MAX_LOCAL_REVOCATIONS = 4096
_SUITE_SESSION_KEY_ENV_VAR = "CIVICCORE_SUITE_SESSION_SECRET"
_REVOCATION_FILE_ENV_VAR = "CIVICCORE_SUITE_SESSION_REVOCATION_FILE"
_REVOKED_SESSION_IDS: dict[str, int] = {}


class SuiteSessionConfigError(RuntimeError):
    """Raised when suite-session signing configuration is unavailable."""


@dataclass(frozen=True)
class SuiteSessionPrincipal:
    """Validated CivicCore suite-session identity."""

    subject: str
    roles: frozenset[str]
    session_id: str


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode((raw + padding).encode("ascii"))


def _signing_key() -> str:
    value = os.getenv(_SUITE_SESSION_KEY_ENV_VAR, "").strip()
    if not value:
        raise SuiteSessionConfigError(
            f"{_SUITE_SESSION_KEY_ENV_VAR} must be set before issuing or validating suite session tokens."
        )
    return value


def issue_suite_session_token(
    *,
    subject: str,
    roles: frozenset[str],
    session_id: str,
    expires_at: datetime | None = None,
) -> str:
    """Issue a compact HMAC-signed suite-session token."""

    expiry = expires_at or (datetime.now(UTC) + _DEFAULT_TOKEN_TTL)
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=UTC)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "roles": sorted(roles),
        "sid": session_id,
        "exp": int(expiry.timestamp()),
    }
    signing_input = ".".join(
        [
            _b64url_encode(json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")),
            _b64url_encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = hmac.new(_signing_key().encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def validate_suite_session_token(
    token: str,
    *,
    required_roles: frozenset[str],
) -> SuiteSessionPrincipal:
    """Validate a CivicCore suite-session token and return its staff principal."""

    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".", 2)
    except ValueError as exc:
        raise PermissionError("suite session token is invalid") from exc

    signing_input = f"{encoded_header}.{encoded_payload}"
    expected_signature = hmac.new(
        _signing_key().encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    try:
        actual_signature = _b64url_decode(encoded_signature)
    except Exception as exc:  # pragma: no cover
        raise PermissionError("suite session signature is invalid") from exc
    if not hmac.compare_digest(actual_signature, expected_signature):
        raise PermissionError("suite session signature is invalid")

    try:
        payload = json.loads(_b64url_decode(encoded_payload))
        header = json.loads(_b64url_decode(encoded_header))
    except Exception as exc:  # pragma: no cover
        raise PermissionError("suite session token is invalid") from exc
    if header != {"alg": "HS256", "typ": "JWT"}:
        raise PermissionError("suite session token has an unsupported header")

    subject = str(payload.get("sub") or "").strip()
    session_id = str(payload.get("sid") or "").strip()
    roles = frozenset(str(role).strip().lower() for role in payload.get("roles", []) if str(role).strip())
    expires_at = int(payload.get("exp") or 0)
    if not subject or not session_id or not roles:
        raise PermissionError("suite session token is missing required claims")
    if expires_at <= int(time.time()):
        raise PermissionError("suite session token expired")
    _load_shared_revocations()
    _prune_revocations()
    if session_id in _REVOKED_SESSION_IDS:
        raise PermissionError("suite session was revoked")

    normalized_required = frozenset(role.strip().lower() for role in required_roles if role.strip())
    if roles.isdisjoint(normalized_required):
        raise PermissionError("suite session lacks a required staff role")
    return SuiteSessionPrincipal(subject=subject, roles=roles, session_id=session_id)


def revoke_suite_session(session_id: str) -> None:
    """Revoke a local fallback suite session by id."""

    normalized = session_id.strip()
    if normalized:
        _REVOKED_SESSION_IDS[normalized] = int((datetime.now(UTC) + _DEFAULT_TOKEN_TTL).timestamp())
        _prune_revocations()
        _persist_shared_revocations()


def _load_validator():
    try:
        from civiccore.auth.suite_session import (  # type: ignore[import-not-found]
            SuiteSessionConfigError as ImportedSuiteSessionConfigError,
            validate_suite_session_token as imported_validate_suite_session_token,
        )

        return ImportedSuiteSessionConfigError, imported_validate_suite_session_token
    except ModuleNotFoundError:
        return SuiteSessionConfigError, validate_suite_session_token


def _revocation_file() -> Path | None:
    raw = os.getenv(_REVOCATION_FILE_ENV_VAR, "").strip()
    if not raw:
        return None
    return Path(raw)


def _load_shared_revocations() -> None:
    path = _revocation_file()
    if path is None or not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(data, dict):
        return
    for session_id, expires_at in data.items():
        if isinstance(session_id, str) and isinstance(expires_at, int):
            _REVOKED_SESSION_IDS[session_id] = expires_at
    _prune_revocations()


def _persist_shared_revocations() -> None:
    path = _revocation_file()
    if path is None:
        return
    _prune_revocations()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(_REVOKED_SESSION_IDS, handle, sort_keys=True)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def _prune_revocations() -> None:
    now = int(datetime.now(UTC).timestamp())
    expired = [session_id for session_id, expires_at in _REVOKED_SESSION_IDS.items() if expires_at <= now]
    for session_id in expired:
        _REVOKED_SESSION_IDS.pop(session_id, None)
    if len(_REVOKED_SESSION_IDS) <= _MAX_LOCAL_REVOCATIONS:
        return
    by_expiry = sorted(_REVOKED_SESSION_IDS.items(), key=lambda item: item[1])
    for session_id, _expires_at in by_expiry[: len(_REVOKED_SESSION_IDS) - _MAX_LOCAL_REVOCATIONS]:
        _REVOKED_SESSION_IDS.pop(session_id, None)


def validate_staff_bearer_token(authorization: str | None) -> SuiteSessionPrincipal | None:
    """Return a suite-session principal when a bearer token is present."""

    value = (authorization or "").strip()
    if not value:
        return None
    scheme, _, token = value.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=401,
            detail={
                "message": "CivicCode staff endpoints require a CivicCore suite session bearer token.",
                "fix": "Send Authorization: Bearer <suite-session-token> from the CivicSuite staff shell.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    config_error, validator = _load_validator()
    try:
        return validator(token.strip(), required_roles=CODE_STAFF_ROLES)
    except config_error as exc:
        raise HTTPException(
            status_code=401,
            detail={
                "message": "CivicCore suite session validation is not configured for CivicCode.",
                "fix": "Set CIVICCORE_SUITE_SESSION_SECRET to the shared CivicSuite staff-session signing key.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "CivicCore suite session was rejected for this CivicCode staff endpoint.",
                "fix": (
                    "Sign in again through the CivicSuite staff shell with the code_admin role, "
                    "then retry with a fresh suite session bearer token."
                ),
            },
        ) from exc


def suite_session_required_error() -> HTTPException:
    """Build the actionable error used when legacy headers are insufficient."""

    return HTTPException(
        status_code=401,
        detail={
            "message": "CivicCode source creation requires a CivicCore suite session.",
            "fix": (
                "Send Authorization: Bearer <suite-session-token> from the CivicSuite staff shell; "
                "legacy X-CivicCode-Role/X-CivicCode-Actor headers alone cannot create sources."
            ),
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
