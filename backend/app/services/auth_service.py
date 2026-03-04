import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    extract_token_subject,
    verify_google_id_token,
)
from app.core.config import Settings
from app.core.exceptions import NotAuthorizedError
from app.core.jwk import GOOGLE_TOKEN_URL
from app.repositories.protocols import UserRepository
from app.schemas.responses import TokenResponse, UserResponse
from app.schemas.user import User

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)


async def google_callback(
    users: UserRepository,
    code: str,
    redirect_uri: str,
    *,
    nonce: str | None = None,
    app_settings: Settings,
) -> TokenResponse:
    user_info = await _exchange_google_code(
        code,
        redirect_uri,
        nonce=nonce,
        app_settings=app_settings,
    )

    if not user_info.get("email_verified", False):
        raise NotAuthorizedError("Google account email is not verified")

    google_id = user_info.get("sub")
    raw_email = user_info.get("email")
    if not google_id or not raw_email:
        raise NotAuthorizedError("Missing required fields in Google user info")

    email = raw_email.lower()
    name = user_info.get("name") or email

    user = User(
        id=uuid.uuid4(),
        google_id=google_id,
        email=email,
        name=name,
        created_at=datetime.now(UTC),
    )

    user = await users.upsert_by_google_id(user)

    return TokenResponse(
        access_token=create_access_token(user.id, app_settings=app_settings),
        refresh_token=create_refresh_token(user.id, app_settings=app_settings),
        user=UserResponse(id=user.id, email=user.email, name=user.name),
    )


async def refresh(
    users: UserRepository,
    refresh_token: str,
    *,
    app_settings: Settings,
) -> TokenResponse:
    try:
        user_id = extract_token_subject(
            refresh_token,
            expected_type="refresh",
            app_settings=app_settings,
        )
    except ValueError as exc:
        raise NotAuthorizedError("Invalid or expired refresh token") from exc

    user = await users.get_by_id(user_id)
    if user is None:
        raise NotAuthorizedError("User not found")

    return TokenResponse(
        access_token=create_access_token(user.id, app_settings=app_settings),
        refresh_token=create_refresh_token(user.id, app_settings=app_settings),
        user=UserResponse(id=user.id, email=user.email, name=user.name),
    )


async def user_from_access_token(
    users: UserRepository,
    access_token: str,
    *,
    app_settings: Settings,
) -> User:
    try:
        user_id = extract_token_subject(
            access_token,
            expected_type="access",
            app_settings=app_settings,
        )
    except ValueError as exc:
        raise NotAuthorizedError("Invalid or expired token") from exc

    user = await users.get_by_id(user_id)
    if user is None:
        raise NotAuthorizedError("Invalid or expired token")
    return user


async def _exchange_google_code(
    code: str,
    redirect_uri: str,
    *,
    nonce: str | None = None,
    app_settings: Settings,
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": app_settings.GOOGLE_CLIENT_ID,
                "client_secret": app_settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            log.warning(
                "google_token_exchange_failed status=%d body=%.300s",
                token_resp.status_code,
                token_resp.text,
            )
            raise NotAuthorizedError("Failed to exchange Google auth code")

        try:
            tokens = token_resp.json()
        except Exception as exc:
            raise NotAuthorizedError("Invalid response from Google token endpoint") from exc

        id_token_str = tokens.get("id_token")
        if not id_token_str:
            raise NotAuthorizedError("Missing id_token in Google response")

    try:
        return await verify_google_id_token(
            id_token_str,
            nonce=nonce,
            app_settings=app_settings,
        )
    except ValueError as exc:
        raise NotAuthorizedError(str(exc)) from exc
