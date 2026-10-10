"""Legacy STEP-5 smoke checks upgraded to final document ingestion API."""
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_invalid_request():
    assert client.post("/documents/classify", data={}).status_code == 422

def test_schema_result(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCUMENT_DB", str(tmp_path / "legacy.sqlite3"))
    response = client.post("/documents/classify", files={"file": ("synthetic.txt", b"Invoice number 101 and payment due", "text/plain")})
    assert response.status_code == 201
    assert response.json()["label"] == "invoice"
