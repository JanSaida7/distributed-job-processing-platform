from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.db.models import User
from app.db.session import SessionLocal


client = TestClient(app)


def _unique_email() -> str:
    """Generate a unique email for testing."""
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


def test_register_user_creates_account() -> None:
    """Test user registration creates a new account."""
    email = _unique_email()
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "securepassword123",
            "full_name": "New User",
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == email
    assert data["full_name"] == "New User"
    assert data["is_active"] is True
    assert "id" in data

    # Verify password is hashed in database
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).one()
        assert user.password_hash != "securepassword123"
        assert len(user.password_hash) > 20  # argon2 hash is long
    finally:
        db.close()


def test_register_duplicate_email_fails() -> None:
    """Test registration with duplicate email fails."""
    email = _unique_email()
    # First registration
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "pass123456",
        },
    )

    # Second registration with same email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "differentpass123",
        },
    )

    assert response.status_code == 409


def test_login_with_valid_credentials() -> None:
    """Test login returns a valid JWT token."""
    email = _unique_email()
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "correctpassword123",
        },
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "correctpassword123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_with_invalid_password() -> None:
    """Test login with wrong password fails."""
    email = _unique_email()
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "correctpassword123",
        },
    )

    # Login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "wrongpassword123",
        },
    )

    assert response.status_code == 401


def test_login_with_nonexistent_email() -> None:
    """Test login with non-existent email fails."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "anypassword",
        },
    )

    assert response.status_code == 401


def test_protected_job_endpoint_requires_token() -> None:
    """Test that job endpoints require authentication."""
    response = client.get("/api/v1/jobs")

    assert response.status_code == 401


def test_create_job_with_valid_token() -> None:
    """Test creating a job with valid JWT token."""
    email = _unique_email()
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123456",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "password123456",
        },
    )

    token = login_response.json()["access_token"]

    # Create job with token
    response = client.post(
        "/api/v1/jobs",
        json={"name": "test-job", "payload": {"key": "value"}},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "test-job"


def test_list_jobs_only_shows_user_jobs() -> None:
    """Test that users only see their own jobs."""
    email1 = _unique_email()
    email2 = _unique_email()
    # Register user 1
    client.post(
        "/api/v1/auth/register",
        json={"email": email1, "password": "password123456"},
    )
    login1 = client.post(
        "/api/v1/auth/login",
        json={"email": email1, "password": "password123456"},
    )
    token1 = login1.json()["access_token"]

    # Register user 2
    client.post(
        "/api/v1/auth/register",
        json={"email": email2, "password": "password123456"},
    )
    login2 = client.post(
        "/api/v1/auth/login",
        json={"email": email2, "password": "password123456"},
    )
    token2 = login2.json()["access_token"]

    # User 1 creates a job
    client.post(
        "/api/v1/jobs",
        json={"name": "user1-job"},
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User 2 creates a job
    client.post(
        "/api/v1/jobs",
        json={"name": "user2-job"},
        headers={"Authorization": f"Bearer {token2}"},
    )

    # User 1 lists jobs - should only see their own
    response1 = client.get(
        "/api/v1/jobs",
        headers={"Authorization": f"Bearer {token1}"},
    )
    jobs1 = response1.json()
    assert len(jobs1) == 1
    assert jobs1[0]["name"] == "user1-job"

    # User 2 lists jobs - should only see their own
    response2 = client.get(
        "/api/v1/jobs",
        headers={"Authorization": f"Bearer {token2}"},
    )
    jobs2 = response2.json()
    assert len(jobs2) == 1
    assert jobs2[0]["name"] == "user2-job"
