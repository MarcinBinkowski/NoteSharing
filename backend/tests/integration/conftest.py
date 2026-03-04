import os
import uuid as _uuid
from collections.abc import AsyncGenerator, Generator
from dataclasses import dataclass
from datetime import UTC, timedelta
from datetime import datetime as _datetime
from typing import Any

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from app.core.auth import create_access_token, create_refresh_token
from app.core.config import Settings
from app.core.constants import AUTH_ACCESS_COOKIE, AUTH_REFRESH_COOKIE
from app.core.rate_limit import LIMITER
from app.main import create_app
from app.repositories.firestore_user import FirestoreUserRepository
from app.schemas.user import User

_TEST_SECRET_KEY = "b323255fb490ae5f38eb6b60282fc2a3"  # pragma: allowlist secret
_TEST_SESSION_KEY = "9c215875bc78a42c8a027eb4481f0da4"  # pragma: allowlist secret
_TEST_PROJECT = "test-project"
_FIRESTORE_PORT = 8080


@pytest.fixture(scope="session")
def firestore_emulator() -> Generator[str]:
    """Start a Firestore emulator container once for the whole test session."""
    with (
        DockerContainer("google/cloud-sdk:emulators")
        .with_exposed_ports(_FIRESTORE_PORT)
        .with_command(
            f"gcloud beta emulators firestore start "
            f"--project={_TEST_PROJECT} --host-port=0.0.0.0:{_FIRESTORE_PORT}"
        )
        .waiting_for(
            LogMessageWaitStrategy("Dev App Server is now running").with_startup_timeout(
                timedelta(seconds=120)
            )
        ) as container
    ):
        host = container.get_container_host_ip()
        port = container.get_exposed_port(_FIRESTORE_PORT)
        emulator_host = f"{host}:{port}"
        os.environ["FIRESTORE_EMULATOR_HOST"] = emulator_host
        try:
            yield emulator_host
        finally:
            del os.environ["FIRESTORE_EMULATOR_HOST"]


def _make_test_settings() -> Settings:
    return Settings(
        DEBUG=True,
        DATABASE_BACKEND="firestore",
        SQLITE_URL="sqlite+aiosqlite:///unused",  # required field; not used with firestore
        SECRET_KEY=_TEST_SECRET_KEY,
        SESSION_SECRET_KEY=_TEST_SESSION_KEY,
        GCP_PROJECT_ID=_TEST_PROJECT,
        GOOGLE_CLIENT_ID="test-client-id",
        GOOGLE_CLIENT_SECRET="test-client-secret",  # pragma: allowlist secret
        BACKEND_URL="http://localhost:8000",
        FRONTEND_URL="http://localhost:5173",
        CORS_ORIGINS=["http://localhost:5173"],
    )


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Clear in-memory rate-limit counters so each test starts with a clean slate."""
    if hasattr(LIMITER, "_storage") and hasattr(LIMITER._storage, "reset"):
        LIMITER._storage.reset()


@pytest_asyncio.fixture(autouse=True)
async def _clear_firestore_data(firestore_emulator: str) -> AsyncGenerator[None]:
    """Wipe all Firestore documents after each test for isolation."""
    yield
    async with httpx.AsyncClient() as ac:
        await ac.delete(
            f"http://{firestore_emulator}/emulator/v1/projects/{_TEST_PROJECT}"
            f"/databases/(default)/documents"
        )


@pytest_asyncio.fixture
async def client(firestore_emulator: str) -> AsyncGenerator[AsyncClient]:
    app = create_app(_make_test_settings())
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac,
    ):
        yield ac


@pytest_asyncio.fixture
async def plain_note_id(client: AsyncClient) -> str:
    """ID of a freshly created plain (no password, no expiry) note."""
    resp = await client.post("/api/notes", json={"content": "plain note content"})
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest_asyncio.fixture
async def password_note(client: AsyncClient) -> tuple[str, str]:
    """(id, password) of a created password-protected note."""
    password = "test-password-123"  # pragma: allowlist secret
    resp = await client.post(
        "/api/notes",
        json={"content": "secret content", "password": password},
    )
    assert resp.status_code == 201
    return resp.json()["id"], password


@pytest_asyncio.fixture
async def burn_note_id(client: AsyncClient) -> str:
    """ID of a created burn-after-reading note."""
    resp = await client.post(
        "/api/notes",
        json={"content": "burn after reading", "burn_after_reading": True},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest_asyncio.fixture
async def expiring_note_id(client: AsyncClient) -> str:
    """ID of a created note that expires in 60 minutes."""
    resp = await client.post(
        "/api/notes",
        json={"content": "expiring content", "expires_in_minutes": 60},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Authenticated-user fixtures
# Each test that requests authed_client / authed_user gets its own isolated
# Firestore app instance with a pre-seeded real user.
# ---------------------------------------------------------------------------


@dataclass
class _AuthContext:
    app: Any  # FastAPI instance
    user: User
    access_token: str
    refresh_token: str


@pytest_asyncio.fixture
async def _auth_context(firestore_emulator: str) -> AsyncGenerator[_AuthContext]:
    """Fresh app + a test user inserted into the Firestore emulator."""
    app = create_app(_make_test_settings())
    async with app.router.lifespan_context(app):
        settings = app.state.settings
        repo = FirestoreUserRepository(app.state.db_client)
        user = await repo.upsert_by_google_id(
            User(
                id=_uuid.uuid4(),
                google_id="test-google-id",
                email="testuser@example.com",
                created_at=_datetime.now(UTC),
            )
        )
        access_token = create_access_token(user.id, app_settings=settings)
        refresh_token = create_refresh_token(user.id, app_settings=settings)
        yield _AuthContext(
            app=app,
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
        )


@pytest_asyncio.fixture
async def authed_client(_auth_context: _AuthContext) -> AsyncGenerator[AsyncClient]:
    """AsyncClient with valid auth cookies for the test user."""
    async with AsyncClient(
        transport=ASGITransport(app=_auth_context.app),
        base_url="http://test",
        cookies={
            AUTH_ACCESS_COOKIE: _auth_context.access_token,
            AUTH_REFRESH_COOKIE: _auth_context.refresh_token,
        },
    ) as ac:
        yield ac


@pytest.fixture
def authed_user(_auth_context: _AuthContext) -> User:
    """The User object that authed_client is authenticated as."""
    return _auth_context.user


@pytest_asyncio.fixture
async def unauthenticated_client(
    _auth_context: _AuthContext,
) -> AsyncGenerator[AsyncClient]:
    """Cookie-free client sharing the same Firestore emulator DB as authed_client."""
    async with AsyncClient(
        transport=ASGITransport(app=_auth_context.app),
        base_url="http://test",
    ) as ac:
        yield ac
