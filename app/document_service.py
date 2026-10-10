"""Document input boundary: check file type, signature and size before parsing.

ICS layer: service. Called by classify_document and extract.
Without it: malformed or oversized files could consume unbounded resources.
Step: introduced in STEP-1.
"""
from __future__ import annotations
import hashlib
import io
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

MAX_BYTES = 2 * 1024 * 1024
MAX_PAGES = 30
MAX_CHARS = 150000

def validate_document(filename: str, content: bytes) -> None:
    """Raise ValueError unless document type, size and signature pass."""
    suffix = Path(filename).suffix.lower()
    if suffix not in (".txt", ".pdf"):
        raise ValueError("Only .pdf and .txt documents are supported")
    if not content or len(content) > MAX_BYTES:
        raise ValueError("Document must contain 1 to 2097152 bytes")
    if suffix == ".pdf" and not content.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF signature")

# STEP-2: keep PDF parsing separate from HTTP response handling.
def extract(filename: str, content: bytes) -> str:
    """Return normalized text from bounded PDF/TXT files, never raw bytes."""
    validate_document(filename, content)
    if filename.lower().endswith(".txt"):
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("TXT must be UTF-8") from exc
    else:
        try:
            pdf = PdfReader(io.BytesIO(content), strict=True)
            if pdf.is_encrypted:
                raise ValueError("Encrypted PDFs are not supported")
            if len(pdf.pages) > MAX_PAGES:
                raise ValueError("PDF exceeds 30 pages")
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Could not parse PDF") from exc
    text = text.replace("\r\n", "\n").strip()
    if not text:
        raise ValueError("No extractable document text")
    if len(text) > MAX_CHARS:
        raise ValueError("Extracted text exceeds limit")
    return text

# STEP-3: local, deterministic baseline with explicit uncertainty.
def classify(text: str) -> tuple[str, float]:
    """Return a label and confidence; heuristic scores are not calibrated."""
    lower = text.lower()
    cues = {
        "invoice": ("invoice", "invoice number", "payment due", "bill to"),
        "contract": ("agreement", "contract", "terms and conditions", "signatures"),
        "resume": ("curriculum vitae", "work experience", "education", "resume"),
    }
    hits = {key: sum(term in lower for term in terms) for key, terms in cues.items()}
    label = max(hits, key=hits.get)
    if hits[label] == 0:
        return "general", 0.30
    if sum(n == hits[label] for n in hits.values()) > 1:
        return "general", 0.40
    return label, min(0.95, 0.65 + 0.10 * (hits[label] - 1))

# STEP-4: metadata storage and review flag, without original document content.
@dataclass(frozen=True)
class Decision:
    id: str
    label: str
    confidence: float
    review_required: bool
    text_length: int

def persist(path: str, decision: Decision, digest: str) -> None:
    """Store a decision transactionally and exclude uploaded text and bytes."""
    with sqlite3.connect(path, timeout=5) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS decisions ("
            "id TEXT PRIMARY KEY, sha256 TEXT NOT NULL, label TEXT NOT NULL, "
            "confidence REAL NOT NULL, review_required INTEGER NOT NULL, "
            "text_length INTEGER NOT NULL)"
        )
        connection.execute(
            "INSERT INTO decisions VALUES (?,?,?,?,?,?)",
            (decision.id, digest, decision.label,
             decision.confidence, int(decision.review_required),
             decision.text_length),
        )

def process_document(filename: str, content: bytes, database: str) -> Decision:
    """Extract, classify and store one document decision in the offline database."""
    text = extract(filename, content)
    label, confidence = classify(text)
    result = Decision(
        id=str(uuid.uuid4()), label=label, confidence=confidence,
        review_required=confidence < 0.75, text_length=len(text),
    )
    persist(database, result, hashlib.sha256(content).hexdigest())
    return result

