import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_validate_valid_query():
    with patch("app.services.es_client.es_client.validate_query", new_callable=AsyncMock) as mock_es:
        mock_es.return_value = {"valid": True}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/validate", json={
                "index": "orders-*",
                "dsl": {"query": {"match_all": {}}}
            })
            
        assert response.status_code == 200
        assert response.json()["valid"] is True

@pytest.mark.asyncio
async def test_validate_invalid_query_and_fix():
    # Attempt 1: Invalid
    # Attempt 2: Valid (after fix)
    
    with patch("app.services.es_client.es_client.validate_query", new_callable=AsyncMock) as mock_es, \
         patch("app.services.llm_client.llm_client.generate_json", new_callable=AsyncMock) as mock_llm:
         
        # Make side_effect return False first, then True
        mock_es.side_effect = [
            {"valid": False, "error": "simulated error"},
            {"valid": True}
        ]
        
        mock_llm.return_value = {"dsl": {"query": {"fixed": True}}}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/validate", json={
                "index": "orders-*",
                "dsl": {"query": {"bad": True}}
            })
            
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["auto_fixed"] is True
        assert data["fixed_dsl"] == {"query": {"fixed": True}}
