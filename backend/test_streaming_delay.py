"""Test streaming delay from backend to frontend."""
import asyncio
import time
import httpx
import json

async def test_streaming_delay():
    """Test how quickly tokens appear in the stream."""
    print("=" * 60)
    print("TESTING STREAMING DELAY")
    print("=" * 60)
    
    url = "http://localhost:8000/process-stream"
    payload = {
        "task": "Say hello in one sentence",
        "context": None,
        "use_rag": False,
        "is_code": False
    }
    
    print("\nSending request to backend...")
    start_time = time.time()
    first_token_time = None
    token_count = 0
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    print(f"✗ Error: {response.status_code}")
                    error_text = await response.aread()
                    print(f"  {error_text.decode()}")
                    return
                
                print("✓ Connected to stream")
                print("Waiting for tokens...\n")
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            
                            if data.get("type") == "token":
                                if first_token_time is None:
                                    first_token_time = time.time()
                                    delay = first_token_time - start_time
                                    print(f"First token received: {delay:.3f}s after request")
                                
                                token_count += 1
                                if token_count <= 10:
                                    elapsed = time.time() - start_time
                                    print(f"  Token {token_count}: {elapsed:.3f}s - '{data.get('token', '')[:20]}'")
                                
                            elif data.get("type") == "first_response_complete":
                                elapsed = time.time() - start_time
                                print(f"\n✓ First response complete: {elapsed:.3f}s")
                                
                            elif data.get("type") == "improved":
                                elapsed = time.time() - start_time
                                print(f"✓ Improved response: {elapsed:.3f}s")
                                
                            elif data.get("type") == "final":
                                elapsed = time.time() - start_time
                                print(f"✓ Final response: {elapsed:.3f}s")
                                break
                                
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            print(f"Error parsing: {e}")
                
                total_time = time.time() - start_time
                print(f"\nTotal time: {total_time:.3f}s")
                print(f"Total tokens received: {token_count}")
                
                if first_token_time:
                    time_to_first_token = first_token_time - start_time
                    print(f"\nTime to first token: {time_to_first_token:.3f}s")
                    
                    if time_to_first_token < 1:
                        print("✓ EXCELLENT: First token appears very quickly")
                    elif time_to_first_token < 3:
                        print("✓ GOOD: First token appears quickly")
                    elif time_to_first_token < 5:
                        print("⚠ WARNING: First token takes a while")
                    else:
                        print("✗ CRITICAL: First token takes too long")
                
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming_delay())

