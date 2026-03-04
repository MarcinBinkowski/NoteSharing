import uuid
from datetime import UTC, datetime
from typing import Any, cast

from google.cloud.firestore_v1.async_transaction import (
    async_transactional,
)
from google.cloud.firestore_v1.base_query import FieldFilter, Or

from app.core.exceptions import NoteNotFoundError
from app.schemas.note import Note


class FirestoreNoteRepository:
    def __init__(self, client: Any) -> None:
        self._client = client
        self._notes = client.collection("notes")

    def _to_doc(self, note: Note) -> dict[str, Any]:
        return {
            "content": note.content,
            "password_hash": note.password_hash,
            "owner_id": str(note.owner_id) if note.owner_id else None,
            "burn_after_reading": note.burn_after_reading,
            "created_at": note.created_at,
            "expires_at": note.expires_at,
        }

    def _from_doc(self, doc_id: str, data: dict[str, Any]) -> Note:
        return Note(
            id=uuid.UUID(doc_id),
            content=data["content"],
            password_hash=data.get("password_hash"),
            owner_id=uuid.UUID(data["owner_id"]) if data.get("owner_id") else None,
            burn_after_reading=data.get("burn_after_reading", False),
            created_at=data["created_at"],
            expires_at=data.get("expires_at"),
        )

    async def create(self, note: Note) -> Note:
        doc_ref = self._notes.document(str(note.id))
        await doc_ref.set(self._to_doc(note))
        return note

    async def get_by_id(self, note_id: uuid.UUID) -> Note | None:
        doc = await self._notes.document(str(note_id)).get()
        if not doc.exists:
            return None
        return self._from_doc(doc.id, doc.to_dict())

    async def delete_if_exists(self, note_id: uuid.UUID) -> bool:
        """Atomically delete a note and return True only if it existed."""
        doc_ref = self._notes.document(str(note_id))

        @async_transactional
        async def _delete_in_txn(transaction: Any) -> bool:
            snapshot = await doc_ref.get(transaction=transaction)
            if not snapshot.exists:
                return False
            transaction.delete(doc_ref)
            return True

        return cast(bool, await _delete_in_txn(self._client.transaction()))

    async def delete_expired(self) -> int:
        """Delete all expired notes using write batches (max 500 ops per batch)."""
        now = datetime.now(UTC)
        query = self._notes.where("expires_at", "<=", now)
        count = 0
        batch = self._client.batch()
        async for doc in query.stream():
            batch.delete(doc.reference)
            count += 1
            if count % 500 == 0:
                await batch.commit()
                batch = self._client.batch()
        if count % 500 != 0 and count > 0:
            await batch.commit()
        return count

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Note]:
        now = datetime.now(UTC)

        or_filter = Or(
            [FieldFilter("expires_at", "==", None), FieldFilter("expires_at", ">", now)]
        )

        query = (
            self._notes.where(filter=FieldFilter("owner_id", "==", str(owner_id)))
            .where(filter=or_filter)
            .order_by("expires_at", direction="DESCENDING")
            .order_by("created_at", direction="DESCENDING")
        )
        return [self._from_doc(doc.id, doc.to_dict()) async for doc in query.stream()]

    async def set_expires_at(self, note_id: uuid.UUID, expires_at: datetime | None) -> None:
        doc_ref = self._notes.document(str(note_id))
        snapshot = await doc_ref.get()
        if not snapshot.exists:
            raise NoteNotFoundError(str(note_id))
        await doc_ref.update({"expires_at": expires_at})
