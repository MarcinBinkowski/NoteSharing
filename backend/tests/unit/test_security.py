import uuid

import jwt
import pytest

from app.core.auth import extract_token_subject
from app.core.config import Settings
from app.core.security import hash_password, verify_password

pytestmark = pytest.mark.unit

_TEST_SECRET_KEY = "b323255fb490ae5f38eb6b60282fc2a3"
_TEST_SESSION_KEY = "9c215875bc78a42c8a027eb4481f0da4"

_TEST_SETTINGS = Settings(
    DEBUG=True,
    DATABASE_BACKEND="sqlite",
    SQLITE_URL="sqlite+aiosqlite:///unused",
    GCP_PROJECT_ID="test-project",
    GOOGLE_CLIENT_ID="test-client-id",
    GOOGLE_CLIENT_SECRET="test-client-secret",
    BACKEND_URL="http://localhost:8000",
    FRONTEND_URL="http://localhost:5173",
    CORS_ORIGINS=["http://localhost:5173"],
    SECRET_KEY=_TEST_SECRET_KEY,
    SESSION_SECRET_KEY=_TEST_SESSION_KEY,
)


async def test_hash_and_verify() -> None:
    pw = "mysecretpassword"
    hashed = await hash_password(pw)
    assert await verify_password(pw, hashed) is True


async def test_wrong_password() -> None:
    pw = "mysecretpassword"
    hashed = await hash_password(pw)
    assert await verify_password("wrongpassword", hashed) is False


async def test_hash_is_different_from_plain() -> None:
    pw = "mysecretpassword"
    hashed = await hash_password(pw)
    assert hashed != pw


def _make_token(sub: str, token_type: str, settings: Settings) -> str:
    """Create a raw JWT with arbitrary sub and type for testing edge cases."""
    from datetime import UTC, datetime, timedelta

    payload = {
        "sub": sub,
        "type": token_type,
        "exp": datetime.now(UTC) + timedelta(minutes=15),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def test_extract_token_subject_rejects_wrong_type() -> None:
    """A refresh token must not be accepted where an access token is expected."""
    token = _make_token(str(uuid.uuid4()), "refresh", _TEST_SETTINGS)
    with pytest.raises(ValueError, match="Invalid token type"):
        extract_token_subject(token, expected_type="access", app_settings=_TEST_SETTINGS)


def test_extract_token_subject_rejects_invalid_uuid_sub() -> None:
    """A token whose sub claim is not a valid UUID must be rejected."""
    token = _make_token("not-a-uuid", "access", _TEST_SETTINGS)
    with pytest.raises(ValueError, match="Invalid token subject"):
        extract_token_subject(token, expected_type="access", app_settings=_TEST_SETTINGS)
