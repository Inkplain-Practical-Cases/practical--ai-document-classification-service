"""Offline deterministic contract and persistence tests."""
import io
import sqlite3
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from app.main import app
from app.document_service import extract, classify, MAX_BYTES

client = TestClient(app)

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

def test_invoice_classification_and_metadata_persistence(tmp_path, monkeypatch):
    db = tmp_path / "results.sqlite3"
    monkeypatch.setenv("DOCUMENT_DB", str(db))
    result = client.post("/documents/classify", files={"file": ("sample.txt", b"Invoice number 101. Bill to Test Company.", "text/plain")})
    assert result.status_code == 201
    item = result.json()
    assert item["label"] == "invoice"
    assert item["review_required"] is False
    with sqlite3.connect(db) as conn:
        count, = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()
        assert count == 1
        assert "Invoice" not in str(conn.execute("SELECT * FROM decisions").fetchone())

def test_unknown_document_routes_to_review(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCUMENT_DB", str(tmp_path / "review.sqlite3"))
    resp = client.post("/documents/classify", files={"file": ("x.txt", b"ambiguous words", "text/plain")})
    assert resp.status_code == 201
    assert resp.json()["review_required"] is True

def test_invalid_document_rejected():
    for name, data in [("data.exe", b"virus"), ("bad.pdf", b"not a PDF"), ("empty.txt", b""), ("huge.txt", b"x" * (MAX_BYTES + 1))]:
        resp = client.post("/documents/classify", files={"file": (name, data)})
        assert resp.status_code == 422

def test_utf8_validation():
    try:
        extract("bad.txt", b"\xff")
        assert False, "expected error"
    except ValueError:
        pass

def test_pdf_parser_accepts_synthetic_pdf(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCUMENT_DB", str(tmp_path / "pdf.sqlite3"))
    writer = PdfWriter()
    writer.add_blank_page(width=120, height=120)
    buffer = io.BytesIO()
    writer.write(buffer)
    response = client.post("/documents/classify", files={"file": ("blank.pdf", buffer.getvalue(), "application/pdf")})
    assert response.status_code == 422  # image-only or blank documents require OCR and are refused
