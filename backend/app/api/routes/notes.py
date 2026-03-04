import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import (
    get_current_user_optional,
    get_current_user_required,
    get_notes_repo,
)
from app.core.rate_limit import LIMITER
from app.repositories.protocols import NoteRepository
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
from app.services import note_service

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post(
    "",
    response_model=NoteCreatedResponse,
    status_code=201,
    operation_id="createNote",
)
@LIMITER.limit("30/minute")
async def create_note(
    request: Request,
    body: NoteCreateRequest,
    notes: Annotated[NoteRepository, Depends(get_notes_repo)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> NoteCreatedResponse:
    return await note_service.create_note(notes, body, owner=current_user)


@router.get(
    "/my",
    response_model=list[NoteListItem],
    operation_id="listMyNotes",
)
async def list_my_notes(
    notes: Annotated[NoteRepository, Depends(get_notes_repo)],
    current_user: Annotated[User, Depends(get_current_user_required)],
) -> list[NoteListItem]:
    return await note_service.list_my_notes(notes, current_user)


@router.get(
    "/{note_id}",
    response_model=NoteMetadataResponse,
    operation_id="getNoteMetadata",
)
async def get_note_metadata(
    note_id: uuid.UUID,
    notes: Annotated[NoteRepository, Depends(get_notes_repo)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> NoteMetadataResponse:
    return await note_service.get_metadata(notes, note_id, current_user=current_user)


@router.post(
    "/{note_id}/content",
    response_model=NoteContentResponse,
    operation_id="getNoteContent",
)
@LIMITER.limit("30/minute")
async def get_note_content(
    note_id: uuid.UUID,
    request: Request,
    notes: Annotated[NoteRepository, Depends(get_notes_repo)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    body: NoteAccessRequest | None = None,
) -> NoteContentResponse:
    """Retrieve note content, verifying the password when required.

    POST is used intentionally: the password must travel in the request body,
    not in the URL (which would appear in server logs and browser history).
    """
    return await note_service.get_content(notes, note_id, body=body, current_user=current_user)


@router.delete(
    "/{note_id}",
    status_code=204,
    operation_id="deleteNote",
)
async def delete_note(
    note_id: uuid.UUID,
    notes: Annotated[NoteRepository, Depends(get_notes_repo)],
    current_user: Annotated[User, Depends(get_current_user_required)],
) -> None:
    await note_service.delete_note(notes, note_id, current_user=current_user)
