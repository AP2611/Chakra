"""Base agent class for all agents in the system."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, Awaitable
import httpx
import json
import re


class BaseAgent(ABC):
    """Base class for all agents using Ollama."""
    
    def __init__(self, name: str, ollama_url: str = "http://localhost:11434", model: str = "qwen2.5:1.5b"):
        self.name = name
        self.ollama_url = ollama_url
        self.model = model
        self.api_url = f"{ollama_url}/api/chat"
    
    async def _call_ollama(
        self, 
        prompt: str, 
        system: Optional[str] = None, 
        max_tokens: int = 2048,
        use_fast_mode: bool = False  # Enable speed optimizations for simple tasks
    ) -> str:
        """Call Ollama API with the given prompt."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        # Aggressive Ollama optimizations for maximum speed
        # Use max_tokens parameter to set num_predict (respect the limit passed by agents)
        if use_fast_mode:
            # Fast mode: aggressive optimizations for speed
            options = {
                "num_predict": min(max_tokens, 256),  # Use max_tokens but cap at 256 for speed
                "temperature": 0.5,      # Lower = faster and more deterministic
                "top_p": 0.7,            # Smaller = faster sampling
                "top_k": 20,             # Smaller = faster
                "repeat_penalty": 1.1,
                "num_ctx": 1024,         # Smaller context = faster processing
            }
        else:
            # Normal mode - still optimized but less aggressive
            options = {
                "num_predict": min(max_tokens, 512),  # Use max_tokens but cap at 512
                "temperature": 0.6,
                "top_p": 0.8,
                "top_k": 30,
                "num_ctx": 2048,
            }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": options  # Always include options
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
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
    
    async def _call_ollama_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        use_fast_mode: bool = False,
        token_callback: Optional[Callable[[str], Awaitable[None]]] = None  # Callback for each token (async function)
    ) -> str:
        """Call Ollama API with streaming enabled. Returns full response and calls callback for each token."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        # Aggressive Ollama optimizations for streaming
        # Use max_tokens parameter to set num_predict (respect the limit passed by agents)
        if use_fast_mode:
            options = {
                "num_predict": min(max_tokens, 256),  # Use max_tokens but cap at 256 for speed
                "temperature": 0.5,      # Lower = faster and more deterministic
                "top_p": 0.7,            # Smaller = faster sampling
                "top_k": 20,             # Smaller = faster
                "repeat_penalty": 1.1,
                "num_ctx": 1024,         # Smaller context = faster processing
            }
        else:
            # Normal mode - still optimized but less aggressive
            options = {
                "num_predict": min(max_tokens, 512),  # Use max_tokens but cap at 512
                "temperature": 0.6,
                "top_p": 0.8,
                "top_k": 30,
                "num_ctx": 2048,
            }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,  # Enable streaming
            "options": options  # Always include options
        }
        
        full_response = ""
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", self.api_url, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        try:
                            error_json = json.loads(error_text)
                            error_detail = error_json.get("error", {}).get("message", str(error_json))
                        except:
                            error_detail = error_text.decode() if isinstance(error_text, bytes) else str(error_text)
                        raise Exception(f"Ollama API returned status {response.status_code}: {error_detail}")
                    
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        try:
                            # Ollama streaming format: each line is a JSON object
                            if line.startswith("data: "):
                                line = line[6:]  # Remove "data: " prefix
                            
                            data = json.loads(line)
                            
                            # Extract token from response
                            token = data.get("message", {}).get("content", "")
                            if not token:
                                # Check for done flag
                                if data.get("done", False):
                                    break
                                continue
                            
                            # Accumulate full response
                            full_response += token
                            
                            # Call token callback immediately if provided (for instant streaming)
                            # Keep await to maintain order, but queue is unbounded so it's instant
                            if token_callback:
                                try:
                                    await token_callback(token)  # Keep await for order, but queue is instant
                                except Exception as e:
                                    print(f"Error in token_callback: {e}")
                                    
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue
                        except Exception as e:
                            print(f"Error processing stream line: {e}")
                            continue
                    
                    return full_response.strip()
                    
        except httpx.TimeoutException as e:
            raise Exception(f"Ollama API timeout after 120s. Is Ollama running? Check: curl http://localhost:11434/api/tags")
        except httpx.ConnectError as e:
            raise Exception(f"Cannot connect to Ollama at {self.ollama_url}. Make sure Ollama is running: ollama serve")
        except httpx.RequestError as e:
            raise Exception(f"Ollama API connection error: {str(e)}. Make sure Ollama is running on {self.ollama_url}")
        except Exception as e:
            error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
            raise Exception(f"Error calling Ollama API: {error_msg}")
    
    def _remove_code_blocks(self, text: str) -> str:
        """Remove all code blocks from text (for plain text responses)."""
        # Remove markdown code blocks (```language ... ```)
        text = re.sub(r'```[\s\S]*?```', '', text)
        # Remove inline code (`code`)
        text = re.sub(r'`[^`]+`', '', text)
        # Remove any remaining code-like patterns
        text = re.sub(r'def\s+\w+\s*\([^)]*\):', '', text)
        text = re.sub(r'class\s+\w+[:\s]', '', text)
        text = re.sub(r'import\s+\w+', '', text)
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines to double
        return text.strip()
    
    @abstractmethod
    async def process(self, **kwargs) -> Dict[str, Any]:
        """Process the input and return output."""
        pass

