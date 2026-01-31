"""Base agent class for all agents in the system."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import httpx


class BaseAgent(ABC):
    """Base class for all agents using Ollama."""
    
    def __init__(self, name: str, ollama_url: str = "http://localhost:11434", model: str = "qwen2.5:1.5b"):
        self.name = name
        self.ollama_url = ollama_url
        self.model = model
        self.api_url = f"{ollama_url}/api/chat"
    
    async def _call_ollama(self, prompt: str, system: Optional[str] = None) -> str:
        """Call Ollama API with the given prompt."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(self.api_url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("message", {}).get("content", "").strip()
        except Exception as e:
            raise Exception(f"Error calling Ollama API: {str(e)}")
    
    @abstractmethod
    async def process(self, **kwargs) -> Dict[str, Any]:
        """Process the input and return output."""
        pass

