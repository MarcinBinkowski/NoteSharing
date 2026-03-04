"""Export the FastAPI OpenAPI schema to ../frontend/openapi.json.

Runs without a real .env by supplying placeholder values for all required
fields — the schema export only needs the routes to be registered, not real
credentials or a live database connection.
"""

import json
import pathlib

from app.core.config import Settings
from app.main import create_app

_DUMMY = Settings(
    SECRET_KEY="x",  # noqa: S106
    SESSION_SECRET_KEY="x",  # noqa: S106
    SQLITE_URL="sqlite+aiosqlite:///:memory:",
    GCP_PROJECT_ID="dev",
    GOOGLE_CLIENT_ID="dev",
    GOOGLE_CLIENT_SECRET="dev",  # noqa: S106
    BACKEND_URL="http://localhost:8000",
    FRONTEND_URL="http://localhost:5173",
    CORS_ORIGINS=["http://localhost:5173"],
    DEBUG=True,
)

app = create_app(_DUMMY)
schema = app.openapi()

out = pathlib.Path(__file__).resolve().parent.parent.parent / "frontend" / "openapi.json"
out.write_text(json.dumps(schema, indent=2) + "\n")
print(f"Written {out}")
