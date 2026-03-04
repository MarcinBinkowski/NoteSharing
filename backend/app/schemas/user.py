import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    google_id: str | None = None
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=256)
    created_at: datetime
