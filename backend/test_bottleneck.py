"""Diagnostic script to identify where the system is getting stuck."""
import asyncio
import time
import httpx
from agents import Yantra, Sutra, Agni
from orchestrator import Orchestrator
from rag.retriever import SimpleRAGRetriever

async def test_ollama_connection():
    """Test if Ollama is accessible and responding."""
    print("\n=== Testing Ollama Connection ===")
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            elapsed = time.time() - start
            print(f"✓ Ollama connection: {elapsed:.2f}s")
            print(f"  Status: {response.status_code}")
            return True
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ Ollama connection failed: {e}")
        print(f"  Time taken: {elapsed:.2f}s")
        return False

async def test_ollama_simple_call():
    """Test a simple Ollama API call."""
    print("\n=== Testing Simple Ollama Call ===")
    start = time.time()
    try:
        yantra = Yantra()
        result = await yantra.process(
            task="Say hello",
            is_code_task=False,
            use_fast_mode=True
        )
        elapsed = time.time() - start
        print(f"✓ Simple Ollama call: {elapsed:.2f}s")
        print(f"  Response length: {len(result['output'])} chars")
        print(f"  Response preview: {result['output'][:100]}...")
        return True, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ Simple Ollama call failed: {e}")
        print(f"  Time taken: {elapsed:.2f}s")
        import traceback
        traceback.print_exc()
        return False, elapsed

async def test_yantra():
    """Test Yantra agent."""
    print("\n=== Testing Yantra Agent ===")
    start = time.time()
    try:
        yantra = Yantra()
        result = await yantra.process(
            task="Write a function to add two numbers",
            is_code_task=True,
            use_fast_mode=True
        )
        elapsed = time.time() - start
        print(f"✓ Yantra: {elapsed:.2f}s")
        print(f"  Output length: {len(result['output'])} chars")
        return True, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ Yantra failed: {e}")
        print(f"  Time taken: {elapsed:.2f}s")
        import traceback
        traceback.print_exc()
        return False, elapsed

async def test_sutra():
    """Test Sutra agent."""
    print("\n=== Testing Sutra Agent ===")
    start = time.time()
    try:
        sutra = Sutra()
        result = await sutra.process(
            yantra_output="def add(a, b): return a + b",
            original_task="Write a function to add two numbers",
            is_code_task=True,
            use_fast_mode=True
        )
        elapsed = time.time() - start
        print(f"✓ Sutra: {elapsed:.2f}s")
        print(f"  Critique length: {len(result['critique'])} chars")
        return True, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ Sutra failed: {e}")
        print(f"  Time taken: {elapsed:.2f}s")
        import traceback
        traceback.print_exc()
        return False, elapsed

async def test_agni():
    """Test Agni agent."""
    print("\n=== Testing Agni Agent ===")
    start = time.time()
    try:
        agni = Agni()
        result = await agni.process(
            original_output="def add(a, b): return a + b",
            critique="Add error handling and type hints",
            task="Write a function to add two numbers",
            is_code_task=True,
            use_fast_mode=True
        )
        elapsed = time.time() - start
        print(f"✓ Agni: {elapsed:.2f}s")
        print(f"  Output length: {len(result['improved_output'])} chars")
        return True, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ Agni failed: {e}")
        print(f"  Time taken: {elapsed:.2f}s")
        import traceback
        traceback.print_exc()
        return False, elapsed

async def test_memory_retrieval():
    """Test memory retrieval."""
    print("\n=== Testing Memory Retrieval ===")
    start = time.time()
    try:
        from agents import Smriti
        smriti = Smriti()
        # Run in thread to avoid blocking
        similar_tasks = await asyncio.to_thread(
            smriti.retrieve_similar, 
            "Write a function", 
            3
        )
        elapsed = time.time() - start
        print(f"✓ Memory retrieval: {elapsed:.2f}s")
        print(f"  Found {len(similar_tasks)} similar tasks")
        return True, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ Memory retrieval failed: {e}")
        print(f"  Time taken: {elapsed:.2f}s")
        import traceback
        traceback.print_exc()
        return False, elapsed

async def test_rag_retrieval():
    """Test RAG retrieval."""
    print("\n=== Testing RAG Retrieval ===")
    start = time.time()
    try:
        rag = SimpleRAGRetriever()
        chunks = await asyncio.to_thread(rag.retrieve, "test query", 3)
        elapsed = time.time() - start
        print(f"✓ RAG retrieval: {elapsed:.2f}s")
        print(f"  Found {len(chunks)} chunks")
        return True, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ RAG retrieval failed: {e}")
        print(f"  Time taken: {elapsed:.2f}s")
        import traceback
        traceback.print_exc()
        return False, elapsed

async def test_full_orchestrator():
    """Test full orchestrator with timing."""
    print("\n=== Testing Full Orchestrator ===")
    start = time.time()
    try:
        orchestrator = Orchestrator()
        
        # Track timing for each step
        step_times = {}
        
        # Step 1: Memory retrieval
        step_start = time.time()
        from agents import Smriti
        smriti = Smriti()
        similar_tasks = await asyncio.to_thread(smriti.retrieve_similar, "test", 3)
        step_times['memory'] = time.time() - step_start
        
        # Step 2: Yantra
        step_start = time.time()
        yantra_result = await orchestrator.yantra.process(
            task="Say hello in one sentence",
            is_code_task=False,
            use_fast_mode=True
        )
        step_times['yantra'] = time.time() - step_start
        
        # Step 3: Sutra
        step_start = time.time()
        sutra_result = await orchestrator.sutra.process(
            yantra_output=yantra_result['output'],
            original_task="Say hello in one sentence",
            is_code_task=False,
            use_fast_mode=True
        )
        step_times['sutra'] = time.time() - step_start
        
        # Step 4: Agni
        step_start = time.time()
        agni_result = await orchestrator.agni.process(
            original_output=yantra_result['output'],
            critique=sutra_result['critique'],
            task="Say hello in one sentence",
            is_code_task=False,
            use_fast_mode=True
        )
        step_times['agni'] = time.time() - step_start
        
        total_elapsed = time.time() - start
        
        print(f"✓ Full orchestrator: {total_elapsed:.2f}s")
        print(f"  Breakdown:")
        for step, duration in step_times.items():
            percentage = (duration / total_elapsed) * 100
            print(f"    {step}: {duration:.2f}s ({percentage:.1f}%)")
        
        return True, total_elapsed, step_times
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ Full orchestrator failed: {e}")
        import traceback
        traceback.print_exc()
        return False, elapsed, {}

async def main():
    """Run all diagnostic tests."""
    print("=" * 60)
    print("DIAGNOSTIC TESTING - Identifying Bottlenecks")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Ollama connection
    results['ollama_connection'] = await test_ollama_connection()
    
    if not results['ollama_connection']:
        print("\n⚠️  Ollama is not accessible. Please start Ollama first:")
        print("   ollama serve")
        return
    
    # Test 2: Simple Ollama call
    results['simple_call'], results['simple_time'] = await test_ollama_simple_call()
    
    # Test 3: Individual agents
    results['yantra_ok'], results['yantra_time'] = await test_yantra()
    results['sutra_ok'], results['sutra_time'] = await test_sutra()
    results['agni_ok'], results['agni_time'] = await test_agni()
    
    # Test 4: Memory and RAG
    results['memory_ok'], results['memory_time'] = await test_memory_retrieval()
    results['rag_ok'], results['rag_time'] = await test_rag_retrieval()
    
    # Test 5: Full orchestrator
    results['orchestrator_ok'], results['orchestrator_time'], results['step_times'] = await test_full_orchestrator()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if results.get('simple_time', 0) > 30:
        print(f"⚠️  Simple Ollama call took {results['simple_time']:.2f}s - TOO SLOW")
        print("   Issue: Ollama is responding slowly")
        print("   Fix: Check Ollama model size, hardware, or use faster model")
    
    total_agent_time = results.get('yantra_time', 0) + results.get('sutra_time', 0) + results.get('agni_time', 0)
    if total_agent_time > 60:
        print(f"⚠️  Total agent time: {total_agent_time:.2f}s - TOO SLOW")
        print("   Issue: Individual agents are slow")
        if results.get('yantra_time', 0) > 20:
            print(f"   - Yantra is slow: {results['yantra_time']:.2f}s")
        if results.get('sutra_time', 0) > 20:
            print(f"   - Sutra is slow: {results['sutra_time']:.2f}s")
        if results.get('agni_time', 0) > 20:
            print(f"   - Agni is slow: {results['agni_time']:.2f}s")
    
    if results.get('memory_time', 0) > 5:
        print(f"⚠️  Memory retrieval took {results['memory_time']:.2f}s - TOO SLOW")
        print("   Issue: Database connection or query is slow")
        print("   Fix: Check MySQL connection, optimize queries")
    
    if results.get('rag_time', 0) > 5:
        print(f"⚠️  RAG retrieval took {results['rag_time']:.2f}s - TOO SLOW")
        print("   Issue: RAG retrieval is slow")
        print("   Fix: Reduce document size or optimize retrieval")
    
    if results.get('orchestrator_time', 0) > 90:
        print(f"⚠️  Full orchestrator took {results['orchestrator_time']:.2f}s - TOO SLOW")
        if results.get('step_times'):
            print("   Breakdown:")
            for step, duration in results['step_times'].items():
                if duration > 15:
                    print(f"   - {step}: {duration:.2f}s (SLOW)")

if __name__ == "__main__":
    asyncio.run(main())

