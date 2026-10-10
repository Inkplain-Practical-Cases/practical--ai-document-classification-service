"""Typed HTTP door delegating to synthetic learning service functions."""
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from app.features.step_2 import transform as action_2
from app.features.step_3 import transform as action_3
app=FastAPI(title="ai-document-classification-service")
class Request(BaseModel):
    message:str=Field(min_length=1,max_length=2000)
@app.post("/process")
def process(request:Request)->dict[str,str]:
    """Apply source-defined transformations in an ordered sequence."""
    try:
        value=request.message
        value=action_2(value)
        value=action_3(value)
        return {"status":"accepted","result":value}
    except ValueError as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc
