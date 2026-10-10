"""STEP-2: extract UTF-8 text and reject invalid encodings/PDF data."""
import io
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from app.main import app
client = TestClient(app)

def test_txt_extraction():
    r = client.post("/documents/classify", files={"file": ("a.txt", b"Sample extracted text")})
    assert r.status_code == 201 and r.json()["text_length"] == len("Sample extracted text")

def test_corrupted_text_rejected():
    assert client.post("/documents/classify", files={"file": ("x.txt", b"\xff")}).status_code == 422

def test_blank_pdf_rejected_as_unextractable():
    pdf = PdfWriter()
    pdf.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    pdf.write(buf)
    assert client.post("/documents/classify", files={"file": ("blank.pdf", buf.getvalue())}).status_code == 422
