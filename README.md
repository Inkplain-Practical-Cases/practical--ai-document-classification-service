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
