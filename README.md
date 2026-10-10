# ai-document-classification-service

Inkplain FDE Starter learning repository. Five STEP branches introduce capabilities in sequence. Each STEP-N branch includes its own CRD, teaching notes and synthetic source. The final main branch contains the STEP-5 implementation.

## Local run

```bash
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

**Caution:** This is a mock training implementation, not a production-grade integration. Real security controls, data storage and external provider implementations need further engineering and QA.

The canonical complete design is FINAL.crd. Simulator export and portal lessons are tracked separately in the Inkplain Case Flow.
