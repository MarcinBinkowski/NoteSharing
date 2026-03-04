from google.cloud.firestore_v1 import AsyncClient

from app.core.config import Settings


def get_firestore_client(app_settings: Settings) -> AsyncClient:
    return AsyncClient(
        project=app_settings.GCP_PROJECT_ID or None,
        database=app_settings.FIRESTORE_DATABASE,
    )
