"""STEP-5: check privacy, validation and regression boundaries."""
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_private_source_text_is_not_persisted(tmp_path, monkeypatch):
    path = tmp_path / "metadata.sqlite3"
    monkeypatch.setenv("DOCUMENT_DB", str(path))
    secret = b"invoice text unique-private-fixture"
    response = client.post("/documents/classify", files={"file": ("x.txt", secret)})
    assert response.status_code == 201
    assert secret not in path.read_bytes()
    with sqlite3.connect(path) as database:
        assert database.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1

def test_missing_file_gets_validation_error():
    assert client.post("/documents/classify").status_code == 422
