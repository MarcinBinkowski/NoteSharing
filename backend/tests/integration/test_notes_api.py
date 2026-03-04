import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_create_note_anonymous(client: AsyncClient) -> None:
    response = await client.post("/api/notes", json={"content": "Hello, world!"})
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["path"] == f"/notes/{data['id']}"
    assert data["burn_after_reading"] is False
    assert data["expires_at"] is None


async def test_create_note_with_expiry(client: AsyncClient) -> None:
    response = await client.post(
        "/api/notes", json={"content": "Expiring note", "expires_in_minutes": 60}
    )
    assert response.status_code == 201
    assert response.json()["expires_at"] is not None


async def test_create_note_empty_content_rejected(client: AsyncClient) -> None:
    response = await client.post("/api/notes", json={"content": "   "})
    assert response.status_code == 422


async def test_create_note_invalid_expiry_rejected(client: AsyncClient) -> None:
    response = await client.post("/api/notes", json={"content": "test", "expires_in_minutes": 0})
    assert response.status_code == 422


async def test_get_note_metadata(client: AsyncClient, plain_note_id: str) -> None:
    response = await client.get(f"/api/notes/{plain_note_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == plain_note_id
    assert data["requires_password"] is False
    assert data["burn_after_reading"] is False
    assert data["is_owner"] is False
    assert "created_at" in data
    assert data["expires_at"] is None


async def test_get_note_metadata_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/api/notes/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_get_note_metadata_password_protected(
    client: AsyncClient, password_note: tuple[str, str]
) -> None:
    note_id, _ = password_note
    response = await client.get(f"/api/notes/{note_id}")
    assert response.status_code == 200
    assert response.json()["requires_password"] is True


async def test_get_note_metadata_expiring(client: AsyncClient, expiring_note_id: str) -> None:
    response = await client.get(f"/api/notes/{expiring_note_id}")
    assert response.status_code == 200
    assert response.json()["expires_at"] is not None


async def test_get_note_content(client: AsyncClient, plain_note_id: str) -> None:
    response = await client.post(f"/api/notes/{plain_note_id}/content", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == plain_note_id
    assert data["content"] == "plain note content"
    assert data["burn_after_reading"] is False


async def test_get_note_content_not_found(client: AsyncClient) -> None:
    response = await client.post(f"/api/notes/{uuid.uuid4()}/content", json={})
    assert response.status_code == 404


async def test_get_note_content_correct_password(
    client: AsyncClient, password_note: tuple[str, str]
) -> None:
    note_id, password = password_note
    response = await client.post(f"/api/notes/{note_id}/content", json={"password": password})
    assert response.status_code == 200
    assert response.json()["content"] == "secret content"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"password": "wrong"},  # pragma: allowlist secret
    ],
)
async def test_get_note_content_bad_password(
    client: AsyncClient, password_note: tuple[str, str], payload: dict
) -> None:
    note_id, _ = password_note
    response = await client.post(f"/api/notes/{note_id}/content", json=payload)
    assert response.status_code == 401


async def test_burn_after_reading_first_read_succeeds(
    client: AsyncClient, burn_note_id: str
) -> None:
    response = await client.post(f"/api/notes/{burn_note_id}/content", json={})
    assert response.status_code == 200
    assert response.json()["content"] == "burn after reading"


async def test_burn_after_reading_second_read_fails(
    client: AsyncClient, burn_note_id: str
) -> None:
    first = await client.post(f"/api/notes/{burn_note_id}/content", json={})
    assert first.status_code == 200

    second = await client.post(f"/api/notes/{burn_note_id}/content", json={})
    assert second.status_code == 404


async def test_delete_note_unauthenticated(client: AsyncClient, plain_note_id: str) -> None:
    response = await client.delete(f"/api/notes/{plain_note_id}")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/notes/my  (requires authentication)
# ---------------------------------------------------------------------------


async def test_list_notes_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/api/notes/my")
    assert response.status_code == 401


async def test_list_notes_empty_for_new_user(authed_client: AsyncClient) -> None:
    response = await authed_client.get("/api/notes/my")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_notes_returns_own_notes(authed_client: AsyncClient) -> None:
    for content in ("first note", "second note", "third note"):
        resp = await authed_client.post("/api/notes", json={"content": content})
        assert resp.status_code == 201

    response = await authed_client.get("/api/notes/my")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 3
    contents = {item["content_preview"] for item in items}
    assert contents == {"first note", "second note", "third note"}


# ---------------------------------------------------------------------------
# is_owner flag
# ---------------------------------------------------------------------------


async def test_note_is_owner_when_authenticated(authed_client: AsyncClient) -> None:
    create_resp = await authed_client.post("/api/notes", json={"content": "my note"})
    note_id = create_resp.json()["id"]

    meta_resp = await authed_client.get(f"/api/notes/{note_id}")
    assert meta_resp.status_code == 200
    assert meta_resp.json()["is_owner"] is True


async def test_note_not_owner_when_unauthenticated(
    authed_client: AsyncClient, unauthenticated_client: AsyncClient
) -> None:
    create_resp = await authed_client.post("/api/notes", json={"content": "my note"})
    note_id = create_resp.json()["id"]

    meta_resp = await unauthenticated_client.get(f"/api/notes/{note_id}")
    assert meta_resp.status_code == 200
    assert meta_resp.json()["is_owner"] is False


# ---------------------------------------------------------------------------
# Authenticated note deletion
# ---------------------------------------------------------------------------


async def test_authenticated_can_delete_own_note(authed_client: AsyncClient) -> None:
    create_resp = await authed_client.post("/api/notes", json={"content": "delete me"})
    assert create_resp.status_code == 201
    note_id = create_resp.json()["id"]

    delete_resp = await authed_client.delete(f"/api/notes/{note_id}")
    assert delete_resp.status_code == 204

    get_resp = await authed_client.get(f"/api/notes/{note_id}")
    assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# Owner bypasses password
# ---------------------------------------------------------------------------


async def test_owner_reads_password_note_without_password(
    authed_client: AsyncClient,
) -> None:
    create_resp = await authed_client.post(
        "/api/notes",
        json={"content": "owner secret", "password": "hunter2"},  # pragma: allowlist secret
    )
    assert create_resp.status_code == 201
    note_id = create_resp.json()["id"]

    # Owner can read with NO password
    read_resp = await authed_client.post(f"/api/notes/{note_id}/content", json={})
    assert read_resp.status_code == 200
    assert read_resp.json()["content"] == "owner secret"
