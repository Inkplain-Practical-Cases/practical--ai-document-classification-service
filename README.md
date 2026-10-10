# AI Document Classification Service — STEP-4

# STEP-4 of 5 — Store label and review decisions

## What you build
A runnable, cumulative offline document ingestion slice. Open app/main.py for the HTTP door and app/document_service.py for the service logic.

## What changed
Store label and review decisions. The previous step's behavior remains covered by earlier tests.

## Components and CRD
be.classify_document, be.process_document, be.extract, be.validate_document, be.classify, be.persist. Follow calls listed in the accompanying STEP-4.crd.

## Run and verify
python -m pip install -r requirements.txt

python -m pytest -q

uvicorn app.main:app --reload

Use only synthetic TXT/PDF fixtures. Binary PDF parsing is text-only (no OCR).

## Next
Verify safety and error tests
