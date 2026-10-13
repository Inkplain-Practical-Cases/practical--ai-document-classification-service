# STEP-5 of 5 — Verify safety and error tests

## What you build
A runnable, cumulative offline document ingestion slice. Open app/main.py for the HTTP door and app/document_service.py for the service logic.

## What changed
Verify safety and error tests. The previous step's behavior remains covered by earlier tests.

## Components and CRD
be.classify_document, be.process_document, be.extract, be.validate_document, be.classify, be.persist. Follow calls listed in the accompanying STEP-5.crd.

## Run and verify
python -m pip install -r requirements.txt

python -m pytest -q

uvicorn app.main:app --reload

Use only synthetic TXT/PDF fixtures. Binary PDF parsing is text-only (no OCR).

## Next
The final main branch adds FINAL.crd and the five-tab .inkp file.

## Database model — STEP-5-ERD
This step keeps the SQLite `decisions` table introduced in STEP-4 without changing its schema. `STEP-5.erd` contains the whole table and labels it `step_change: unchanged`. Open `STEP-5-ERD` in the main `.inkp` Simulator project to compare it with STEP-4; both are generated from the real `persist` SQL in `app/document_service.py`. There are no additional tables or relationships in this step.
