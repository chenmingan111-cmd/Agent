from fastapi import APIRouter
from app.services.es_client import es_client

router = APIRouter()

@router.get("/health")
async def health_check():
    es_status = "down"
    try:
        if await es_client.client.ping():
            es_status = "up"
    except Exception:
        pass
        
    return {
        "status": "ok", 
        "elasticsearch": es_status,
        "version": "1.0.0"
    }
