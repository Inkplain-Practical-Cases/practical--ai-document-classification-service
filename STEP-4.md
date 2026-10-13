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

## Database model — STEP-4-ERD
This step introduces SQLite table `decisions`, whose real six columns and primary key are documented in `STEP-4.erd` (derived from the `CREATE TABLE` in `app/document_service.py:persist`). Run the ERD through the Inkplain Simulator `.inkp` tab `STEP-4-ERD` after the five flow tabs. `id` is the primary key; the schema has no foreign keys and stores neither raw uploaded bytes nor extracted document text. `review_required` is a numeric 0/1 flag, not a second table.
