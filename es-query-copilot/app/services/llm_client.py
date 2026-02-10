import json
import httpx
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.errors import LLMGenerationError

class LLMClient:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.provider = settings.LLM_PROVIDER
        # Currently only implementing OpenAI-compatible interface
        self.base_url = "https://api.openai.com/v1" if self.provider == "openai" else os.getenv("LLM_BASE_URL")

    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        params = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                # Provide a dummy URL if base_url is faulty in dev, but generally should be correct
                url = f"{self.base_url}/chat/completions"
                response = await client.post(url, json=params, headers=headers, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise LLMGenerationError(f"LLM returned invalid JSON: {str(e)}")
            except Exception as e:
                # Let tenacity retry on network errors, but re-raise others
                if isinstance(e, (httpx.RequestError, httpx.HTTPStatusError)):
                    raise e
                raise LLMGenerationError(f"LLM call failed: {str(e)}")

llm_client = LLMClient()
