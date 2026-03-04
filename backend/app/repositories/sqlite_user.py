import uuid
from datetime import UTC, datetime

import aiosqlite

from app.schemas.user import User


class SqliteUserRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    @staticmethod
    def _row_to_user(row: aiosqlite.Row) -> User:
        dt = datetime.fromisoformat(row["created_at"])
        return User(
            id=uuid.UUID(row["id"]),
            google_id=row["google_id"],
            email=row["email"],
            created_at=dt if dt.tzinfo else dt.replace(tzinfo=UTC),
        )

    async def create(self, user: User) -> User:
        await self._conn.execute(
            """
            INSERT INTO users (id, google_id, email, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(user.id),
                user.google_id,
                user.email.lower(),
                user.created_at.isoformat(),
            ),
        )
        await self._conn.commit()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        async with self._conn.execute("SELECT * FROM users WHERE id = ?", (str(user_id),)) as cur:
            row = await cur.fetchone()
        return self._row_to_user(row) if row else None

    async def _get_by_google_id(self, google_id: str) -> User | None:
        async with self._conn.execute(
            "SELECT * FROM users WHERE google_id = ?", (google_id,)
        ) as cur:
            row = await cur.fetchone()
        return self._row_to_user(row) if row else None

    async def upsert_by_google_id(self, user: User) -> User:
        if not user.google_id:
            return await self.create(user)
        # Atomic upsert: INSERT new row or UPDATE email/name on google_id conflict.
        # A single statement eliminates the TOCTOU race between concurrent OAuth callbacks.
        async with self._conn.execute(
            """
            INSERT INTO users (id, google_id, email, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(google_id) DO UPDATE SET
                email = excluded.email
            RETURNING id, google_id, email, created_at
            """,
            (
                str(user.id),
                user.google_id,
                user.email.lower(),
                user.created_at.isoformat(),
            ),
        ) as cur:
            row = await cur.fetchone()
        await self._conn.commit()
        return self._row_to_user(row)  # type: ignore[arg-type]
