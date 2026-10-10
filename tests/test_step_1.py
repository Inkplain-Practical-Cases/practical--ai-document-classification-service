"""STEP-1: valid synthetic input and unsafe upload rejection."""
from fastapi.testclient import TestClient
from app.main import app
from app.document_service import MAX_BYTES
client = TestClient(app)

def test_readiness():
    assert client.get("/health").json() == {"status": "ok"}

def test_valid_synthetic_txt():
    assert client.post("/documents/classify", files={"file": ("sample.txt", b"synthetic words")}).status_code == 201

def test_reject_unsupported_empty_and_oversize():
    for name, payload in [("bad.exe", b"x"), ("empty.txt", b""), ("large.txt", b"x" * (MAX_BYTES+1)), ("fake.pdf", b"bad")]:
        assert client.post("/documents/classify", files={"file": (name, payload)}).status_code == 422
