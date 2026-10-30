import os
import json
import time
from pathlib import Path
from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_FILE = DATA_DIR / "config.json"

# Load .env file on module import
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)

DEFAULT_CONFIG = {
    "ollama_url": "http://localhost:11434",
    "gemini_api_key": "",
    "openai_api_key": "",
    "openai_base_url": "https://api.openai.com/v1",
    "anthropic_api_key": ""
}

CLOUD_MODELS = {
    "gemini": [
        {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash-Lite (⚡ Ultra Fast • ~1.2s)", "provider": "gemini"},
        {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash (🚀 Fast & Smart • Recommended)", "provider": "gemini"},
        {"id": "gemini-flash-lite-latest", "name": "Gemini Flash-Lite Latest (⚡ High Speed)", "provider": "gemini"},
        {"id": "gemini-3.1-flash-lite", "name": "Gemini 3.1 Flash-Lite (Fast)", "provider": "gemini"}
    ],
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o (Flagship Multimodal)", "provider": "openai"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini (Fast & Affordable)", "provider": "openai"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "openai"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai"}
    ],
    "anthropic": [
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet (State of the Art)", "provider": "anthropic"},
        {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku (Ultra Fast)", "provider": "anthropic"},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus (Complex Analysis)", "provider": "anthropic"}
    ]
}

def load_config() -> Dict[str, Any]:
    """Load configuration from disk with env / .env fallback."""
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=True)

    config = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception:
            pass

    # Environment variables (including from .env) take precedence if set
    if os.environ.get("OLLAMA_URL"):
        config["ollama_url"] = os.environ["OLLAMA_URL"]
    if os.environ.get("GEMINI_API_KEY"):
        config["gemini_api_key"] = os.environ["GEMINI_API_KEY"]
    if os.environ.get("OPENAI_API_KEY"):
        config["openai_api_key"] = os.environ["OPENAI_API_KEY"]
    if os.environ.get("OPENAI_BASE_URL"):
        config["openai_base_url"] = os.environ["OPENAI_BASE_URL"]
    if os.environ.get("ANTHROPIC_API_KEY"):
        config["anthropic_api_key"] = os.environ["ANTHROPIC_API_KEY"]

    return config

def save_config(config: Dict[str, Any]):
    """Persist configuration to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

class MultiLLMManager:
    """Unified manager for local Ollama and Cloud LLMs (Gemini, ChatGPT, Claude)."""

    def __init__(self):
        self.config = load_config()
        self._models_cache = None
        self._models_cache_time = 0.0

    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update and save config."""
        self.config.update(updates)
        self._models_cache = None # invalidate cache
        save_config(self.config)
        return self.config

    def get_api_key(self, provider: str, request_key: Optional[str] = None) -> Optional[str]:
        """Retrieve API key from request, config, or environment (including .env)."""
        if request_key and request_key.strip():
            return request_key.strip()

        # Reload latest values from .env if present
        if ENV_FILE.exists():
            load_dotenv(ENV_FILE, override=True)

        if provider == "gemini":
            return os.environ.get("GEMINI_API_KEY") or self.config.get("gemini_api_key")
        elif provider == "openai":
            return os.environ.get("OPENAI_API_KEY") or self.config.get("openai_api_key")
        elif provider == "anthropic":
            return os.environ.get("ANTHROPIC_API_KEY") or self.config.get("anthropic_api_key")
        return None

    async def check_ollama_health(self) -> Dict[str, Any]:
        """Check Ollama service availability."""
        url = self.config.get("ollama_url", "http://localhost:11434").rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{url}/api/version")
                if res.status_code == 200:
                    data = res.json()
                    return {"connected": True, "version": data.get("version", "active"), "url": url}
        except Exception:
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    res = await client.get(f"{url}/api/tags")
                    if res.status_code == 200:
                        return {"connected": True, "version": "active", "url": url}
            except Exception as e:
                return {"connected": False, "error": str(e), "url": url}
        return {"connected": False, "error": "Unreachable", "url": url}

    async def get_all_models(self) -> Dict[str, Any]:
        """Return all available models grouped by provider (cached for high performance)."""
        now = time.time()
        if self._models_cache and (now - self._models_cache_time) < 30.0:
            return self._models_cache

        # 1. Local Ollama Models
        ollama_models = []
        url = self.config.get("ollama_url", "http://localhost:11434").rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    for m in data.get("models", []):
                        size_gb = round(m.get("size", 0) / (1024 ** 3), 2)
                        speed_hint = "⚡ Fast" if size_gb < 4.0 else "🧠 High Quality"
                        ollama_models.append({
                            "id": m.get("name"),
                            "name": f"{m.get('name')} ({size_gb} GB • {speed_hint})",
                            "provider": "ollama",
                            "size_gb": size_gb
                        })
        except Exception:
            pass

        # 2. Check Key Status for Cloud Providers
        cloud_status = {
            "gemini": bool(self.get_api_key("gemini")),
            "openai": bool(self.get_api_key("openai")),
            "anthropic": bool(self.get_api_key("anthropic"))
        }

        result = {
            "ollama_models": ollama_models,
            "gemini_models": CLOUD_MODELS["gemini"],
            "openai_models": CLOUD_MODELS["openai"],
            "anthropic_models": CLOUD_MODELS["anthropic"],
            "cloud_keys_configured": cloud_status
        }
        self._models_cache = result
        self._models_cache_time = now
        return result

    async def preload_model(self, model: str) -> Dict[str, Any]:
        """Pre-warm local model into RAM/VRAM so the user's first query is instantaneous."""
        if self.infer_provider(model) != "ollama":
            return {"status": "skipped", "reason": "Cloud models require no local RAM loading"}

        url = self.config.get("ollama_url", "http://localhost:11434").rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # An empty generation call with keep_alive instructs Ollama to load model weights into RAM immediately
                res = await client.post(
                    f"{url}/api/generate",
                    json={"model": model, "keep_alive": "24h"}
                )
                return {"status": "preloaded", "model": model, "http_status": res.status_code}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def infer_provider(self, model: str) -> str:
        """Determine provider based on model identifier."""
        m_lower = model.lower()
        if "gemini" in m_lower:
            return "gemini"
        elif any(k in m_lower for k in ["gpt-4", "gpt-3.5", "o1-", "chatgpt"]):
            return "openai"
        elif "claude" in m_lower:
            return "anthropic"
        return "ollama"

    async def stream_generate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        provider: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Unified async generator streaming tokens across Ollama, Gemini, OpenAI, and Claude."""
        resolved_provider = provider or self.infer_provider(model)

        if resolved_provider == "gemini":
            async for token in self._stream_gemini(model, prompt, system_prompt, temperature, api_key):
                yield token
        elif resolved_provider == "openai":
            async for token in self._stream_openai(model, prompt, system_prompt, temperature, api_key):
                yield token
        elif resolved_provider == "anthropic":
            async for token in self._stream_anthropic(model, prompt, system_prompt, temperature, api_key):
                yield token
        else:
            async for token in self._stream_ollama(model, prompt, system_prompt, temperature):
                yield token

    async def _stream_ollama(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float
    ) -> AsyncGenerator[str, None]:
        """Stream from local Ollama service with persistent 24h keep_alive and optimized context size."""
        url = self.config.get("ollama_url", "http://localhost:11434").rstrip("/")
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "keep_alive": "24h", # Keep model loaded in memory! Don't unload after 5m!
            "options": {
                "temperature": float(temperature),
                "num_ctx": 4096 # Avoid huge KV allocations that slow down loading
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                async with client.stream("POST", f"{url}/api/generate", json=payload) as response:
                    if response.status_code != 200:
                        err = await response.aread()
                        yield f"\n\n[Ollama Error: Status {response.status_code}: {err.decode('utf-8', errors='ignore')}]"
                        return

                    async for line in response.aiter_lines():
                        if not line or not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            if token:
                                yield token
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError:
            yield f"\n\n⚠️ **Ollama Offline**: Could not connect to local Ollama at `{url}`.\nPlease ensure Ollama is running (`ollama serve`) or switch to a Cloud Model (Gemini, OpenAI, Claude) in Settings."
        except Exception as e:
            yield f"\n\n⚠️ **Ollama Error**: {str(e)}"

    async def _stream_gemini(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        request_key: Optional[str],
        is_fallback: bool = False
    ) -> AsyncGenerator[str, None]:
        """Stream from Google Gemini API via SSE with automatic smart fallback on 503/404."""
        key = self.get_api_key("gemini", request_key)
        if not key:
            yield "\n\n⚠️ **Gemini API Key Missing**: Please provide your Google Gemini API key in **Settings** (or set `GEMINI_API_KEY` in environment)."
            return

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={key}"
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": float(temperature)}
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", endpoint, json=payload) as response:
                    if response.status_code != 200:
                        err_body = await response.aread()
                        try:
                            err_json = json.loads(err_body)
                            msg = err_json.get("error", {}).get("message", err_body.decode())
                        except Exception:
                            msg = err_body.decode(errors="ignore")

                        # Automatic Smart Fallback for 503 High Demand or 404 Deprecated/Unavailable
                        if response.status_code in (503, 404) and not is_fallback:
                            fallback_model = "gemini-3.5-flash-lite" if model != "gemini-3.5-flash-lite" else "gemini-3.5-flash"
                            yield f"*(⚡ Note: Model `{model}` is currently experiencing high demand on Google servers. Automatically re-routing to ultra-fast `{fallback_model}`...)*\n\n"
                            async for tok in self._stream_gemini(
                                model=fallback_model,
                                prompt=prompt,
                                system_prompt=system_prompt,
                                temperature=temperature,
                                request_key=request_key,
                                is_fallback=True
                            ):
                                yield tok
                            return

                        yield f"\n\n⚠️ **Google Gemini API Error** (Status {response.status_code}): {msg}"
                        return

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if not data_str:
                            continue
                        try:
                            chunk = json.loads(data_str)
                            candidates = chunk.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    text_token = p.get("text", "")
                                    if text_token:
                                        yield text_token
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n\n⚠️ **Gemini Streaming Error**: {str(e)}"

    async def _stream_openai(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        request_key: Optional[str]
    ) -> AsyncGenerator[str, None]:
        """Stream from OpenAI / ChatGPT compatible API."""
        key = self.get_api_key("openai", request_key)
        if not key:
            yield "\n\n⚠️ **OpenAI API Key Missing**: Please enter your OpenAI API key in **Settings** (or set `OPENAI_API_KEY` in environment)."
            return

        base_url = self.config.get("openai_base_url", "https://api.openai.com/v1").rstrip("/")
        endpoint = f"{base_url}/chat/completions"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": float(temperature),
            "stream": True
        }
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", endpoint, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        err_body = await response.aread()
                        err_text = err_body.decode(errors="ignore")
                        try:
                            err_json = json.loads(err_body)
                            msg = err_json.get("error", {}).get("message", err_text)
                            code = err_json.get("error", {}).get("code", "")
                        except Exception:
                            msg = err_text
                            code = ""

                        if response.status_code == 429 and ("insufficient_quota" in err_text or "credit_balance_exhausted" in err_text or code == "credit_balance_exhausted"):
                            yield (
                                "\n\n⚠️ **OpenAI Account Credit Exhausted (Status 429)**:\n"
                                "Your OpenAI API key is authentic and connected, but your OpenAI account has **$0 remaining credits**.\n\n"
                                "**How to fix:**\n"
                                "1. **Add billing credits** ($5 minimum) at [platform.openai.com/settings/organization/billing](https://platform.openai.com/settings/organization/billing/)\n"
                                "2. **Or switch to Google Gemini** in the model dropdown above (Gemini 3.5 Flash-Lite is active, 100% free, and responds in 1.2s!)\n"
                                "3. **Or use free OpenAI-compatible models** via Groq (`https://api.groq.com/openai/v1`)."
                            )
                            return

                        yield f"\n\n⚠️ **OpenAI API Error** (Status {response.status_code}): {msg}"
                        return

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            choices = chunk.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                token = delta.get("content", "")
                                if token:
                                    yield token
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n\n⚠️ **OpenAI Streaming Error**: {str(e)}"

    async def test_provider_key(
        self,
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Test API key authentication, model availability, and response speed."""
        key = self.get_api_key(provider, api_key)
        start_time = time.time()

        if provider == "gemini":
            if not key:
                return {"success": False, "message": "Gemini API key is empty."}
            test_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={key}"
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(test_url, json={"contents": [{"parts": [{"text": "Hi"}]}]})
                    latency = round((time.time() - start_time) * 1000)
                    if resp.status_code == 200:
                        return {
                            "success": True,
                            "latency_ms": latency,
                            "model": "gemini-3.5-flash-lite",
                            "message": f"Connected to Google Gemini! Latency: {round(latency/1000, 2)}s"
                        }
                    else:
                        err_text = resp.text
                        try:
                            err_json = resp.json()
                            msg = err_json.get("error", {}).get("message", err_text)
                        except Exception:
                            msg = err_text
                        return {"success": False, "status_code": resp.status_code, "message": f"Gemini error ({resp.status_code}): {msg}"}
            except Exception as e:
                return {"success": False, "message": f"Gemini connection failed: {str(e)}"}

        elif provider == "openai":
            if not key:
                return {"success": False, "message": "OpenAI API key is empty."}
            target_base = (base_url or self.config.get("openai_base_url", "https://api.openai.com/v1")).rstrip("/")
            test_url = f"{target_base}/chat/completions"
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5
            }
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(test_url, json=payload, headers=headers)
                    latency = round((time.time() - start_time) * 1000)
                    if resp.status_code == 200:
                        return {
                            "success": True,
                            "latency_ms": latency,
                            "model": "gpt-4o-mini",
                            "message": f"Connected to OpenAI ChatGPT! Latency: {round(latency/1000, 2)}s"
                        }
                    else:
                        err_text = resp.text
                        try:
                            err_json = resp.json()
                            msg = err_json.get("error", {}).get("message", err_text)
                            code = err_json.get("error", {}).get("code", "")
                        except Exception:
                            msg = err_text
                            code = ""

                        if resp.status_code == 429 and ("insufficient_quota" in err_text or "credit_balance_exhausted" in err_text or code == "credit_balance_exhausted"):
                            return {
                                "success": False,
                                "status_code": 429,
                                "code": "credit_balance_exhausted",
                                "message": "[Quota Exceeded] Key authenticated, but account balance is $0 (Credits exhausted). Top up at platform.openai.com"
                            }
                        return {"success": False, "status_code": resp.status_code, "message": f"OpenAI error ({resp.status_code}): {msg}"}
            except Exception as e:
                return {"success": False, "message": f"OpenAI connection failed: {str(e)}"}

        elif provider == "anthropic":
            if not key:
                return {"success": False, "message": "Anthropic API key is empty."}
            test_url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 5,
                "messages": [{"role": "user", "content": "Hi"}]
            }
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(test_url, json=payload, headers=headers)
                    latency = round((time.time() - start_time) * 1000)
                    if resp.status_code == 200:
                        return {
                            "success": True,
                            "latency_ms": latency,
                            "model": "claude-3-5-haiku",
                            "message": f"Connected to Anthropic Claude! Latency: {round(latency/1000, 2)}s"
                        }
                    else:
                        return {"success": False, "status_code": resp.status_code, "message": f"Anthropic error: {resp.text[:150]}"}
            except Exception as e:
                return {"success": False, "message": f"Anthropic connection failed: {str(e)}"}

        elif provider == "ollama":
            health = await self.check_ollama_health()
            if health.get("connected"):
                return {"success": True, "message": f"Ollama connected (v{health.get('version')})"}
            else:
                return {"success": False, "message": f"Ollama unreachable: {health.get('error')}"}

        return {"success": False, "message": f"Unknown provider: {provider}"}

    async def _stream_anthropic(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        request_key: Optional[str]
    ) -> AsyncGenerator[str, None]:
        """Stream from Anthropic Claude API."""
        key = self.get_api_key("anthropic", request_key)
        if not key:
            yield "\n\n⚠️ **Anthropic API Key Missing**: Please enter your Anthropic API key in **Settings** (or set `ANTHROPIC_API_KEY` in environment)."
            return

        endpoint = "https://api.anthropic.com/v1/messages"
        payload = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": float(temperature),
            "stream": True
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", endpoint, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        err_body = await response.aread()
                        try:
                            err_json = json.loads(err_body)
                            msg = err_json.get("error", {}).get("message", err_body.decode())
                        except Exception:
                            msg = err_body.decode(errors="ignore")
                        yield f"\n\n⚠️ **Anthropic Claude API Error** (Status {response.status_code}): {msg}"
                        return

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if not data_str:
                            continue
                        try:
                            chunk = json.loads(data_str)
                            event_type = chunk.get("type")
                            if event_type == "content_block_delta":
                                delta = chunk.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    token = delta.get("text", "")
                                    if token:
                                        yield token
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n\n⚠️ **Claude Streaming Error**: {str(e)}"
