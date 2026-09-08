from pydantic import BaseModel, ConfigDict, Field

VALID_JOB_STATUSES = {"queued", "running", "completed", "failed", "cancelled", "dead_letter"}


class JobStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., min_length=1, max_length=50)
    expected_version: int | None = Field(None, ge=1)

    def model_post_init(self, __context):
        if self.status not in VALID_JOB_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(VALID_JOB_STATUSES))}")
