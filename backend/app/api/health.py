import logging

from fastapi import FastAPI, HTTPException, Request

from app.db import check_db_health

log = logging.getLogger(__name__)


async def health_check(request: Request) -> dict[str, str]:
    """Liveness + readiness probe. Returns 503 when the database is unreachable."""
    try:
        await check_db_health(request)
    except Exception as exc:
        log.warning("health_check_db_error: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok"}


def register_health_routes(app: FastAPI) -> None:
    app.get("/api/health", tags=["health"], operation_id="healthCheck")(health_check)
