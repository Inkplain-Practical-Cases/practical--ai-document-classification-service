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

