from typing import Any

from fastapi import Request

from app.core.config import Settings
from app.db.firestore import get_firestore_client
from app.db.sqlite import open_sqlite


async def open_db_client(settings: Settings) -> Any:
	if settings.DATABASE_BACKEND == "firestore":
		return get_firestore_client(settings)
	if settings.DATABASE_BACKEND == "sqlite":
		return await open_sqlite(settings.SQLITE_URL)
	msg = f"Unsupported database backend: {settings.DATABASE_BACKEND}"
	raise RuntimeError(msg)


async def close_db_client(settings: Settings, db_client: Any) -> None:
	if settings.DATABASE_BACKEND == "sqlite" and db_client is not None:
		await db_client.close()


async def check_db_health(request: Request) -> None:
	settings: Settings = request.app.state.settings
	if settings.DATABASE_BACKEND == "sqlite":
		await request.app.state.db_client.execute("SELECT 1")
		return

	if settings.DATABASE_BACKEND == "firestore":
		marker_doc = request.app.state.db_client.collection("__healthcheck__").document(
			"__healthcheck__"
		)
		await marker_doc.get()
		return

	msg = f"Unsupported database backend: {settings.DATABASE_BACKEND}"
	raise RuntimeError(msg)
