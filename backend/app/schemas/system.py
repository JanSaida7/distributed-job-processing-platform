from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class InfoResponse(BaseModel):
    name: str
    environment: str
    version: str