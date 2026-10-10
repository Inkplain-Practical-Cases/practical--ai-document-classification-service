"""Offline document triage: validation, extraction, classification and SQLite storage.

All classification rules are deterministic and intentionally educational.  No user
documents are transmitted to an external model or written to application logs.
"""
from __future__ import annotations
import hashlib
import io
import os
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from pypdf import PdfReader

MAX_BYTES = 2 * 1024 * 1024
LABELS = ("invoice", "contract", "resume", "general")

@dataclass(frozen=True)
class Decision:
    id: str
    label: str
    confidence: float
    review_required: bool
    text_length: int

def extract(filename: str, content: bytes) -> str:
    """Reject oversized/unsupported input and safely extract local PDF/TXT."""
    if not content or len(content) > MAX_BYTES:
        raise ValueError("Document must contain 1 to 2097152 bytes")
    extension = Path(filename).suffix.lower()
    if extension == ".txt":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("TXT must be UTF-8") from exc
    elif extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF signature")
        try:
            reader = PdfReader(io.BytesIO(content), strict=True)
            if reader.is_encrypted:
                raise ValueError("Encrypted PDFs are not supported")
            if len(reader.pages) > 30:
                raise ValueError("PDF exceeds 30 pages")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Could not parse PDF") from exc
    else:
        raise ValueError("Only .pdf and .txt documents are supported")
    text = text.replace("\r\n", "\n").strip()
    if not text:
        raise ValueError("No extractable document text")
    if len(text) > 150000:
        raise ValueError("Extracted text exceeds limit")
    return text

def classify(text: str) -> tuple[str, float]:
    """Deterministic offline baseline: transparent labels and low-confidence review."""
    lower = text.lower()
    cues = {
        "invoice": ("invoice", "invoice number", "payment due", "bill to"),
        "contract": ("agreement", "contract", "terms and conditions", "signatures"),
        "resume": ("curriculum vitae", "work experience", "education", "resume"),
    }
    hits = {label: sum(1 for term in terms if term in lower) for label, terms in cues.items()}
    best = max(hits, key=hits.get)
    if hits[best] == 0:
        return "general", 0.30
    if list(hits.values()).count(hits[best]) > 1:
        return "general", 0.40
    return best, min(0.95, 0.65 + 0.10 * (hits[best]-1))

def persist(path: str, decision: Decision, digest: str) -> None:
    """Save metadata only, never original document content."""
    with sqlite3.connect(path, timeout=5) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS decisions
            (id TEXT PRIMARY KEY, sha256 TEXT NOT NULL, label TEXT NOT NULL,
             confidence REAL NOT NULL, review_required INTEGER NOT NULL,
             text_length INTEGER NOT NULL)""")
        db.execute("INSERT INTO decisions VALUES (?,?,?,?,?,?)",
                   (decision.id, digest, decision.label, decision.confidence,
                    int(decision.review_required), decision.text_length))

def process_document(filename: str, data: bytes, database: str) -> Decision:
    text = extract(filename, data)
    label, confidence = classify(text)
    decision = Decision(str(uuid.uuid4()), label, confidence, confidence < 0.75, len(text))
    persist(database, decision, hashlib.sha256(data).hexdigest())
    return decision
