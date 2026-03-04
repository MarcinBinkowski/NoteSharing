from google.cloud.firestore_v1 import AsyncClient

from app.core import config as app_config
from app.core.config import Settings


def get_firestore_client(app_settings: Settings | None = None) -> AsyncClient:
    settings = app_settings if app_settings is not None else app_config.settings
    return AsyncClient(
        project=settings.GCP_PROJECT_ID or None,
        database=settings.FIRESTORE_DATABASE,
    )
