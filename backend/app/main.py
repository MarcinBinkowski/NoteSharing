import logging
import pathlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from html import escape

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.middleware import register_middleware
from app.api.routes import auth_router, notes_router
from app.core.config import Settings
from app.core.logging import setup_logging
from app.db import check_db_health, close_db_client, open_db_client

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

    @app.get("/api/health", tags=["health"], operation_id="healthCheck")
    async def health_check(request: Request) -> dict[str, str]:
        """Liveness + readiness probe. Returns 503 when the database is unreachable."""
        try:
            await check_db_health(request)
        except Exception as exc:
            log.warning("health_check_db_error: %s", exc)
            raise HTTPException(status_code=503, detail="Database unavailable") from exc
        return {"status": "ok"}

    app.include_router(notes_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")

    static_dir = pathlib.Path(__file__).resolve().parent.parent / "static"
    if static_dir.is_dir():
        assets_dir = static_dir / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str, request: Request) -> FileResponse | HTMLResponse:
            candidate = (static_dir / full_path).resolve()
            if candidate.is_file() and candidate.is_relative_to(static_dir):
                return FileResponse(candidate)
            if request.url.path.startswith("/api/"):
                escaped = escape(request.url.path)
                return HTMLResponse(
                    content=(
                        "<!doctype html>"
                        "<html lang='en'>"
                        "<head>"
                        "<meta charset='utf-8'/>"
                        "<meta name='viewport' content='width=device-width,initial-scale=1'/>"
                        "<title>404 - Not Found</title>"
                        "<style>"
                        "body{font-family:ui-sans-serif,system-ui,sans-serif;max-width:48rem;"
                        "margin:3rem auto;padding:0 1rem;line-height:1.5;color:#1f2937}"
                        "h1{margin:0 0 .5rem}code{background:#f3f4f6;padding:.2rem .4rem;"
                        "border-radius:.3rem}"
                        "</style>"
                        "</head>"
                        "<body>"
                        "<h1>404 - Endpoint Not Found</h1>"
                        "<p>The requested API endpoint does not exist:</p>"
                        f"<p><code>{escaped}</code></p>"
                        "<p>Please check the URL and method.</p>"
                        "</body>"
                        "</html>"
                    ),
                    status_code=404,
                )
            return FileResponse(static_dir / "index.html")

    return app
