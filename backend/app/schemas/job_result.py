from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobResultUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: dict[str, Any] | list[Any] | str | None = Field(default=None)
