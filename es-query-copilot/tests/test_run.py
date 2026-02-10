import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_run_endpoint_low_risk():
    with patch("app.services.es_client.es_client.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = {"took": 5, "hits": {"total": 1, "hits": []}}
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/run", json={
                "index": "orders-*",
                "dsl": {"query": {"match_all": {}}, "size": 10}
            })
            
        assert response.status_code == 200
        assert response.json()["took"] == 5

@pytest.mark.asyncio
async def test_run_endpoint_high_risk():
    # Simulate high risk (e.g. wildcard)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/run", json={
            "index": "orders-*",
            "dsl": {"query": {"wildcard": {"field": "*val*"}}}
        })
    
    # Expect 403 Forbidden
    assert response.status_code == 403
    assert "High risk query blocked" in response.json()["detail"]
