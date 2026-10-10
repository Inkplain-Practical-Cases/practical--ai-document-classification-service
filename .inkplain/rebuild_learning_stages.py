"""Generate five independently runnable, cumulative document-triage learning stages.

Output directory is outside the repository so the GitHub Actions history repair
can safely create new commits from immutable stage snapshots.
"""
from __future__ import annotations
import copy
import json
import sys
from pathlib import Path

TARGET = Path(sys.argv[1])
REPO = "https://github.com/Inkplain-Practical-Cases/practical--ai-document-classification-service"
SLUG = "ai-document-classification-service"
TITLES = [
    "Validate document upload",
    "Extract PDF and text content",
    "Classify with offline provider",
    "Store label and review decisions",
    "Verify safety and error tests",
]
BRANCHES = [
    "step-01-validate-document-upload",
    "step-02-extract-pdf-and-text-content",
    "step-03-classify-with-offline-provider",
    "step-04-store-label-and-review-decisions",
    "step-05-verify-safety-and-error-tests",
]
BASE = '''"""Document input boundary: check file type, signature and size before parsing.

ICS layer: service. Called by classify_document and extract.
Without it: malformed or oversized files could consume unbounded resources.
Step: introduced in STEP-1.
"""
from __future__ import annotations
import hashlib
import io
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

MAX_BYTES = 2 * 1024 * 1024
MAX_PAGES = 30
MAX_CHARS = 150000

def validate_document(filename: str, content: bytes) -> None:
    """Raise ValueError unless document type, size and signature pass."""
    suffix = Path(filename).suffix.lower()
    if suffix not in (".txt", ".pdf"):
        raise ValueError("Only .pdf and .txt documents are supported")
    if not content or len(content) > MAX_BYTES:
        raise ValueError("Document must contain 1 to 2097152 bytes")
    if suffix == ".pdf" and not content.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF signature")

'''
EXTRACT = '''# STEP-2: keep PDF parsing separate from HTTP response handling.
def extract(filename: str, content: bytes) -> str:
    """Return normalized text from bounded PDF/TXT files, never raw bytes."""
    validate_document(filename, content)
    if filename.lower().endswith(".txt"):
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("TXT must be UTF-8") from exc
    else:
        try:
            pdf = PdfReader(io.BytesIO(content), strict=True)
            if pdf.is_encrypted:
                raise ValueError("Encrypted PDFs are not supported")
            if len(pdf.pages) > MAX_PAGES:
                raise ValueError("PDF exceeds 30 pages")
            text = "\\n".join(page.extract_text() or "" for page in pdf.pages)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Could not parse PDF") from exc
    text = text.replace("\\r\\n", "\\n").strip()
    if not text:
        raise ValueError("No extractable document text")
    if len(text) > MAX_CHARS:
        raise ValueError("Extracted text exceeds limit")
    return text

'''
CLASSIFY = '''# STEP-3: local, deterministic baseline with explicit uncertainty.
def classify(text: str) -> tuple[str, float]:
    """Return a label and confidence; heuristic scores are not calibrated."""
    lower = text.lower()
    cues = {
        "invoice": ("invoice", "invoice number", "payment due", "bill to"),
        "contract": ("agreement", "contract", "terms and conditions", "signatures"),
        "resume": ("curriculum vitae", "work experience", "education", "resume"),
    }
    hits = {key: sum(term in lower for term in terms) for key, terms in cues.items()}
    label = max(hits, key=hits.get)
    if hits[label] == 0:
        return "general", 0.30
    if sum(n == hits[label] for n in hits.values()) > 1:
        return "general", 0.40
    return label, min(0.95, 0.65 + 0.10 * (hits[label] - 1))

'''
PERSIST = '''# STEP-4: metadata storage and review flag, without original document content.
@dataclass(frozen=True)
class Decision:
    id: str
    label: str
    confidence: float
    review_required: bool
    text_length: int

def persist(path: str, decision: Decision, digest: str) -> None:
    """Store a decision transactionally and exclude uploaded text and bytes."""
    with sqlite3.connect(path, timeout=5) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS decisions ("
            "id TEXT PRIMARY KEY, sha256 TEXT NOT NULL, label TEXT NOT NULL, "
            "confidence REAL NOT NULL, review_required INTEGER NOT NULL, "
            "text_length INTEGER NOT NULL)"
        )
        connection.execute(
            "INSERT INTO decisions VALUES (?,?,?,?,?,?)",
            (decision.id, digest, decision.label,
             decision.confidence, int(decision.review_required),
             decision.text_length),
        )

def process_document(filename: str, content: bytes, database: str) -> Decision:
    """Extract, classify and store one document decision in the offline database."""
    text = extract(filename, content)
    label, confidence = classify(text)
    result = Decision(
        id=str(uuid.uuid4()), label=label, confidence=confidence,
        review_required=confidence < 0.75, text_length=len(text),
    )
    persist(database, result, hashlib.sha256(content).hexdigest())
    return result

'''
ROUTE_START = '''"""Typed FastAPI door: size-bounded multipart upload entry point.

ICS layer: door. Calls document_service. No business rules in the route.
Without it: callers cannot submit a document using the public HTTP contract.
"""
import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from app.document_service import MAX_BYTES, validate_document
'''
ROUTE_MIDDLE = '''from app.document_service import extract
'''
ROUTE_CLASSIFY = '''from app.document_service import classify
'''
ROUTE_PERSIST = '''from app.document_service import process_document
'''
ROUTE_BASE = '''
app = FastAPI(title="AI Document Classification Service")

@app.get("/health")
def health() -> dict[str, str]:
    """Small readiness signal, without revealing credentials or user data."""
    return {"status": "ok"}

@app.post("/documents/classify", status_code=201)
async def classify_document(file: UploadFile = File(...)) -> dict:
    """Read once within a strict bound and delegate work to the service."""
    raw = await file.read(MAX_BYTES + 1)
    await file.close()
    try:
'''
ROUTE_END = '''    except ValueError as exc:
        # Public contract exposes a safe validation error, not a stack trace.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
'''
STAGE_LINES = {
    1: '''        validate_document(file.filename or "", raw)
        return {"stage": 1, "status": "accepted"}
''',
    2: '''        text = extract(file.filename or "", raw)
        return {"stage": 2, "text_length": len(text)}
''',
    3: '''        text = extract(file.filename or "", raw)
        label, confidence = classify(text)
        return {
            "stage": 3, "text_length": len(text), "label": label,
            "confidence": confidence, "review_required": confidence < 0.75,
        }
''',
    4: '''        decision = process_document(
            file.filename or "", raw,
            os.environ.get("DOCUMENT_DB", "/tmp/inkplain-documents.sqlite3"),
        )
        return vars(decision)
''',
    5: '''        decision = process_document(
            file.filename or "", raw,
            os.environ.get("DOCUMENT_DB", "/tmp/inkplain-documents.sqlite3"),
        )
        return vars(decision)
''',
}
TESTS = {
1: '''"""STEP-1: valid synthetic input and unsafe upload rejection."""
from fastapi.testclient import TestClient
from app.main import app
from app.document_service import MAX_BYTES
client = TestClient(app)

def test_readiness():
    assert client.get("/health").json() == {"status": "ok"}

def test_valid_synthetic_txt():
    assert client.post("/documents/classify", files={"file": ("sample.txt", b"synthetic words")}).status_code == 201

def test_reject_unsupported_empty_and_oversize():
    for name, payload in [("bad.exe", b"x"), ("empty.txt", b""), ("large.txt", b"x" * (MAX_BYTES+1)), ("fake.pdf", b"bad")]:
        assert client.post("/documents/classify", files={"file": (name, payload)}).status_code == 422
''',
2: '''"""STEP-2: extract UTF-8 text and reject invalid encodings/PDF data."""
import io
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from app.main import app
client = TestClient(app)

def test_txt_extraction():
    r = client.post("/documents/classify", files={"file": ("a.txt", b"Sample extracted text")})
    assert r.status_code == 201 and r.json()["text_length"] == len("Sample extracted text")

def test_corrupted_text_rejected():
    assert client.post("/documents/classify", files={"file": ("x.txt", b"\\xff")}).status_code == 422

def test_blank_pdf_rejected_as_unextractable():
    pdf = PdfWriter()
    pdf.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    pdf.write(buf)
    assert client.post("/documents/classify", files={"file": ("blank.pdf", buf.getvalue())}).status_code == 422
''',
3: '''"""STEP-3: typed categories and low confidence routed to review."""
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_invoice_keyword_rules():
    response = client.post("/documents/classify", files={"file": ("invoice.txt", b"Invoice number 10; payment due")})
    assert response.status_code == 201
    assert response.json()["label"] == "invoice"
    assert response.json()["review_required"] is False

def test_uncertain_text_needs_review():
    response = client.post("/documents/classify", files={"file": ("other.txt", b"unrelated synthetic terms")})
    assert response.status_code == 201
    assert response.json()["label"] == "general"
    assert response.json()["review_required"] is True
''',
4: '''"""STEP-4: persistence stores only metadata and a digest."""
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_persisted_decision(tmp_path, monkeypatch):
    path = tmp_path / "results.sqlite3"
    monkeypatch.setenv("DOCUMENT_DB", str(path))
    response = client.post("/documents/classify", files={"file": ("case.txt", b"invoice payment due")})
    assert response.status_code == 201
    result = response.json()
    assert result["id"] and result["label"] == "invoice"
    with sqlite3.connect(path) as database:
        row = database.execute("SELECT label, sha256 FROM decisions").fetchone()
        assert row[0] == "invoice" and len(row[1]) == 64
''',
5: '''"""STEP-5: check privacy, validation and regression boundaries."""
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_private_source_text_is_not_persisted(tmp_path, monkeypatch):
    path = tmp_path / "metadata.sqlite3"
    monkeypatch.setenv("DOCUMENT_DB", str(path))
    secret = b"invoice text unique-private-fixture"
    response = client.post("/documents/classify", files={"file": ("x.txt", secret)})
    assert response.status_code == 201
    assert secret not in path.read_bytes()
    with sqlite3.connect(path) as database:
        assert database.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1

def test_missing_file_gets_validation_error():
    assert client.post("/documents/classify").status_code == 422
''',
}
BASE_COMPONENTS = {
    "be.classify_document": ("classify_document", "app/main.py", "door", "Accept multipart upload, dispatch to the document service and expose a typed HTTP result."),
    "be.validate_document": ("validate_document", "app/document_service.py", "service", "Reject unsafe size, extension and PDF-signature inputs before processing."),
    "be.extract": ("extract", "app/document_service.py", "service", "Decode UTF-8 text or extract bounded PDF page text locally."),
    "be.classify": ("classify", "app/document_service.py", "service", "Score deterministic document keywords and flag classification uncertainty."),
    "be.process_document": ("process_document", "app/document_service.py", "service", "Coordinate document extraction, scoring and persistence."),
    "be.persist": ("persist", "app/document_service.py", "provider", "Write minimal review metadata and SHA-256 digest to SQLite."),
}
COMPONENTS_BY_STEP = {
    1: ["be.classify_document", "be.validate_document"],
    2: ["be.classify_document", "be.extract", "be.validate_document"],
    3: ["be.classify_document", "be.extract", "be.validate_document", "be.classify"],
    4: ["be.classify_document", "be.process_document", "be.extract", "be.validate_document", "be.classify", "be.persist"],
    5: ["be.classify_document", "be.process_document", "be.extract", "be.validate_document", "be.classify", "be.persist"],
}
CALLS = {
    1: [("be.classify_document", "be.validate_document")],
    2: [("be.classify_document", "be.extract"), ("be.extract", "be.validate_document")],
    3: [("be.classify_document", "be.extract"), ("be.extract", "be.validate_document"), ("be.classify_document", "be.classify")],
    4: [("be.classify_document", "be.process_document"), ("be.process_document", "be.extract"), ("be.extract", "be.validate_document"), ("be.process_document", "be.classify"), ("be.process_document", "be.persist")],
    5: [("be.classify_document", "be.process_document"), ("be.process_document", "be.extract"), ("be.extract", "be.validate_document"), ("be.process_document", "be.classify"), ("be.process_document", "be.persist")],
}
def write(root: Path, path: str, value: str):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(value, encoding="utf-8")

def make_crd(i: int, final: bool=False) -> dict:
    previous = set(COMPONENTS_BY_STEP.get(i-1, []))
    revision = "main" if final else BRANCHES[i-1]
    comps = []
    for cid in COMPONENTS_BY_STEP[i]:
        symbol, path, layer, description = BASE_COMPONENTS[cid]
        outcalls = [target for source,target in CALLS[i] if source == cid]
        comps.append({
            "id": cid, "name": symbol, "kind": "function", "side": "backend",
            "layer": layer, "description": description, "flows": ["classification"],
            "step_change": "unchanged" if final or cid in previous and i == 5 else ("changed" if cid in previous and cid == "be.classify_document" else "added" if cid not in previous else "unchanged"),
            "source": {"file": path, "symbol": symbol},
            "inputs": [{"name": "document", "description": "Synthetic input or validated service arguments"}],
            "validations": ["Reject malformed, unauthorized or out-of-bound input before side effects"],
            "operations": [{"id": "call-"+dest.replace(".","-"), "title": "Call "+dest, "calls": {"to": dest, "type":"call"}} for dest in outcalls],
            "outputs": [{"name":"result", "description":"Typed local result or a specific validation failure"}],
        })
    return {
        "crd_version": 1, "name": "AI Document Classification Service " + ("FINAL" if final else "STEP-"+str(i)),
        "description": "Cumulative offline document triage, source-derived contracts",
        "source": {"repo": REPO, "revision": revision, "roots": {"backend":"app"}, "stacks":["python-fastapi"]},
        "step": {"no":"final" if final else i, "of": 5, "title":TITLES[i-1],
                 "branch":revision,"previous": None if i == 1 else "STEP-"+str(i-1)+".crd","removed":[]},
        "flows":[{"id":"classification","name":"Classify document","entry":"be.classify_document"}],
        "components":comps,
    }

def build_simulator() -> dict:
    docs=[]
    for i in range(1,6):
        crd=make_crd(i)
        edges=[]
        nodes=[]
        for n,comp in enumerate(crd["components"]):
            docid="crd-ai-document-classification-service-s"+str(i)+"-"+comp["id"].replace(".","-")
            nodes.append({
                "id":"node-"+docid,"type":"diagramNode",
                "position":{"x":100 + 265 * (n%4), "y":130 + 230*(n//4)},
                "width":220,"height":190,
                "data":{"label":comp["name"],"shape":"module","icon":"function",
                        "color":"#1677ff","linkedCanvasId":docid,
                        "linkedCanvasName":comp["name"],
                        "nodeAttributes":[{"key":"step_change","value":comp["step_change"]}],
                        "operationSteps":[]},
            })
            docs.append({"path":"process_executor_canvas/"+docid,
                         "data":{"name":comp["name"], "input":comp["inputs"],
                                 "validations":comp["validations"],
                                 "operation":comp["operations"],
                                 "output":comp["outputs"],
                                 "attributes":[{"key":"source","value":comp["source"]["file"]+"::"+comp["source"]["symbol"]}]}})
        ids={c["id"]:"node-crd-ai-document-classification-service-s"+str(i)+"-"+c["id"].replace(".","-") for c in crd["components"]}
        for j,(source,target) in enumerate(CALLS[i]):
            edges.append({"id":"edge-"+str(i)+"-"+str(j),"source":ids[source],
                          "target":ids[target],"sourceHandle":"r","targetHandle":"l",
                          "type":"smoothstep","data":{"color":"#64748b","lineStyle":"solid",
                          "markerStartShape":"none","markerEndShape":"arrowclosed",
                          "pathType":"orthogonal","strokeWidth":1}})
        docs.append({"path":"diagram_canvas/crd-ai-document-classification-service-step-"+str(i),
                     "data":{"name":"STEP-"+str(i),"order":i-1,"nodes":nodes,"edges":edges}})
    return {
        "version":1,"exportedAt":"2026-10-10T16:00:00Z",
        "projectId":"crd-ai-document-classification-service",
        "projectName":"AI Document Classification Service",
        "meta":None,"docs":docs,
    }

REQS = "fastapi>=0.115,<1\npydantic>=2,<3\npytest>=8,<10\nhttpx>=0.27,<1\nuvicorn>=0.30,<1\npypdf>=5,<7\npython-multipart>=0.0.9,<1\n"
ENV = "# Optional SQLite destination; only hashes and decision metadata are persisted.\nDOCUMENT_DB=/tmp/inkplain-documents.sqlite3\n"
def build_stages():
    accumulated_tests={}
    for i in range(1,6):
        root=TARGET/("step-"+str(i))
        root.mkdir(parents=True, exist_ok=True)
        content=BASE
        if i>=2: content+=EXTRACT
        if i>=3: content+=CLASSIFY
        if i>=4: content+=PERSIST
        route=ROUTE_START
        if i>=2: route+=ROUTE_MIDDLE
        if i>=3: route+=ROUTE_CLASSIFY
        if i>=4: route+=ROUTE_PERSIST
        route+=ROUTE_BASE+STAGE_LINES[i]+ROUTE_END
        write(root,"app/__init__.py",'''"""Application package for the offline document classification case."""\n''')
        write(root,"app/main.py",route)
        write(root,"app/document_service.py",content)
        write(root,"requirements.txt",REQS)
        write(root,".env.example",ENV)
        accumulated_tests["tests/test_step_"+str(i)+".py"]=TESTS[i]
        for path,value in accumulated_tests.items(): write(root,path,value)
        write(root,"STEP-"+str(i)+".crd",json.dumps(make_crd(i),indent=2))
        md=("# STEP-"+str(i)+" of 5 — "+TITLES[i-1]+"\n\n"
            "## What you build\nA runnable, cumulative offline document ingestion slice. "
            "Open app/main.py for the HTTP door and app/document_service.py for the service logic.\n\n"
            "## What changed\n"+TITLES[i-1]+". The previous step's behavior remains covered by earlier tests.\n\n"
            "## Components and CRD\n"+", ".join(COMPONENTS_BY_STEP[i])+
            ". Follow calls listed in the accompanying STEP-"+str(i)+".crd.\n\n"
            "## Run and verify\npython -m pip install -r requirements.txt\n\n"
            "python -m pytest -q\n\nuvicorn app.main:app --reload\n\n"
            "Use only synthetic TXT/PDF fixtures. Binary PDF parsing is text-only (no OCR).\n\n"
            "## Next\n"+(TITLES[i] if i<5 else "The final main branch adds FINAL.crd and the five-tab .inkp file.")+"\n")
        write(root,"STEP-"+str(i)+".md",md)
        write(root,"README.md","# AI Document Classification Service — STEP-"+str(i)+"\n\n"+md)
    final=TARGET/"final"
    final.mkdir(parents=True,exist_ok=True)
    write(final,"FINAL.crd",json.dumps(make_crd(5,final=True),indent=2))
    write(final,SLUG+".inkp",json.dumps(build_simulator(),separators=(",",":")))
    summary="# AI Document Classification Service\n\nFive cumulative FastAPI learning steps, each independently tested.\n\n"
    for i in range(1,6):
        summary+=str(i)+". "+TITLES[i-1]+" — "+BRANCHES[i-1]+"\n"
    summary+=("\n## Run the final service\n\npython -m pip install -r requirements.txt\n\n"
              "python -m pytest -q\n\nuvicorn app.main:app --reload\n\n"
              "POST synthetic PDF or TXT using multipart field file at /documents/classify. "
              "Responses include label, confidence, review_required and ID. "
              "Classification is deterministic keyword matching, not a remote LLM. "
              "Only SHA-256 document digest and decision metadata are retained in SQLite. "
              "No OCR or malware-hardened isolation is provided.\n\n"
              "The final main branch includes FINAL.crd and "+SLUG+".inkp. "
              "Each STEP branch includes only its corresponding STEP-N.crd and STEP-N.md.\n")
    write(final,"README.md",summary)

if __name__=="__main__":
    build_stages()
    print("Generated five cumulative learning snapshots, FINAL.crd and the Simulator .inkp")
