import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.schemas.note import Note

pytestmark = pytest.mark.unit


def test_is_expired_no_expiry() -> None:
    note = Note(
        id=uuid.uuid4(),
        content="hello",
        created_at=datetime.now(UTC),
        expires_at=None,
    )
    assert note.is_expired is False


def test_is_expired_future() -> None:
    note = Note(
        id=uuid.uuid4(),
        content="hello",
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    assert note.is_expired is False


def test_is_expired_past() -> None:
    note = Note(
        id=uuid.uuid4(),
        content="hello",
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    assert note.is_expired is True


def test_is_expired_naive_datetime() -> None:
    note = Note(
        id=uuid.uuid4(),
        content="hello",
        created_at=datetime.now(UTC),
        expires_at=datetime(2000, 1, 1),  # naive and in the past
    )
    assert note.is_expired is True


def test_requires_password() -> None:
    note = Note(
        id=uuid.uuid4(),
        content="hello",
        password_hash="somehash",
        created_at=datetime.now(UTC),
    )
    assert note.requires_password is True


def test_no_password_required() -> None:
    note = Note(
        id=uuid.uuid4(),
        content="hello",
        created_at=datetime.now(UTC),
    )
    assert note.requires_password is False


def test_burn_after_reading_default() -> None:
    note = Note(
        id=uuid.uuid4(),
        content="hello",
        created_at=datetime.now(UTC),
    )
    assert note.burn_after_reading is False


def test_from_attributes() -> None:
    class FakeRow:
        id = uuid.uuid4()
        content = "hello"
        password_hash = None
        owner_id = None
        burn_after_reading = False
        created_at = datetime.now(UTC)
        expires_at = None

    note = Note.model_validate(FakeRow())
    assert note.content == "hello"
