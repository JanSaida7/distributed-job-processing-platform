from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    payload: dict[str, Any] | list[Any] | str | None = None

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, value: Any) -> Any:
        if value is None:
            return value
        if isinstance(value, (dict, list, str)):
            return value
        raise TypeError("payload must be a dict, list, string, or null")


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    payload: dict[str, Any] | list[Any] | str | None = None
    result: dict[str, Any] | list[Any] | str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
