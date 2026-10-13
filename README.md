# AI Document Classification Service

Five cumulative FastAPI learning steps, each independently tested.

1. Validate document upload — step-01-validate-document-upload
2. Extract PDF and text content — step-02-extract-pdf-and-text-content
3. Classify with offline provider — step-03-classify-with-offline-provider
4. Store label and review decisions — step-04-store-label-and-review-decisions
5. Verify safety and error tests — step-05-verify-safety-and-error-tests

## Run the final service

python -m pip install -r requirements.txt

python -m pytest -q

uvicorn app.main:app --reload

POST synthetic PDF or TXT using multipart field file at /documents/classify. Responses include label, confidence, review_required and ID. Classification is deterministic keyword matching, not a remote LLM. Only SHA-256 document digest and decision metadata are retained in SQLite. No OCR or malware-hardened isolation is provided.

The final main branch includes FINAL.crd and ai-document-classification-service.inkp. Each STEP branch includes only its corresponding STEP-N.crd and STEP-N.md.

## Source-derived SQLite ERDs

The offline service stores metadata in one `decisions` SQLite table, created in STEP-4 and unchanged in STEP-5. The learning repository includes `STEP-4.erd` and `STEP-5.erd` on their respective branches and `FINAL.erd` on main. The same main `.inkp` keeps its original five component-flow tabs and adds `STEP-4-ERD` and `STEP-5-ERD` as read-only visual diagrams (PK + six exact SQLite columns, no FK relationships). Earlier STEP-1–3 have no persistent database, so no fictitious entity diagrams are drawn. Preview the `.inkp` in Inkplain Simulator or via each step's System design lesson.
