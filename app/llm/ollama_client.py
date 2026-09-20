import os
import httpx
from typing import Dict, Any, Optional

class OllamaClient:
    def __init__(self):
        self.api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    async def generate(self, prompt: str, system: Optional[str] = None, format: Optional[str] = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system
        if format:
            payload["format"] = format
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.api_url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except httpx.ConnectError:
            raise Exception("Failed to connect to Ollama. Please ensure Ollama is running locally.")
        except Exception as e:
            raise Exception(f"Ollama API error: {e}")
