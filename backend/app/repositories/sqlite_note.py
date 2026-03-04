import uuid
from datetime import UTC, datetime

import aiosqlite

from app.core.exceptions import NoteNotFoundError
from app.schemas.note import Note


class SqliteNoteRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    @staticmethod
    def _row_to_note(row: aiosqlite.Row) -> Note:
        def _dt(val: str | None) -> datetime | None:
            if val is None:
                return None
            dt = datetime.fromisoformat(val)
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

        created_at = _dt(row["created_at"])
        if created_at is None:
            msg = "Invalid note row: missing created_at"
            raise ValueError(msg)

        return Note(
            id=uuid.UUID(row["id"]),
            content=row["content"],
            password_hash=row["password_hash"],
            owner_id=uuid.UUID(row["owner_id"]) if row["owner_id"] else None,
            burn_after_reading=bool(row["burn_after_reading"]),
            created_at=created_at,
            expires_at=_dt(row["expires_at"]),
        )

    @staticmethod
    def _iso(dt: datetime | None) -> str | None:
        if dt is None:
            return None
        return (dt if dt.tzinfo else dt.replace(tzinfo=UTC)).isoformat()

    @staticmethod
    def _uid(u: uuid.UUID) -> str:
        return str(u)

    async def create(self, note: Note) -> Note:
        await self._conn.execute(
            """
            INSERT INTO notes
                (id, content, password_hash, owner_id, burn_after_reading,
                 created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self._uid(note.id),
                note.content,
                note.password_hash,
                self._uid(note.owner_id) if note.owner_id else None,
                int(note.burn_after_reading),
                self._iso(note.created_at),
                self._iso(note.expires_at),
            ),
        )
        await self._conn.commit()
        return note

    async def get_by_id(self, note_id: uuid.UUID) -> Note | None:
        async with self._conn.execute(
            "SELECT * FROM notes WHERE id = ?", (self._uid(note_id),)
        ) as cur:
            row = await cur.fetchone()
        return self._row_to_note(row) if row else None

    async def delete_if_exists(self, note_id: uuid.UUID) -> bool:
        """Atomically delete via a single DELETE … RETURNING id, avoiding TOCTOU."""
        async with self._conn.execute(
            "DELETE FROM notes WHERE id = ? RETURNING id", (self._uid(note_id),)
        ) as cur:
            deleted = await cur.fetchone()
        await self._conn.commit()
        return deleted is not None

    async def delete_expired(self) -> int:
        now = self._iso(datetime.now(UTC))
        async with self._conn.execute(
            "DELETE FROM notes WHERE expires_at IS NOT NULL AND expires_at <= ? RETURNING id",
            (now,),
        ) as cur:
            rows = list(await cur.fetchall())
        await self._conn.commit()
        return len(rows)

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Note]:
        now = self._iso(datetime.now(UTC))
        async with self._conn.execute(
            """
            SELECT * FROM notes
            WHERE owner_id = ?
              AND (expires_at IS NULL OR expires_at > ?)
            ORDER BY (expires_at IS NULL) ASC, expires_at DESC, created_at DESC
            """,
            (self._uid(owner_id), now),
        ) as cur:
            rows = await cur.fetchall()
        return [self._row_to_note(r) for r in rows]

    async def set_expires_at(self, note_id: uuid.UUID, expires_at: datetime | None) -> None:
        async with self._conn.execute(
            "UPDATE notes SET expires_at = ? WHERE id = ? RETURNING id",
            (self._iso(expires_at), self._uid(note_id)),
        ) as cur:
            row = await cur.fetchone()
        await self._conn.commit()
        if row is None:
            raise NoteNotFoundError(str(note_id))
