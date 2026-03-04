import logging
import secrets
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.rate_limit import LIMITER

logger = logging.getLogger(__name__)


def register_middleware(app: FastAPI, settings: Settings) -> None:
    app_settings = settings

    app.state.limiter = LIMITER
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    session_key = app_settings.SESSION_SECRET_KEY or app_settings.SECRET_KEY
    app.add_middleware(
        SessionMiddleware,
        secret_key=session_key,
        session_cookie="notes_oauth_session",
        path="/api/auth",
        https_only=app_settings.BACKEND_URL.startswith("https://"),
        same_site="lax",
        max_age=15 * 60,
    )

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_error(_req: Request, _exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

    @app.exception_handler(AppError)
    async def _app_error(_req: Request, exc: AppError) -> JSONResponse:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unhandled_error(req: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(req.state, "request_id", None)
        logger.exception(
            "unhandled_server_error method=%s path=%s request_id=%s",
            req.method,
            req.url.path,
            request_id,
        )
        response = JSONResponse({"detail": "Internal server error"}, status_code=500)
        if request_id is not None:
            response.headers["X-Request-ID"] = request_id
        return response

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';",
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), camera=(), microphone=(), payment=()",
        )
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        if not app_settings.DEBUG:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
            )
        return response

    @app.middleware("http")
    async def request_logging(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = secrets.token_hex(8)
        request.state.request_id = request_id
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
            status_code = response.status_code if response is not None else 500
            logger.info(
                "%s %s %d %.1fms",
                request.method,
                request.url.path,
                status_code,
                elapsed_ms,
            )
