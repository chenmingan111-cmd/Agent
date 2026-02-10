from elasticsearch import AsyncElasticsearch
from app.core.config import settings
from app.core.errors import ESDriverError

class ESClient:
    def __init__(self):
        self.client = AsyncElasticsearch(
            settings.ES_URL,
            basic_auth=(settings.ES_USER, settings.ES_PASSWORD),
            verify_certs=False,  # For local dev/test with self-signed certs
            request_timeout=settings.DEFAULT_TIMEOUT_MS / 1000
        )

    async def close(self):
        await self.client.close()

    async def get_mapping(self, index: str) -> dict:
        try:
            return await self.client.indices.get_mapping(index=index)
        except Exception as e:
            raise ESDriverError(f"Failed to get mapping for {index}: {str(e)}")

    async def get_field_caps(self, index: str, fields: str = "*") -> dict:
        try:
            return await self.client.field_caps(index=index, fields=fields)
        except Exception as e:
            raise ESDriverError(f"Failed to get field caps for {index}: {str(e)}")

    async def validate_query(self, index: str, query: dict) -> dict:
        try:
            return await self.client.indices.validate_query(
                index=index,
                body=query,
                explain=True
            )
        except Exception as e:
            # We don't raise error here because validate failure is expected logic
            return {"valid": False, "error": str(e)}

    async def search(self, index: str, body: dict, **kwargs) -> dict:
        try:
            return await self.client.search(index=index, body=body, **kwargs)
        except Exception as e:
            raise ESDriverError(f"Search failed: {str(e)}")
    
    async def get_document(self, index: str, id: str):
        try:
            return await self.client.get(index=index, id=id)
        except Exception as e:
            raise ESDriverError(f"Get document failed: {str(e)}")
            
    async def explain(self, index: str, id: str, body: dict):
        try:
            return await self.client.explain(index=index, id=id, body=body)
        except Exception as e:
             raise ESDriverError(f"Explain failed: {str(e)}")

    async def open_point_in_time(self, index: str, keep_alive: str = "1m") -> str:
        try:
            resp = await self.client.open_point_in_time(index=index, keep_alive=keep_alive)
            return resp["id"]
        except Exception as e:
            raise ESDriverError(f"Failed to open PIT: {str(e)}")

    async def close_point_in_time(self, id: str):
         try:
            await self.client.close_point_in_time(body={"id": id})
         except Exception:
             pass

es_client = ESClient()
