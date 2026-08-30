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
    db_job = Job(
        user_id=user_id,
        name=job.name,
        status="queued",
        payload=json.dumps(job.payload) if job.payload is not None else None,
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

    job.status = update.status
    if update.status == "running" and job.started_at is None:
        job.started_at = datetime.now(timezone.utc)
    if update.status in {"completed", "failed", "cancelled"}:
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
    job.finished_at = job.finished_at or datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)
    return _serialize_job_response(job)
