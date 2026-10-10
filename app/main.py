"""Typed FastAPI door: size-bounded multipart upload entry point.

ICS layer: door. Calls document_service. No business rules in the route.
Without it: callers cannot submit a document using the public HTTP contract.
"""
import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from app.document_service import MAX_BYTES, validate_document
from app.document_service import extract
from app.document_service import classify
from app.document_service import process_document

app = FastAPI(title="AI Document Classification Service")

@app.get("/health")
def health() -> dict[str, str]:
    """Small readiness signal, without revealing credentials or user data."""
    return {"status": "ok"}

@app.post("/documents/classify", status_code=201)
async def classify_document(file: UploadFile = File(...)) -> dict:
    """Read once within a strict bound and delegate work to the service."""
    raw = await file.read(MAX_BYTES + 1)
    await file.close()
    try:
        decision = process_document(
            file.filename or "", raw,
            os.environ.get("DOCUMENT_DB", "/tmp/inkplain-documents.sqlite3"),
        )
        return vars(decision)
    except ValueError as exc:
        # Public contract exposes a safe validation error, not a stack trace.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
