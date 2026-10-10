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

