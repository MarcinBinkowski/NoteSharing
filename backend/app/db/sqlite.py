import aiosqlite

_DDL: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS notes (
        id                 TEXT PRIMARY KEY,
        content            TEXT NOT NULL,
        password_hash      TEXT,
        owner_id           TEXT,
        burn_after_reading INTEGER NOT NULL DEFAULT 0,
        created_at         TEXT NOT NULL,
        expires_at         TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        id         TEXT PRIMARY KEY,
        google_id  TEXT UNIQUE,
        email      TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_notes_owner   ON notes (owner_id)",
    "CREATE INDEX IF NOT EXISTS idx_notes_expires ON notes (expires_at)",
    "CREATE INDEX IF NOT EXISTS idx_users_google  ON users (google_id)",
]


async def open_sqlite(url: str) -> aiosqlite.Connection:
    """Open (or create) a SQLite database and initialize schema."""
    path = url.removeprefix("sqlite+aiosqlite:///").removeprefix("sqlite:///")
    conn = await aiosqlite.connect(path, isolation_level=None)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA synchronous=NORMAL")
    await conn.execute("PRAGMA cache_size=-64000")
    await conn.execute("PRAGMA foreign_keys=ON")
    for stmt in _DDL:
        await conn.execute(stmt)
    return conn
