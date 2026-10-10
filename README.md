# AI Document Classification Service

Offline, synthetic FastAPI learning service with deterministic document triage.

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
python -m pytest -q
```

POST a synthetic PDF or UTF-8 TXT file to `/documents/classify` (multipart field `file`).
The response includes a label, confidence and review_required flag. Classification uses
explicit keyword rules, **not an LLM**. Only a content SHA-256 digest and decision metadata
are stored in SQLite (`DOCUMENT_DB`); source text and file bytes are not persisted.

Limits: 2 MiB input, 30 PDF pages, 150k characters extracted. PDFs must have
extractable text (no OCR). This is a teaching baseline, not a malware-hardened
untrusted PDF sandbox. Existing STEP branches are historical lessons and need
cumulative ancestry repair before the full case is published.
