"""STEP-3: typed categories and low confidence routed to review."""
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_invoice_keyword_rules():
    response = client.post("/documents/classify", files={"file": ("invoice.txt", b"Invoice number 10; payment due")})
    assert response.status_code == 201
    assert response.json()["label"] == "invoice"
    assert response.json()["review_required"] is False

def test_uncertain_text_needs_review():
    response = client.post("/documents/classify", files={"file": ("other.txt", b"unrelated synthetic terms")})
    assert response.status_code == 201
    assert response.json()["label"] == "general"
    assert response.json()["review_required"] is True
