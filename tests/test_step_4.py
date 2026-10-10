"""STEP-4: persistence stores only metadata and a digest."""
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_persisted_decision(tmp_path, monkeypatch):
    path = tmp_path / "results.sqlite3"
    monkeypatch.setenv("DOCUMENT_DB", str(path))
    response = client.post("/documents/classify", files={"file": ("case.txt", b"invoice payment due")})
    assert response.status_code == 201
    result = response.json()
    assert result["id"] and result["label"] == "invoice"
    with sqlite3.connect(path) as database:
        row = database.execute("SELECT label, sha256 FROM decisions").fetchone()
        assert row[0] == "invoice" and len(row[1]) == 64
