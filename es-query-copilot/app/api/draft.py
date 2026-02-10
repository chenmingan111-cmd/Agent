from fastapi import APIRouter, HTTPException
from app.models.dto import DraftRequest, DraftResponse
from app.services.llm_client import llm_client
from app.core.field_catalog import field_catalog
from app.core.prompt import SYSTEM_PROMPT
from app.core.errors import LLMGenerationError

router = APIRouter()

@router.post("/draft", response_model=DraftResponse)
async def create_draft(request: DraftRequest):
    # 1. Get Fields
    catalog_subset = field_catalog.get_index_fields(request.index)
    if not catalog_subset:
        # In MVP, if catalog is empty, we warn or proceed with empty?
        # Let's proceed but context will be empty (LLM might hallucinate)
        pass

    # 2. Prepare Prompt
    # Truncate catalog if too large (MVP mitigation)
    catalog_str = str(catalog_subset)[:10000] 
    
    sys_prompt = SYSTEM_PROMPT.format(
        index=request.index,
        timezone=request.user_context.get("timezone", "UTC"),
        catalog=catalog_str
    )
    
    try:
        # 3. Call LLM
        result = await llm_client.generate_json(
            system_prompt=sys_prompt,
            user_prompt=request.nl_query
        )
        
        # 4. Parse result (already JSON)
        return DraftResponse(
            dsl=result.get("dsl", {}),
            explanation=result.get("explanation", []),
            risk=result.get("risk", {"level": "unknown", "reasons": []}),
            confidence=result.get("confidence", 0.0)
        )
        
    except LLMGenerationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")
