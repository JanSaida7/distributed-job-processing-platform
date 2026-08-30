from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_info_endpoint() -> None:
    response = client.get("/api/v1/info")

    assert response.status_code == 200
    assert response.json() == {
        "name": "distributed-job-processing-platform",
        "environment": "development",
        "version": "0.1.0",
    }


def test_queue_status_endpoint() -> None:
    response = client.get("/api/v1/queue-status")

    assert response.status_code == 200
    data = response.json()
    assert data["broker"] == "redis"
    assert data["status"] in {"connected", "disconnected"}