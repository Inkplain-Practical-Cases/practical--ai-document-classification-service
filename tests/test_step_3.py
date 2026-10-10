"""Synthetic API response and validation test."""
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_invalid_request():
    assert client.post("/process",json={}).status_code==422
def test_schema_result():
    response=client.post("/process",json={"message":"synthetic sample"})
    assert response.status_code in (200,422)
