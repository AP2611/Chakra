"""Test with a real request to measure actual performance."""
import asyncio
import time
from orchestrator import Orchestrator

async def test_real_request():
    """Test with a real user request."""
    print("=" * 60)
    print("TESTING REAL REQUEST")
    print("=" * 60)
    print("\nRequest: 'write a python code for bubble sort'")
    print("Starting...\n")
    
    orchestrator = Orchestrator()
    
    # Track timing
    start_time = time.time()
    step_times = {}
    
    # Track events
    events = []
    
    async def stream_callback(data):
        """Track streaming events."""
        event_type = data.get("type", "unknown")
        events.append({
            "type": event_type,
            "time": time.time() - start_time,
            "data": data
        })
        if event_type == "token":
            print(".", end="", flush=True)
        elif event_type == "first_response_complete":
            print(f"\n✓ First response complete at {time.time() - start_time:.2f}s")
        elif event_type == "improving_started":
            print(f"✓ Improvements started at {time.time() - start_time:.2f}s")
        elif event_type == "improved":
            print(f"✓ Improved response at {time.time() - start_time:.2f}s")
        elif event_type == "iteration_complete":
            print(f"✓ Iteration complete at {time.time() - start_time:.2f}s")
        elif event_type == "final":
            print(f"✓ Final response at {time.time() - start_time:.2f}s")
        elif event_type == "error":
            print(f"\n✗ Error: {data.get('error', 'Unknown error')}")
    
    try:
        # Process the request
        result = await orchestrator.process(
            task="write a python code for bubble sort",
            context=None,
            use_rag=False,
            is_code=True,
            stream_callback=stream_callback
        )
        
        total_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"\nTotal Time: {total_time:.2f} seconds")
        print(f"Final Score: {result['final_score']:.2f}")
        print(f"Iterations: {result['total_iterations']}")
        
        # Show timing breakdown
        if events:
            print("\nEvent Timeline:")
            for event in events:
                print(f"  {event['time']:.2f}s - {event['type']}")
        
        # Show solution preview
        print(f"\nSolution Preview (first 200 chars):")
        print(result['final_solution'][:200] + "...")
        
        # Show iterations breakdown
        if result.get('iterations'):
            print(f"\nIterations Breakdown:")
            for i, iteration in enumerate(result['iterations'], 1):
                print(f"\n  Iteration {i}:")
                print(f"    Score: {iteration.get('score', 0):.2f}")
                print(f"    Improvement: {iteration.get('improvement', 0):.2f}")
                if iteration.get('yantra_output'):
                    print(f"    Yantra output length: {len(iteration['yantra_output'])} chars")
                if iteration.get('sutra_critique'):
                    print(f"    Sutra critique length: {len(iteration['sutra_critique'])} chars")
                if iteration.get('agni_output'):
                    print(f"    Agni output length: {len(iteration['agni_output'])} chars")
        
        # Performance analysis
        print("\n" + "=" * 60)
        print("PERFORMANCE ANALYSIS")
        print("=" * 60)
        
        if total_time < 15:
            print("✓ EXCELLENT: Response time is fast (< 15s)")
        elif total_time < 30:
            print("✓ GOOD: Response time is acceptable (< 30s)")
        elif total_time < 60:
            print("⚠ WARNING: Response time is slow (< 60s)")
        else:
            print("✗ CRITICAL: Response time is too slow (> 60s)")
        
        # Check for bottlenecks
        first_response_time = None
        for event in events:
            if event['type'] == 'first_response_complete':
                first_response_time = event['time']
                break
        
        if first_response_time:
            print(f"\nFirst Response Time: {first_response_time:.2f}s")
            if first_response_time < 5:
                print("✓ First response appears quickly")
            elif first_response_time < 10:
                print("⚠ First response is acceptable")
            else:
                print("✗ First response is too slow")
        
        improvement_time = None
        for event in events:
            if event['type'] == 'improved':
                improvement_time = event['time']
                break
        
        if improvement_time and first_response_time:
            improvement_delay = improvement_time - first_response_time
            print(f"\nImprovement Delay: {improvement_delay:.2f}s (time between first response and improvement)")
            if improvement_delay < 10:
                print("✓ Improvements appear quickly")
            else:
                print("⚠ Improvements take a while")
        
        return result
        
    except Exception as e:
        total_time = time.time() - start_time
        print(f"\n✗ ERROR after {total_time:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_real_request())

