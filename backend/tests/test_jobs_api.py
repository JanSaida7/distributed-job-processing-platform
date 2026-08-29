from fastapi.testclient import TestClient

from app.main import app
from app.db.models import Job
from app.db.session import SessionLocal


client = TestClient(app)


def test_create_job_returns_created_record() -> None:
    payload = {"name": "email-report", "payload": {"user_id": 42, "template": "daily"}}

    response = client.post("/api/v1/jobs", json=payload)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "email-report"
    assert data["status"] == "queued"
    assert data["payload"] == {"user_id": 42, "template": "daily"}
    assert data["id"] is not None

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == data["id"]).one()
        assert job.name == "email-report"
        assert job.status == "queued"
        assert job.payload == '{"user_id": 42, "template": "daily"}'
    finally:
        db.close()


def test_list_jobs_returns_created_jobs() -> None:
    response = client.get("/api/v1/jobs")

    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert any(job["name"] == "email-report" for job in jobs)


def test_get_job_by_id_returns_single_job() -> None:
    created = client.post(
        "/api/v1/jobs",
        json={"name": "cleanup-task", "payload": {"folder": "tmp"}},
    )
    job_id = created.json()["id"]

    response = client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["name"] == "cleanup-task"


def test_update_job_status_transitions_to_running() -> None:
    created = client.post(
        "/api/v1/jobs",
        json={"name": "batch-job", "payload": {"task": "import"}},
    )
    job_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "running"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "running"
    assert data["started_at"] is not None


def test_update_job_status_rejects_invalid_status() -> None:
    created = client.post(
        "/api/v1/jobs",
        json={"name": "invalid-job", "payload": {"task": "noop"}},
    )
    job_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "unknown-status"},
    )

    assert response.status_code == 422


def test_complete_job_marks_finished_at() -> None:
    created = client.post(
        "/api/v1/jobs",
        json={"name": "report-job", "payload": {"task": "generate"}},
    )
    job_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "completed"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["finished_at"] is not None


def test_cancel_job_marks_cancelled_status() -> None:
    created = client.post(
        "/api/v1/jobs",
        json={"name": "cancelled-job", "payload": {"task": "skip"}},
    )
    job_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "cancelled"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["finished_at"] is not None


def test_update_job_result_sets_completion_output() -> None:
    created = client.post(
        "/api/v1/jobs",
        json={"name": "result-job", "payload": {"task": "transform"}},
    )
    job_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/jobs/{job_id}/result",
        json={"result": {"rows_processed": 3, "status": "ok"}},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["result"] == {"rows_processed": 3, "status": "ok"}
    assert data["status"] == "completed"
    assert data["finished_at"] is not None
