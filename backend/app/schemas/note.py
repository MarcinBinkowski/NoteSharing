import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class Note(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    password_hash: str | None = Field(None, exclude=True)
    owner_id: uuid.UUID | None = None
    burn_after_reading: bool = False
    created_at: datetime
    expires_at: datetime | None = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        return datetime.now(UTC) >= expires

    @property
    def requires_password(self) -> bool:
        return self.password_hash is not None
