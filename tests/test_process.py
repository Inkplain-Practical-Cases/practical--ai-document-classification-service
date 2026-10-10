"""Contract tests for the first accepted-request slice."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_accept_valid_request():
    response = client.post("/process", json={"message": "synthetic example"})
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

def test_reject_missing_message():
    assert client.post("/process", json={}).status_code == 422
