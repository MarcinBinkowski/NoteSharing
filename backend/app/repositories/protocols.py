import uuid
from typing import Protocol, runtime_checkable

from app.schemas.note import Note
from app.schemas.user import User


@runtime_checkable
class NoteRepository(Protocol):
    async def create(self, note: Note) -> Note: ...

    async def get_by_id(self, note_id: uuid.UUID) -> Note | None: ...

    async def delete_if_exists(self, note_id: uuid.UUID) -> bool: ...

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Note]: ...


@runtime_checkable
class UserRepository(Protocol):
    async def create(self, user: User) -> User: ...

    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    async def upsert_by_google_id(self, user: User) -> User: ...
