from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_liveness():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_db_endpoint_shape():
    response = client.get("/health/db")
    assert response.status_code == 200
    body = response.json()
    assert "connected" in body
    assert "database" in body
    assert "status" in body
