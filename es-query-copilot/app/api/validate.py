from fastapi import APIRouter
from app.models.dto import ValidateRequest, ValidateResponse
from app.core.fixer import dsl_fixer

router = APIRouter()

@router.post("/validate", response_model=ValidateResponse)
async def validate_query(request: ValidateRequest):
    is_valid, final_dsl, errors, was_fixed = await dsl_fixer.validate_and_fix(
        request.index, 
        request.dsl
    )
    
    return ValidateResponse(
        valid=is_valid,
        errors=errors,
        auto_fixed=was_fixed,
        fixed_dsl=final_dsl if was_fixed else None,
        warnings=[]
    )
