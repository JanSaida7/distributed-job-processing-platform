import json
import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.models import Job, User
from app.db.session import SessionLocal
from app.core.security import hash_password


client = TestClient(app)


def _unique_email() -> str:
    """Generate a unique email for testing."""
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


def _get_auth_token(email: str, password: str = "password123") -> str:
    """Register and login a user, returning auth token"""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return login_response.json()["access_token"]


def test_create_job_with_idempotency_key_returns_same_job_on_duplicate():
    """Test that submitting the same job with same idempotency_key returns the same job"""
    email = _unique_email()
    auth_token = _get_auth_token(email)
    
    job_data = {
        "name": "test-idempotent-job",
        "payload": {"data": "test"},
        "idempotency_key": f"unique-key-{uuid.uuid4().hex}",
    }

    # Create first job
    response1 = client.post(
        "/api/v1/jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response1.status_code == 201
    job1 = response1.json()
    job_id_1 = job1["id"]

    # Submit same request with same idempotency key
    response2 = client.post(
        "/api/v1/jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response2.status_code == 201
    job2 = response2.json()
    job_id_2 = job2["id"]

    # Should return same job
    assert job_id_1 == job_id_2
    assert job1["name"] == job2["name"]


def test_create_job_with_different_idempotency_keys_creates_separate_jobs():
    """Test that different idempotency keys create separate jobs"""
    email = _unique_email()
    auth_token = _get_auth_token(email)
    
    base_data = {"name": "test-job"}

    # Create first job with key1
    response1 = client.post(
        "/api/v1/jobs",
        json={**base_data, "idempotency_key": f"key-1-{uuid.uuid4().hex}"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    job1_id = response1.json()["id"]

    # Create second job with key2
    response2 = client.post(
        "/api/v1/jobs",
        json={**base_data, "idempotency_key": f"key-2-{uuid.uuid4().hex}"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    job2_id = response2.json()["id"]

    # Should be different jobs
    assert job1_id != job2_id


def test_create_job_without_idempotency_key_always_creates_new_job():
    """Test that jobs without idempotency_key always create new jobs"""
    email = _unique_email()
    auth_token = _get_auth_token(email)
    
    job_data = {"name": "test-job-no-key", "payload": {"value": 1}}

    response1 = client.post(
        "/api/v1/jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    job1_id = response1.json()["id"]

    response2 = client.post(
        "/api/v1/jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    job2_id = response2.json()["id"]

    # Should create separate jobs
    assert job1_id != job2_id


def test_job_response_includes_version():
    """Test that job responses include version field"""
    email = _unique_email()
    auth_token = _get_auth_token(email)
    
    response = client.post(
        "/api/v1/jobs",
        json={"name": "test-version-job"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 201
    job = response.json()
    assert "version" in job
    assert job["version"] == 1


def test_update_job_status_increments_version():
    """Test that status updates increment the version"""
    email = _unique_email()
    auth_token = _get_auth_token(email)
    
    # Create job
    response = client.post(
        "/api/v1/jobs",
        json={"name": "test-version-update"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    job_id = response.json()["id"]
    initial_version = response.json()["version"]

    # Update status
    update_response = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "running"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert update_response.status_code == 200
    updated_job = update_response.json()
    assert updated_job["version"] == initial_version + 1


def test_update_job_status_with_version_conflict_fails():
    """Test that status update fails when expected version doesn't match"""
    email = _unique_email()
    auth_token = _get_auth_token(email)
    
    # Create job
    response = client.post(
        "/api/v1/jobs",
        json={"name": "test-conflict-detection"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    job_id = response.json()["id"]

    # Try to update with wrong expected version
    conflict_response = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "running", "expected_version": 999},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert conflict_response.status_code == 409
    response_data = conflict_response.json()
    assert "Version conflict" in str(response_data)


def test_update_job_status_with_correct_version_succeeds():
    """Test that status update succeeds with correct expected version"""
    email = _unique_email()
    auth_token = _get_auth_token(email)
    
    # Create job (version starts at 1)
    response = client.post(
        "/api/v1/jobs",
        json={"name": "test-correct-version"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    job_id = response.json()["id"]

    # Update with correct expected version
    update_response = client.patch(
        f"/api/v1/jobs/{job_id}/status",
        json={"status": "running", "expected_version": 1},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["version"] == 2


def test_cancel_job_increments_version():
    """Test that cancelling a job increments the version"""
    email = _unique_email()
    auth_token = _get_auth_token(email)
    
    # Create job
    response = client.post(
        "/api/v1/jobs",
        json={"name": "test-cancel-version"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    job_id = response.json()["id"]
    initial_version = response.json()["version"]

    # Cancel job
    cancel_response = client.post(
        f"/api/v1/jobs/{job_id}/cancel",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["version"] == initial_version + 1
    assert cancel_response.json()["status"] == "cancelled"


def test_retry_job_increments_version():
    """Test that retrying a failed job increments the version"""
    email = _unique_email()
    auth_token = _get_auth_token(email)
    
    # Create job
    create_response = client.post(
        "/api/v1/jobs",
        json={"name": "test-retry-version"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    job_id = create_response.json()["id"]

    # Mark job as failed manually in database
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        initial_version = job.version
        job.status = "failed"
        job.error_message = "Test failure"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()

    # Retry the job
    retry_response = client.post(
        f"/api/v1/jobs/{job_id}/retry",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert retry_response.status_code == 200
    assert retry_response.json()["version"] == initial_version + 1
    assert retry_response.json()["status"] == "queued"


def test_idempotency_key_is_per_user():
    """Test that idempotency keys are isolated per user"""
    # Create two users
    email1 = _unique_email()
    email2 = _unique_email()
    
    token1 = _get_auth_token(email1)
    token2 = _get_auth_token(email2)

    shared_key = f"shared-key-{uuid.uuid4().hex}"
    job_data = {
        "name": "test-shared-key",
        "idempotency_key": shared_key,
    }

    # Create job for user1
    response1 = client.post(
        "/api/v1/jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {token1}"},
    )
    job1_id = response1.json()["id"]

    # Create job for user2 with same idempotency key
    response2 = client.post(
        "/api/v1/jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {token2}"},
    )
    job2_id = response2.json()["id"]

    # Should be different jobs because users are different
    assert job1_id != job2_id
