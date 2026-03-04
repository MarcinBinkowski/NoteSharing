from typing import Final

AUTH_ACCESS_COOKIE: Final[str] = "notes_at"
AUTH_REFRESH_COOKIE: Final[str] = "notes_rt"

GOOGLE_TOKEN_URL: Final[str] = "https://oauth2.googleapis.com/token"  # noqa: S105
GOOGLE_AUTH_BASE: Final[str] = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_JWKS_URL: Final[str] = "https://www.googleapis.com/oauth2/v3/certs"
