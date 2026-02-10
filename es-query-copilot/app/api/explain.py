from fastapi import APIRouter, HTTPException
from app.models.dto import ExplainRequest, ExplainResponse
from app.services.es_client import es_client

router = APIRouter()

@router.post("/explain", response_model=ExplainResponse)
async def explain_query(request: ExplainRequest):
    try:
        resp = await es_client.explain(
            index=request.index, 
            id=request.doc_id, 
            body=request.dsl
        )
        
        return ExplainResponse(
            matched=resp.get("matched", False),
            explanation=resp.get("explanation", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
