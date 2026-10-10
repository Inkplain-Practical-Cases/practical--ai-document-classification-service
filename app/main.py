"""ai document classification service: FastAPI learning entry point.
ICS layer: door / composition root.
Why it exists: binds a typed request handler to an HTTP endpoint.
Without it: requests cannot reach the example service.
Step: added in step 1 (Validate document upload).
"""
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="ai document classification service")

class Request(BaseModel):
    """A synthetic message that can be validated without a provider."""
    message: str = Field(min_length=1, max_length=2000)

def handle_request(message: str) -> dict[str, str]:
    """Return an explicit local acknowledgement, not a fabricated AI result."""
    return {"status": "accepted", "message": message}

@app.post("/process")
def process(request: Request) -> dict[str, str]:
    """Enforce the request schema before passing to the handler."""
    return handle_request(request.message)
