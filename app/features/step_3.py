"""STEP-3: Classify with offline provider.
ICS layer: service. Called by: app.main.process.
Why it exists: isolates this teaching operation for direct tests.
Without it: the specific STEP-3 transformation is unavailable.
"""
def transform(value:str)->str:
    """Transform a synthetic string into an offline result."""
    return "invoice" if "invoice" in value.lower() else "general"
