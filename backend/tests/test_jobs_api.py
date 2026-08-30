from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.db.models import Job
from app.db.session import SessionLocal


client = TestClient(app)


def _unique_email() -> str:
    """Generate a unique email for testing."""
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


def _register_and_login() -> str:
    """Register a user and return JWT token."""
    email = _unique_email()
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123456"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123456"},
    )
    return login_response.json()["access_token"]


def test_create_job_returns_created_record() -> None:
    token = _register_and_login()
    payload = {"name": "email-report", "payload": {"user_id": 42, "template": "daily"}}

    response = client.post(
        "/api/v1/jobs",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

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
    token = _register_and_login()
    response = client.get(
        "/api/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)


def test_get_job_by_id_returns_single_job() -> None:
    token = _register_and_login()
    created = client.post(
        "/api/v1/jobs",
        json={"name": "cleanup-task", "payload": {"folder": "tmp"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    job_id = created.json()["id"]

    response = client.get(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["name"] == "cleanup-task"


def test_update_job_status_transitions_to_running() -> None:
    token = _register_and_login()
    created = client.post(
        "/api/v1/jobs",
        json={"name": "batch-job", "payload": {"task": "import"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    job_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "running"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "running"
    assert data["started_at"] is not None


def test_update_job_status_rejects_invalid_status() -> None:
    token = _register_and_login()
    created = client.post(
        "/api/v1/jobs",
        json={"name": "invalid-job", "payload": {"task": "noop"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    job_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "unknown-status"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_complete_job_marks_finished_at() -> None:
    token = _register_and_login()
    created = client.post(
        "/api/v1/jobs",
        json={"name": "report-job", "payload": {"task": "generate"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    job_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["finished_at"] is not None


def test_cancel_job_marks_cancelled_status() -> None:
    token = _register_and_login()
    created = client.post(
        "/api/v1/jobs",
        json={"name": "cancelled-job", "payload": {"task": "skip"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    job_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "cancelled"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["finished_at"] is not None


def test_update_job_result_sets_completion_output() -> None:
    token = _register_and_login()
    created = client.post(
        "/api/v1/jobs",
        json={"name": "result-job", "payload": {"task": "transform"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    job_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/jobs/{job_id}/result",
        json={"result": {"rows_processed": 3, "status": "ok"}},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["result"] == {"rows_processed": 3, "status": "ok"}
    assert data["status"] == "completed"
    assert data["finished_at"] is not None
