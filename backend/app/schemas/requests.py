from pydantic import BaseModel, Field, field_validator


class NoteCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=100_000)
    password: str | None = Field(None, min_length=1, max_length=128)
    expires_in_minutes: int | None = Field(None, gt=0, le=43_200)
    burn_after_reading: bool = False

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        _ = cls
        stripped = v.strip()
        if not stripped:
            raise ValueError("Content cannot be blank or whitespace-only")
        return stripped


class NoteAccessRequest(BaseModel):
    password: str | None = Field(None, min_length=1, max_length=128)
