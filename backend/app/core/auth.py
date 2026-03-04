import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt

from app.core.config import Settings
from app.core.jwk import GOOGLE_JWK_CLIENT


def _create_token(
    user_id: uuid.UUID,
    token_type: str,
    expires_delta: timedelta,
    app_settings: Settings,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "exp": now + expires_delta,
        "iat": now,
    }
    return jwt.encode(payload, app_settings.SECRET_KEY, algorithm=app_settings.JWT_ALGORITHM)


def create_access_token(user_id: uuid.UUID, app_settings: Settings) -> str:
    return _create_token(
        user_id,
        "access",
        timedelta(minutes=app_settings.JWT_ACCESS_EXPIRE_MINUTES),
        app_settings=app_settings,
    )


def create_refresh_token(user_id: uuid.UUID, app_settings: Settings) -> str:
    return _create_token(
        user_id,
        "refresh",
        timedelta(days=app_settings.JWT_REFRESH_EXPIRE_DAYS),
        app_settings=app_settings,
    )


def extract_token_subject(
    token: str,
    *,
    expected_type: Literal["access", "refresh"],
    app_settings: Settings,
) -> uuid.UUID:
    """Decode token and return UUID subject for the expected token type.

    Raises:
        ValueError: if token is invalid, has wrong type, or has invalid subject claim.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            app_settings.SECRET_KEY,
            algorithms=[app_settings.JWT_ALGORITHM],
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


async def verify_google_id_token(
    id_token_str: str,
    *,
    nonce: str | None = None,
    app_settings: Settings,
) -> dict[str, Any]:
    """Verify and decode a Google OIDC id_token."""
    try:
        signing_key = await asyncio.to_thread(
            GOOGLE_JWK_CLIENT.get_signing_key_from_jwt, id_token_str
        )
        payload: dict[str, Any] = jwt.decode(
            id_token_str,
            signing_key.key,
            algorithms=["RS256"],
            audience=app_settings.GOOGLE_CLIENT_ID,
            issuer="https://accounts.google.com",
        )
    except jwt.PyJWTError as exc:
        raise ValueError("Invalid Google ID token") from exc

    if nonce is not None and payload.get("nonce") != nonce:
        raise ValueError("Nonce mismatch in Google ID token")

    return payload
