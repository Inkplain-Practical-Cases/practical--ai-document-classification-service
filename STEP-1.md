# STEP-1 — Validate document upload

## What you build
A validated FastAPI input route with an explicit handler and synthetic fixtures. This first branch is runnable and has no real credentials.

## Learn
Pydantic input constraints, the door-to-handler call, and rejection of invalid requests.

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest -q
```

## Verify
POST /process with {"message":"synthetic example"} receives 200; missing message returns 422.

## Next
STEP-2 adds the next business component while retaining the current behavior.
