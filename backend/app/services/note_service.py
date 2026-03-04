import uuid
from datetime import UTC, datetime, timedelta

from app.core.exceptions import (
    InvalidPasswordError,
    NoteExpiredError,
    NoteNotFoundError,
)
from app.core.security import hash_password, verify_password
from app.repositories.protocols import NoteRepository
from app.schemas.note import Note
from app.schemas.requests import (
    NoteAccessRequest,
    NoteCreateRequest,
)
from app.schemas.responses import (
    NoteContentResponse,
    NoteCreatedResponse,
    NoteListItem,
    NoteMetadataResponse,
)
from app.schemas.user import User

_PREVIEW_MAX_LENGTH = 80


def _to_list_item(note: Note) -> NoteListItem:
    preview = note.content[:_PREVIEW_MAX_LENGTH] + (
        "\u2026" if len(note.content) > _PREVIEW_MAX_LENGTH else ""
    )
    return NoteListItem(
        id=note.id,
        requires_password=note.requires_password,
        burn_after_reading=note.burn_after_reading,
        content_preview=preview,
        created_at=note.created_at,
        expires_at=note.expires_at,
    )


def _is_owner(note: Note, current_user: User | None) -> bool:
    return current_user is not None and note.owner_id == current_user.id


async def _get_active_note(notes: NoteRepository, note_id: uuid.UUID) -> Note:
    note = await notes.get_by_id(note_id)
    if note is None:
        raise NoteNotFoundError(str(note_id))
    if note.is_expired:
        await notes.delete_if_exists(note.id)
        raise NoteExpiredError(str(note_id))
    return note


async def create_note(
    notes: NoteRepository,
    req: NoteCreateRequest,
    owner: User | None = None,
) -> NoteCreatedResponse:
    note_id = uuid.uuid4()
    now = datetime.now(UTC)
    expires_at = (
        now + timedelta(minutes=req.expires_in_minutes) if req.expires_in_minutes else None
    )

    note = Note(
        id=note_id,
        content=req.content,
        password_hash=await hash_password(req.password) if req.password else None,
        owner_id=owner.id if owner else None,
        burn_after_reading=req.burn_after_reading,
        created_at=now,
        expires_at=expires_at,
    )

    await notes.create(note)

    return NoteCreatedResponse(
        id=note_id,
        path=f"/notes/{note_id}",
        expires_at=expires_at,
        burn_after_reading=req.burn_after_reading,
    )


async def get_metadata(
    notes: NoteRepository,
    note_id: uuid.UUID,
    current_user: User | None = None,
) -> NoteMetadataResponse:
    note = await _get_active_note(notes, note_id)

    return NoteMetadataResponse(
        id=note.id,
        requires_password=note.requires_password,
        burn_after_reading=note.burn_after_reading,
        is_owner=_is_owner(note, current_user),
        created_at=note.created_at,
        expires_at=note.expires_at,
    )


async def get_content(
    notes: NoteRepository,
    note_id: uuid.UUID,
    body: NoteAccessRequest | None = None,
    current_user: User | None = None,
) -> NoteContentResponse:
    note = await _get_active_note(notes, note_id)
    is_owner = _is_owner(note, current_user)

    password = body.password if body else None
    if note.requires_password and not is_owner:
        password_hash = note.password_hash
        if password_hash is None:
            raise InvalidPasswordError()
        if password is None:
            await verify_password("", password_hash)
            raise InvalidPasswordError()
        if not await verify_password(password, password_hash):
            raise InvalidPasswordError()

    response = NoteContentResponse(
        id=note.id,
        content=note.content,
        created_at=note.created_at,
        expires_at=note.expires_at,
        burn_after_reading=note.burn_after_reading,
    )

    if note.burn_after_reading and not is_owner:
        was_deleted = await notes.delete_if_exists(note.id)
        if not was_deleted:
            raise NoteNotFoundError(str(note_id))

    return response


async def delete_note(
    notes: NoteRepository,
    note_id: uuid.UUID,
    current_user: User,
) -> None:
    note = await notes.get_by_id(note_id)
    if note is None:
        raise NoteNotFoundError(str(note_id))

    if note.owner_id != current_user.id:
        # Intentionally return 404 instead of 403: returning 403 would reveal
        # that the note exists, allowing enumeration of other users' notes.
        raise NoteNotFoundError(str(note_id))

    await notes.delete_if_exists(note.id)


async def list_my_notes(
    notes: NoteRepository,
    current_user: User,
) -> list[NoteListItem]:
    rows = await notes.list_by_owner(current_user.id)
    return [_to_list_item(n) for n in rows]
