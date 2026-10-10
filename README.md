# AI Document Classification Service — STEP-1

# STEP-1 of 5 — Validate document upload

## What you build
A runnable, cumulative offline document ingestion slice. Open app/main.py for the HTTP door and app/document_service.py for the service logic.

## What changed
Validate document upload. The previous step's behavior remains covered by earlier tests.

## Components and CRD
be.classify_document, be.validate_document. Follow calls listed in the accompanying STEP-1.crd.

## Run and verify
python -m pip install -r requirements.txt

python -m pytest -q

uvicorn app.main:app --reload

Use only synthetic TXT/PDF fixtures. Binary PDF parsing is text-only (no OCR).

## Next
Extract PDF and text content
