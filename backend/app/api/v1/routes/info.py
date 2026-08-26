from fastapi import APIRouter

from app.core.config import settings
from app.schemas.system import InfoResponse


router = APIRouter(tags=["system"])


@router.get("/info", response_model=InfoResponse)
def application_info() -> InfoResponse:
    return InfoResponse(
        name=settings.app_name,
        environment=settings.app_env,
        version="0.1.0",
    )