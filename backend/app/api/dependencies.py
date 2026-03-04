from typing import Annotated, Any

from fastapi import Cookie, Depends, Request

from app.core.auth import extract_token_subject
from app.core.constants import AUTH_ACCESS_COOKIE
from app.core.exceptions import NotAuthorizedError
from app.repositories.firestore_note import FirestoreNoteRepository
from app.repositories.firestore_user import FirestoreUserRepository
from app.repositories.protocols import NoteRepository, UserRepository
from app.repositories.sqlite_note import SqliteNoteRepository
from app.repositories.sqlite_user import SqliteUserRepository
from app.schemas.user import User


def build_notes_repo(backend: str, db_client: Any) -> NoteRepository:
    if backend == "firestore":
        return FirestoreNoteRepository(db_client)
    if backend == "sqlite":
        return SqliteNoteRepository(db_client)
    msg = f"Unsupported database backend: {backend}"
    raise RuntimeError(msg)


def build_users_repo(backend: str, db_client: Any) -> UserRepository:
    if backend == "firestore":
        return FirestoreUserRepository(db_client)
    if backend == "sqlite":
        return SqliteUserRepository(db_client)
    msg = f"Unsupported database backend: {backend}"
    raise RuntimeError(msg)


def get_notes_repo(request: Request) -> NoteRepository:
    return build_notes_repo(
        request.app.state.settings.DATABASE_BACKEND,
        request.app.state.db_client,
    )


def get_users_repo(request: Request) -> UserRepository:
    return build_users_repo(
        request.app.state.settings.DATABASE_BACKEND,
        request.app.state.db_client,
    )


async def get_current_user_optional(
    request: Request,
    users: Annotated[UserRepository, Depends(get_users_repo)],
    access_token_cookie: Annotated[str | None, Cookie(alias=AUTH_ACCESS_COOKIE)] = None,
) -> User | None:
    if access_token_cookie is None:
        return None

    try:
        user_id = extract_token_subject(
            access_token_cookie,
            expected_type="access",
            app_settings=request.app.state.settings,
        )
    except ValueError:
        return None

    return await users.get_by_id(user_id)


async def get_current_user_required(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    if user is None:
        raise NotAuthorizedError("Authentication required")
    return user
