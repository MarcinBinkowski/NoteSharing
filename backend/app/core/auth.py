import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from jwt import PyJWKClient

from app.core.config import Settings
from app.core.config import settings as default_settings


def _effective_settings(app_settings: Settings | None) -> Settings:
    return app_settings if app_settings is not None else default_settings


def _create_token(
    user_id: uuid.UUID,
    token_type: str,
    expires_delta: timedelta,
    app_settings: Settings | None = None,
) -> str:
    settings = _effective_settings(app_settings)
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "exp": now + expires_delta,
        "iat": now,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: uuid.UUID, app_settings: Settings | None = None) -> str:
    settings = _effective_settings(app_settings)
    return _create_token(
        user_id,
        "access",
        timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
        app_settings=settings,
    )


def create_refresh_token(user_id: uuid.UUID, app_settings: Settings | None = None) -> str:
    settings = _effective_settings(app_settings)
    return _create_token(
        user_id,
        "refresh",
        timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        app_settings=settings,
    )


def extract_token_subject(
    token: str,
    *,
    expected_type: Literal["access", "refresh"],
    app_settings: Settings | None = None,
) -> uuid.UUID:
    """Decode token and return UUID subject for the expected token type.

    Raises:
        ValueError: if token is invalid, has wrong type, or has invalid subject claim.
    """
    settings = _effective_settings(app_settings)
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise ValueError("Invalid token") from exc

    if payload.get("type") != expected_type:
        raise ValueError("Invalid token type")

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise ValueError("Invalid token subject")

    try:
        return uuid.UUID(subject)
    except ValueError as exc:
        raise ValueError("Invalid token subject") from exc


GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105
GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"

_google_jwks_client = PyJWKClient(GOOGLE_JWKS_URL, cache_jwk_set=True, lifespan=3600)


async def verify_google_id_token(
    id_token_str: str,
    *,
    nonce: str | None = None,
    app_settings: Settings | None = None,
) -> dict[str, Any]:
    """Verify and decode a Google OIDC id_token."""
    settings = _effective_settings(app_settings)
    try:
        signing_key = await asyncio.to_thread(
            _google_jwks_client.get_signing_key_from_jwt, id_token_str
        )
        payload: dict[str, Any] = jwt.decode(
            id_token_str,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.GOOGLE_CLIENT_ID,
            issuer="https://accounts.google.com",
        )
    except jwt.PyJWTError as exc:
        raise ValueError("Invalid Google ID token") from exc

    if nonce is not None and payload.get("nonce") != nonce:
        raise ValueError("Nonce mismatch in Google ID token")

    return payload
