import json

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Job
from app.db.session import get_db
from app.schemas.job import JobCreate, JobResponse
from app.schemas.job_result import JobResultUpdate
from app.schemas.job_status import JobStatusUpdate
from app.core.security import get_current_user_id
from app.tasks import enqueue_job


router = APIRouter(tags=["jobs"])


def _serialize_job_response(job: Job) -> JobResponse:
    payload = None
    if job.payload is not None:
        try:
            payload = json.loads(job.payload)
        except json.JSONDecodeError:
            payload = job.payload

    result = None
    if job.result is not None:
        try:
            result = json.loads(job.result)
        except json.JSONDecodeError:
            result = job.result

    return JobResponse(
        id=job.id,
        name=job.name,
        status=job.status,
        payload=payload,
        result=result,
        error_message=job.error_message,
        version=job.version,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> JobResponse:
    # Check for duplicate idempotency key
    if job.idempotency_key:
        existing_job = (
            db.query(Job)
            .filter(Job.user_id == user_id, Job.idempotency_key == job.idempotency_key)
            .one_or_none()
        )
        if existing_job:
            return _serialize_job_response(existing_job)
    
    db_job = Job(
        user_id=user_id,
        name=job.name,
        status="queued",
        payload=json.dumps(job.payload) if job.payload is not None else None,
        idempotency_key=job.idempotency_key,
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    try:
        enqueue_job(db_job.id, user_id)
    except Exception:
        pass

    return _serialize_job_response(db_job)


@router.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> list[JobResponse]:
    jobs = db.query(Job).filter(Job.user_id == user_id).order_by(Job.created_at.desc()).all()
    return [_serialize_job_response(job) for job in jobs]


@router.get("/jobs/failed", response_model=list[JobResponse])
def list_failed_jobs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> list[JobResponse]:
    jobs = (
        db.query(Job)
        .filter(Job.user_id == user_id, Job.status == "failed")
        .order_by(Job.finished_at.desc().nullslast())
        .all()
    )
    return [_serialize_job_response(job) for job in jobs]


@router.get("/jobs/dead-letter", response_model=list[JobResponse])
def list_dead_letter_jobs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> list[JobResponse]:
    jobs = (
        db.query(Job)
        .filter(Job.user_id == user_id, Job.status == "dead_letter")
        .order_by(Job.finished_at.desc().nullslast())
        .all()
    )
    return [_serialize_job_response(job) for job in jobs]


@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
def retry_job(
    job_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status not in {"failed", "dead_letter"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only failed or dead-letter jobs can be retried")

    job.status = "queued"
    job.version += 1
    job.error_message = None
    job.started_at = None
    job.finished_at = None
    db.commit()
    db.refresh(job)

    try:
        enqueue_job(job.id, user_id)
    except Exception:
        pass

    return _serialize_job_response(job)


@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_job(
    job_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status in {"completed", "cancelled", "dead_letter"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job cannot be cancelled from its current state")

    job.status = "cancelled"
    job.version += 1
    job.error_message = job.error_message or "cancelled by user"
    job.finished_at = job.finished_at or datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return _serialize_job_response(job)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _serialize_job_response(job)


@router.patch("/jobs/{job_id}/status", response_model=JobResponse)
def update_job_status(
    job_id: int,
    update: JobStatusUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Check for version conflict (optimistic locking)
    if update.expected_version is not None and job.version != update.expected_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Version conflict: expected {update.expected_version}, but current version is {job.version}",
        )

    job.status = update.status
    job.version += 1
    if update.status == "running" and job.started_at is None:
        job.started_at = datetime.now(timezone.utc)
    if update.status in {"completed", "failed", "cancelled", "dead_letter"}:
        job.finished_at = job.finished_at or datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)
    return _serialize_job_response(job)


@router.patch("/jobs/{job_id}/result", response_model=JobResponse)
def update_job_result(
    job_id: int,
    update: JobResultUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if update.result is not None:
        job.result = json.dumps(update.result)
    job.status = "completed"
    job.version += 1
    job.finished_at = job.finished_at or datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)
    return _serialize_job_response(job)
