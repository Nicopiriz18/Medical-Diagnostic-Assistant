import httpx
from app.core.config import settings

class LLMClient:
    def __init__(self):
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.api_key = settings.LLM_API_KEY

    async def chat(self, *, messages, model: str, temperature: float = 0.2) -> str:
        if not self.api_key:
            raise RuntimeError("LLM_API_KEY no configurada")

        url = f"{self.base_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()

        return data["choices"][0]["message"]["content"]
