# AI Document Classification Service — STEP-3

# STEP-3 of 5 — Classify with offline provider

## What you build
A runnable, cumulative offline document ingestion slice. Open app/main.py for the HTTP door and app/document_service.py for the service logic.

## What changed
Classify with offline provider. The previous step's behavior remains covered by earlier tests.

## Components and CRD
be.classify_document, be.extract, be.validate_document, be.classify. Follow calls listed in the accompanying STEP-3.crd.

## Run and verify
python -m pip install -r requirements.txt

python -m pytest -q

uvicorn app.main:app --reload

Use only synthetic TXT/PDF fixtures. Binary PDF parsing is text-only (no OCR).

## Next
Store label and review decisions
