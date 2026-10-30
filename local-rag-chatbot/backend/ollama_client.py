import json
from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx

DEFAULT_OLLAMA_URL = "http://localhost:11434"

class OllamaClient:
    """Async client for communicating with local Ollama service."""

    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL):
        self.base_url = base_url.rstrip("/")

    def set_base_url(self, new_url: str):
        self.base_url = new_url.rstrip("/")

    async def check_health(self) -> Dict[str, Any]:
        """Check if Ollama service is reachable and retrieve version."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(f"{self.base_url}/api/version")
                if res.status_code == 200:
                    data = res.json()
                    return {"connected": True, "version": data.get("version", "unknown"), "url": self.base_url}
        except Exception as e:
            # Fallback to checking root or tags
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    res = await client.get(f"{self.base_url}/api/tags")
                    if res.status_code == 200:
                        return {"connected": True, "version": "active", "url": self.base_url}
            except Exception as e2:
                return {"connected": False, "error": str(e2), "url": self.base_url}

        return {"connected": False, "error": "Unreachable", "url": self.base_url}

    async def get_models(self) -> List[Dict[str, Any]]:
        """Fetch all installed models from local Ollama."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = []
                    for m in data.get("models", []):
                        size_gb = round(m.get("size", 0) / (1024 ** 3), 2)
                        models.append({
                            "name": m.get("name"),
                            "model": m.get("model"),
                            "size_gb": size_gb,
                            "modified_at": m.get("modified_at")
                        })
                    return models
        except Exception:
            pass
        return []

    async def stream_generate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Stream token generation from Ollama."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": float(temperature)
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        yield f"\n\n[Ollama Error: Status {response.status_code}: {error_text.decode('utf-8', errors='ignore')}]"
                        return

                    async for line in response.aiter_lines():
                        if not line or not line.strip():
                            continue
                        try:
                            chunk_data = json.loads(line)
                            token = chunk_data.get("response", "")
                            if token:
                                yield token
                            if chunk_data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

        except httpx.ConnectError:
            yield f"\n\n⚠️ **Connection Error**: Could not connect to Ollama at `{self.base_url}`.\nPlease ensure Ollama is running (`ollama serve`)."
        except Exception as e:
            yield f"\n\n⚠️ **Streaming Error**: {str(e)}"
