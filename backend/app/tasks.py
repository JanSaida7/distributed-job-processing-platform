import json
from datetime import datetime, timezone

from redis import Redis

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.models import Job
from app.db.session import SessionLocal


def _mark_job_failed(job_id: int, error_message: str) -> None:
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).one_or_none()
        if job is not None:
            job.status = "failed"
            job.error_message = error_message
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def _execute_payload_task(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {"status": "processed", "payload": payload}

    task_name = payload.get("task") or payload.get("operation") or payload.get("action")

    if task_name == "sum":
        numbers = payload.get("values", [])
        total = sum(int(v) for v in numbers)
        return {"status": "processed", "operation": "sum", "result": total}

    if task_name == "echo":
        return {"status": "processed", "operation": "echo", "result": payload.get("value")}

    if task_name == "transform":
        transformed = {str(key): str(value).upper() for key, value in payload.get("mapping", {}).items()}
        return {"status": "processed", "operation": "transform", "result": transformed}

    return {"status": "processed", "operation": task_name or "generic", "payload": payload}


def enqueue_job(job_id: int, user_id: int | None = None) -> bool:
    if not settings.enable_job_queue:
        return False

    if settings.celery_task_always_eager:
        process_job(job_id, user_id)
        return True

    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()
        process_job.delay(job_id, user_id)
        return True
    except Exception as exc:
        _mark_job_failed(job_id, f"Queue unavailable: {exc}")
        return False


@celery_app.task(
    bind=True,
    name="app.process_job",
    max_retries=3,
    default_retry_delay=5,
    retry_backoff=True,
)
def process_job(self, job_id: int, user_id: int | None = None) -> dict:
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).one_or_none()
        if job is None:
            return {"job_id": job_id, "status": "not_found"}

        if job.user_id is not None and user_id is not None and job.user_id != user_id:
            return {"job_id": job_id, "status": "forbidden"}

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        payload = json.loads(job.payload) if job.payload else {}
        task_result = _execute_payload_task(payload)
        result = {
            "status": "processed",
            "source": "celery-worker",
            "task": task_result.get("operation"),
            "payload": payload,
            "result": task_result.get("result"),
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

        job.result = json.dumps(result)
        job.status = "completed"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        return {
            "job_id": job.id,
            "status": job.status,
            "result": result,
        }
    except Exception as exc:  # pragma: no cover - defensive fallback
        job = db.query(Job).filter(Job.id == job_id).one_or_none()
        if job is not None:
            job.error_message = str(exc)
            job.finished_at = datetime.now(timezone.utc)
            db.commit()

        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            if job is not None:
                job.status = "dead_letter"
                job.error_message = str(exc)
                job.finished_at = datetime.now(timezone.utc)
                db.commit()
            return {"job_id": job_id, "status": "dead_letter", "error": str(exc)}
    finally:
        db.close()
