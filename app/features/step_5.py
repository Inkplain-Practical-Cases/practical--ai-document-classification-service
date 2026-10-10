"""STEP-5: Verify safety and error tests.
ICS layer: service. Called by: app.main.process.
Why it exists: isolates this teaching operation for direct tests.
Without it: the specific STEP-5 transformation is unavailable.
"""
def transform(value:str)->str:
    """Transform a synthetic string into an offline result."""
    if not value.strip(): raise ValueError("empty input")
    return "verified:"+value[:80]
