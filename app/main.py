"""FastAPI HTTP boundary for the offline PDF/TXT classification learning case."""
import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from app.document_service import MAX_BYTES, process_document

app = FastAPI(title="AI Document Classification Service")

class ClassificationResponse(BaseModel):
    id: str
    label: str
    confidence: float = Field(ge=0, le=1)
    review_required: bool
    text_length: int

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/documents/classify", response_model=ClassificationResponse, status_code=201)
async def classify_document(file: UploadFile = File(...)) -> ClassificationResponse:
    """Bound the upload before reading; reject invalid documents with 422."""
    raw = await file.read(MAX_BYTES + 1)
    await file.close()
    try:
        decision = process_document(
            file.filename or "document", raw,
            os.environ.get("DOCUMENT_DB", "/tmp/inkplain-documents.sqlite3"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ClassificationResponse(**vars(decision))
