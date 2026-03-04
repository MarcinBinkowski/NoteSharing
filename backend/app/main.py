import logging
import pathlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import register_health_routes
from app.api.middleware import register_middleware
from app.api.routes import auth_router, notes_router
from app.api.spa import register_spa_routes
from app.core.config import Settings
from app.core.logging import setup_logging
from app.db import close_db_client, open_db_client

log = logging.getLogger(__name__)


def create_app(settings: Settings) -> FastAPI:
    setup_logging(log_level=settings.LOG_LEVEL)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.db_client = await open_db_client(settings)
        yield
        await close_db_client(settings, app.state.db_client)

    docs_enabled = settings.DEBUG or settings.ENABLE_DOCS_IN_PROD

    app = FastAPI(
        title=settings.APP_NAME,
        docs_url="/api/docs" if docs_enabled else None,
        openapi_url="/api/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
    )

    app.state.settings = settings

    register_middleware(app, settings)
    register_health_routes(app)

    app.include_router(notes_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")

    static_dir = pathlib.Path(__file__).resolve().parent.parent / "static"
    if static_dir.is_dir():
        register_spa_routes(app, static_dir)

    return app

