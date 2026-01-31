"""Test Ollama connection."""
import asyncio
import httpx

async def test_ollama():
    """Test Ollama API connection."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": "qwen2.5:1.5b",
                "messages": [{"role": "user", "content": "Say hello"}],
                "stream": False
            }
            print("Testing Ollama connection...")
            print(f"URL: http://localhost:11434/api/chat")
            print(f"Payload: {payload}")
            
            response = await client.post(
                "http://localhost:11434/api/chat",
                json=payload
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Success! Response: {result.get('message', {}).get('content', '')[:200]}")
                return True
            else:
                print(f"\n❌ Error: {response.text}")
                return False
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_ollama())

