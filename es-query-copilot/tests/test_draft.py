import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_draft_endpoint():
    mock_llm_response = {
        "dsl": {"query": {"match_all": {}}},
        "explanation": ["test explanation"],
        "risk": {"level": "low", "reasons": []},
        "confidence": 0.9
    }
    
    with patch("app.services.llm_client.llm_client.generate_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_llm_response
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/draft", json={
                "index": "orders-*",
                "nl_query": "test query"
            })
            
        assert response.status_code == 200
        data = response.json()
        assert "dsl" in data
        assert data["confidence"] == 0.9
