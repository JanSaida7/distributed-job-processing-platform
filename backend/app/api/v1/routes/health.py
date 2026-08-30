from fastapi import APIRouter, Depends
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Job
from app.db.session import get_db
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


@router.get("/queue-metrics")
def queue_metrics(db: Session = Depends(get_db)) -> dict[str, object]:
    counts = {
        "total_jobs": db.query(Job).count(),
        "queued_jobs": db.query(Job).filter(Job.status == "queued").count(),
        "running_jobs": db.query(Job).filter(Job.status == "running").count(),
        "completed_jobs": db.query(Job).filter(Job.status == "completed").count(),
        "failed_jobs": db.query(Job).filter(Job.status == "failed").count(),
        "cancelled_jobs": db.query(Job).filter(Job.status == "cancelled").count(),
        "dead_letter_jobs": db.query(Job).filter(Job.status == "dead_letter").count(),
    }

    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()
        status = "connected"
        error = None
    except Exception as exc:  # pragma: no cover - defensive fallback
        status = "disconnected"
        error = str(exc)

    payload: dict[str, object] = {
        "status": status,
        "broker": "redis",
        "job_counts": counts,
    }
    if error is not None:
        payload["error"] = error

    return payload