import asyncio
import uuid
from typing import Any

from app.schemas.user import User


class FirestoreUserRepository:
    _google_locks: dict[str, asyncio.Lock] = {}

    def __init__(self, client: Any) -> None:
        self._users = client.collection("users")

    def _to_doc(self, user: User) -> dict[str, Any]:
        return {
            "google_id": user.google_id,
            "email": user.email.lower(),
            "created_at": user.created_at,
        }

    def _from_doc(self, doc_id: str, data: dict[str, Any]) -> User:
        return User(
            id=uuid.UUID(doc_id),
            google_id=data.get("google_id"),
            email=data["email"],
            created_at=data["created_at"],
        )

    async def create(self, user: User) -> User:
        doc_ref = self._users.document(str(user.id))
        await doc_ref.set(self._to_doc(user))
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        doc = await self._users.document(str(user_id)).get()
        if not doc.exists:
            return None
        return self._from_doc(doc.id, doc.to_dict())

    async def _get_by_google_id(self, google_id: str) -> User | None:
        query = self._users.where("google_id", "==", google_id).limit(1)
        docs = [doc async for doc in query.stream()]
        if not docs:
            return None
        return self._from_doc(docs[0].id, docs[0].to_dict())

    async def upsert_by_google_id(self, user: User) -> User:
        if not user.google_id:
            return await self.create(user)

        lock = self._google_locks.setdefault(user.google_id, asyncio.Lock())
        async with lock:
            existing = await self._get_by_google_id(user.google_id)
            if existing:
                doc_ref = self._users.document(str(existing.id))
                updated_fields = {
                    "email": user.email.lower(),
                    "google_id": user.google_id,
                }
                await doc_ref.update(updated_fields)
                return User(
                    id=existing.id,
                    google_id=user.google_id,
                    email=user.email.lower(),
                    created_at=existing.created_at,
                )
            return await self.create(user)
