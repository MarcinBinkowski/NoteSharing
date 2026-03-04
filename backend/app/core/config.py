import pathlib
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = pathlib.Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_prefix="NOTES_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Notes"
    DEBUG: bool = False
    ENABLE_DOCS_IN_PROD: bool = False

    DATABASE_BACKEND: Literal["firestore", "sqlite"] = "firestore"

    SQLITE_URL: str | None = None

    GCP_PROJECT_ID: str
    FIRESTORE_DATABASE: str = "(default)"

    SECRET_KEY: str  # noqa: S105
    SESSION_SECRET_KEY: str

    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    BACKEND_URL: str
    FRONTEND_URL: str

    RATE_LIMIT_DEFAULT: str = "60/minute"

    CORS_ORIGINS: list[str]

    LOG_LEVEL: str = "INFO"

    @model_validator(mode="after")
    def _require_sqlite_url_for_sqlite_backend(self) -> Self:
        if self.DATABASE_BACKEND == "sqlite" and not self.SQLITE_URL:
            raise ValueError("NOTES_SQLITE_URL is required when DATABASE_BACKEND=sqlite")
        return self

    @model_validator(mode="after")
    def _normalize_urls_and_cors(self) -> Self:
        backend_url = self.BACKEND_URL.rstrip("/")
        frontend_url = self.FRONTEND_URL.rstrip("/")
        self.BACKEND_URL = backend_url
        self.FRONTEND_URL = frontend_url
        cors_origins = self.CORS_ORIGINS
        if frontend_url and frontend_url not in cors_origins:
            self.CORS_ORIGINS = [*cors_origins, frontend_url]
        return self

    @model_validator(mode="after")
    def _reject_default_secret_key_in_production(self) -> Self:
        if not self.DEBUG and self.SECRET_KEY == "change-me-in-production-use-openssl-rand-hex-32":  # noqa: S105
            raise ValueError(
                "NOTES_SECRET_KEY must be set to a secure random value in production. "
                "Generate one with: openssl rand -hex 32"
            )
        if not self.DEBUG and not self.SESSION_SECRET_KEY:
            raise ValueError(
                "NOTES_SESSION_SECRET_KEY must be set in production to allow independent "
                "rotation of JWT and session secrets. "
                "Generate one with: openssl rand -hex 32"
            )
        return self
