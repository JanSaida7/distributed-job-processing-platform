from fastapi import APIRouter
from redis import Redis

from app.core.config import settings
from app.schemas.system import HealthResponse


router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/queue-status")
def queue_status() -> dict[str, str]:
    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()
        return {"status": "connected", "broker": "redis"}
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {"status": "disconnected", "broker": "redis", "error": str(exc)}