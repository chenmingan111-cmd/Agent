from fastapi import APIRouter, HTTPException
from app.models.dto import RunRequest, RunResponse
from app.core.risk import risk_analyzer
from app.core.errors import HighRiskBlockedError
from app.services.es_client import es_client
from app.core.config import settings

router = APIRouter()

@router.post("/run", response_model=RunResponse)
async def run_query(request: RunRequest):
    # 1. Risk Check
    risk = risk_analyzer.evaluate(request.dsl)
    if risk["level"] == "high":
        raise HTTPException(
            status_code=403, 
            detail=f"High risk query blocked: {risk['reasons']}"
        )
    
    # 2. Deep Paging Handling (PIT + search_after)
    # MVP Simplified: We won't fully implement automatic PIT loop here as it requires
    # keeping state or return cursor. For MVP, we'll just check limits and
    # error if too deep without PIT, OR if user requested simple page, we run it.
    
    # If standard search
    try:
        size = request.dsl.get("size", 10)
        from_ = request.dsl.get("from", 0)
        
        # Enforce max size if not set
        if size > settings.MAX_SIZE:
             request.dsl["size"] = settings.MAX_SIZE
             
        # Execute
        resp = await es_client.search(
            index=request.index,
            body=request.dsl,
            timeout=f"{request.timeout_ms}ms"
        )
        
        return RunResponse(
            took=resp.get("took", 0),
            timed_out=resp.get("timed_out", False),
            hits=resp.get("hits", {}),
            aggs=resp.get("aggregations", {}),
            warnings=[]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
