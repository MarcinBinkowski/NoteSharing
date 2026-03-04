import uuid
from datetime import datetime

from pydantic import BaseModel


class NoteCreatedResponse(BaseModel):
    id: uuid.UUID
    path: str
    expires_at: datetime | None
    burn_after_reading: bool


class NoteMetadataResponse(BaseModel):
    id: uuid.UUID
    requires_password: bool
    burn_after_reading: bool
    is_owner: bool = False
    created_at: datetime
    expires_at: datetime | None


class NoteContentResponse(BaseModel):
    id: uuid.UUID
    content: str
    created_at: datetime
    expires_at: datetime | None
    burn_after_reading: bool


class NoteListItem(BaseModel):
    id: uuid.UUID
    requires_password: bool
    burn_after_reading: bool
    content_preview: str = ""
    created_at: datetime
    expires_at: datetime | None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    user: UserResponse | None = None
