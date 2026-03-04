import pytest
from httpx import AsyncClient

from app.schemas.user import User

pytestmark = pytest.mark.integration



async def test_get_current_user_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


async def test_get_current_user_authenticated(
    authed_client: AsyncClient, authed_user: User
) -> None:
    response = await authed_client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(authed_user.id)
    assert data["email"] == authed_user.email
    assert data["name"] == authed_user.name


async def test_get_current_user_invalid_token(client: AsyncClient) -> None:
    client.cookies.set("notes_at", "not-a-valid-token", domain="test")
    response = await client.get("/api/auth/me")
    assert response.status_code == 401



async def test_logout_invalidates_session(authed_client: AsyncClient) -> None:
    resp = await authed_client.post("/api/auth/logout")
    assert resp.status_code == 204


async def test_refresh_no_token_returns_401(client: AsyncClient) -> None:
    response = await client.post("/api/auth/refresh")
    assert response.status_code == 401


async def test_refresh_with_valid_token_returns_204(
    authed_client: AsyncClient,
) -> None:
    response = await authed_client.post("/api/auth/refresh")
    assert response.status_code == 204


async def test_refresh_with_invalid_token_returns_401(client: AsyncClient) -> None:
    client.cookies.set("notes_rt", "garbage-token", domain="test")
    response = await client.post("/api/auth/refresh")
    assert response.status_code == 401
