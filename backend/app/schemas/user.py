import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    google_id: str | None = None
    email: EmailStr
    created_at: datetime
