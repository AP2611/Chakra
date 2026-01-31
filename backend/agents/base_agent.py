"""Base agent class for all agents in the system."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import httpx
import json


class BaseAgent(ABC):
    """Base class for all agents using Ollama."""
    
    def __init__(self, name: str, ollama_url: str = "http://localhost:11434", model: str = "qwen2.5:1.5b"):
        self.name = name
        self.ollama_url = ollama_url
        self.model = model
        self.api_url = f"{ollama_url}/api/chat"
    
    async def _call_ollama(self, prompt: str, system: Optional[str] = None, max_tokens: int = 2048) -> str:
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
                
                # Check status before parsing
                if response.status_code != 200:
                    error_text = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("error", {}).get("message", str(error_json))
                    except:
                        error_detail = error_text
                    raise Exception(f"Ollama API returned status {response.status_code}: {error_detail}")
                
                result = response.json()
                content = result.get("message", {}).get("content", "")
                if not content:
                    # Fallback: try different response formats
                    content = result.get("response", "") or result.get("content", "")
                
                if not content:
                    # If still no content, log the full response for debugging
                    raise Exception(f"Ollama API returned empty response. Full response: {json.dumps(result, indent=2)[:500]}")
                
                return content.strip()
        except httpx.TimeoutException as e:
            raise Exception(f"Ollama API timeout after 90s. Is Ollama running? Check: curl http://localhost:11434/api/tags")
        except httpx.ConnectError as e:
            raise Exception(f"Cannot connect to Ollama at {self.ollama_url}. Make sure Ollama is running: ollama serve")
        except httpx.RequestError as e:
            raise Exception(f"Ollama API connection error: {str(e)}. Make sure Ollama is running on {self.ollama_url}")
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_response = e.response.json()
                error_detail = error_response.get("error", {}).get("message", str(error_response))
            except:
                error_detail = str(e.response.text)
            raise Exception(f"Ollama API HTTP error {e.response.status_code}: {error_detail}")
        except json.JSONDecodeError as e:
            raise Exception(f"Ollama API returned invalid JSON: {str(e)}")
        except Exception as e:
            error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
            raise Exception(f"Error calling Ollama API: {error_msg}")
    
    @abstractmethod
    async def process(self, **kwargs) -> Dict[str, Any]:
        """Process the input and return output."""
        pass

