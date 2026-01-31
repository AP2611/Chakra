"""Orchestrator that coordinates all agents in the recursive learning loop."""
from typing import Dict, Any, List, Optional, Callable, Awaitable
import asyncio
import os
from dotenv import load_dotenv
from agents import Yantra, Sutra, Agni, Smriti
from rag.retriever import SimpleRAGRetriever
from evaluation.evaluator import Evaluator

# Load environment variables
load_dotenv()


class Orchestrator:
    """Orchestrates the multi-agent system with recursive learning."""
    
    def __init__(
        self,
        ollama_url: Optional[str] = None,
        model: Optional[str] = None,
        max_iterations: int = 1,  # Default to 1 iteration for speed
        min_improvement: float = 0.01  # Simple threshold
    ):
        # Use environment variables if not provided
        ollama_url = ollama_url or os.getenv('OLLAMA_URL', 'http://localhost:11434')
        model = model or os.getenv('OLLAMA_MODEL', 'qwen2.5:1.5b')
        
        self.yantra = Yantra(ollama_url, model)
        self.sutra = Sutra(ollama_url, model)
        self.agni = Agni(ollama_url, model)
        self.smriti = Smriti()
        self.rag = SimpleRAGRetriever()
        self.evaluator = Evaluator()
        self.max_iterations = max_iterations
        self.min_improvement = min_improvement
    
    async def process(
        self,
        task: str,
        context: Optional[str] = None,
        use_rag: bool = False,
        is_code: bool = True,
        strict_rag: bool = False,
        rag_chunks: Optional[List[str]] = None,
        max_iterations: Optional[int] = None,
        stream_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None  # Callback for streaming updates
    ) -> Dict[str, Any]:
        """Process a task through the recursive learning loop."""
        
        # Run RAG and memory retrieval in parallel for speed
        if use_rag and rag_chunks is None:
            # Parallel execution
            rag_task = asyncio.create_task(
                asyncio.to_thread(self.rag.retrieve, task, 3)
            )
            memory_task = asyncio.create_task(
                asyncio.to_thread(self.smriti.retrieve_similar, task, 3)
            )
            rag_chunks = await rag_task
            similar_tasks = await memory_task
            past_examples = [ex["solution"] for ex in similar_tasks] if similar_tasks else []
        else:
            # Only memory retrieval
            similar_tasks = await asyncio.to_thread(self.smriti.retrieve_similar, task, 3)
            past_examples = [ex["solution"] for ex in similar_tasks] if similar_tasks else []
        
        iterations = []
        best_score = 0.0
        best_solution = None
        current_solution = None
        
        # Smart iteration control: Use 1 iteration for very simple questions (speed optimization)
        # Only apply to very simple questions to minimize quality impact
        task_words = len(task.split())
        task_lower = task.lower()
        
        # Very simple questions: < 10 words AND no complex keywords
        is_very_simple = (
            task_words < 10 and 
            not any(keyword in task_lower for keyword in [
                "explain", "how", "why", "describe", "analyze", "compare", 
                "complex", "detailed", "comprehensive", "implement", "create", "build"
            ])
        )
        
        # Use custom max_iterations if provided, otherwise default to 1 for speed
        actual_max_iterations = max_iterations if max_iterations is not None else 1
        
        # Track background task for first iteration
        background_task = None
        
        for iteration in range(actual_max_iterations):
            iteration_data = {
                "iteration": iteration + 1,
                "yantra_output": None,
                "sutra_critique": None,
                "agni_output": None,
                "score": None,
                "improvement": None
            }
            
            # Always use fast mode for speed optimization
            use_fast_mode = True
            
            # Step 1: Yantra generates solution with token streaming for first iteration
            accumulated_tokens = []
            
            async def token_callback(token: str):
                """Callback to stream tokens as they're generated."""
                if stream_callback is not None and iteration == 0:
                    accumulated_tokens.append(token)
                    try:
                        await stream_callback({
                            "type": "token",
                            "token": token,
                            "accumulated": "".join(accumulated_tokens),
                            "status": "streaming"
                        })
                    except (BrokenPipeError, ConnectionError, OSError) as e:
                        print(f"Connection closed during token streaming: {e}")
                    except Exception as e:
                        print(f"Error in token_callback: {e}")
            
            # Use token streaming for first iteration if stream_callback is provided
            use_token_streaming = (stream_callback is not None and iteration == 0)
            
            yantra_result = await self.yantra.process(
                task=task,
                context=context,
                rag_chunks=rag_chunks,
                past_examples=past_examples if iteration == 0 and not strict_rag else None,  # Don't use examples in strict RAG mode
                strict_rag=strict_rag,
                is_code_task=is_code,  # Pass is_code to Yantra
                use_fast_mode=use_fast_mode,  # Enable fast mode for simple questions
                token_callback=token_callback if use_token_streaming else None
            )
            iteration_data["yantra_output"] = yantra_result["output"]
            current_solution = yantra_result["output"]
            
            # Stream first response complete (if not already streamed via tokens)
            if stream_callback is not None and iteration == 0 and not use_token_streaming:
                try:
                    await stream_callback({
                        "type": "first_response",
                        "iteration": 1,
                        "solution": yantra_result["output"],
                        "status": "initial"
                    })
                except (BrokenPipeError, ConnectionError, OSError) as e:
                    print(f"Connection closed during first_response: {e}")
                except Exception as e:
                    print(f"Error in stream_callback: {e}")  # Don't fail if callback errors
            elif stream_callback is not None and iteration == 0 and use_token_streaming:
                # Signal that streaming is complete
                try:
                    await stream_callback({
                        "type": "first_response_complete",
                        "iteration": 1,
                        "solution": yantra_result["output"],
                        "status": "complete"
                    })
                except (BrokenPipeError, ConnectionError, OSError) as e:
                    print(f"Connection closed during first_response_complete: {e}")
                except Exception as e:
                    print(f"Error in stream_callback: {e}")
            
            # For first iteration with streaming: run Sutra+Agni in background
            if iteration == 0 and stream_callback is not None:
                # Store initial solution and create iteration data
                initial_solution = current_solution
                iterations.append(iteration_data)  # Add incomplete iteration data
                
                # Background task function for improvements
                async def improve_in_background():
                    """Run Sutra and Agni in background after first response."""
                    try:
                        # Send improving_started event
                        try:
                            await stream_callback({
                                "type": "improving_started",
                                "iteration": 1,
                                "status": "improving"
                            })
                        except (BrokenPipeError, ConnectionError, OSError) as e:
                            print(f"Connection closed during improving_started: {e}")
                            return  # Exit if connection is closed
                        except Exception as e:
                            print(f"Error sending improving_started: {e}")
                        
                        # Step 2: Sutra critiques
                        sutra_result = await self.sutra.process(
                            yantra_output=initial_solution,
                            original_task=task,
                            rag_chunks=rag_chunks,
                            strict_rag=strict_rag,
                            is_code_task=is_code,
                            use_fast_mode=use_fast_mode
                        )
                        iteration_data["sutra_critique"] = sutra_result["critique"]
                        
                        # Step 3: Agni improves
                        agni_result = await self.agni.process(
                            original_output=initial_solution,
                            critique=sutra_result["critique"],
                            task=task,
                            rag_chunks=rag_chunks,
                            strict_rag=strict_rag,
                            is_code_task=is_code,
                            use_fast_mode=use_fast_mode
                        )
                        improved_solution = agni_result["improved_output"]
                        iteration_data["agni_output"] = improved_solution
                        
                        # Stream improved response
                        try:
                            await stream_callback({
                                "type": "improved",
                                "iteration": 1,
                                "solution": improved_solution,
                                "score": None,  # Will be updated after evaluation
                                "status": "improving"
                            })
                        except (BrokenPipeError, ConnectionError, OSError) as e:
                            print(f"Connection closed during improved: {e}")
                            return
                        except Exception as e:
                            print(f"Error in stream_callback (improved): {e}")
                        
                        # Step 4: Evaluate
                        score_result = self.evaluator.evaluate(
                            solution=improved_solution,
                            task=task,
                            is_code=is_code,
                            rag_chunks=rag_chunks,
                            iteration_num=0
                        )
                        score = score_result["total"]
                        iteration_data["score"] = score
                        iteration_data["score_details"] = score_result
                        iteration_data["improvement"] = 0.0  # First iteration has no improvement
                        
                        # Update best solution
                        nonlocal best_score, best_solution
                        if score > best_score:
                            best_score = score
                            best_solution = improved_solution
                        
                        # Stream final iteration result
                        try:
                            await stream_callback({
                                "type": "iteration_complete",
                                "iteration": 1,
                                "solution": improved_solution,
                                "score": score,
                                "improvement": 0.0,
                                "status": "complete"
                            })
                        except (BrokenPipeError, ConnectionError, OSError) as e:
                            print(f"Connection closed during iteration_complete: {e}")
                            return
                        except Exception as e:
                            print(f"Error in stream_callback (iteration_complete): {e}")
                        
                    except Exception as e:
                        # Handle any errors in background task
                        error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
                        print(f"Error in background improvement task: {error_msg}")
                        try:
                            await stream_callback({
                                "type": "error",
                                "error": f"Error during background improvement: {error_msg}",
                                "iteration": 1
                            })
                        except (BrokenPipeError, ConnectionError, OSError):
                            print("Connection closed, cannot send error event")
                        except Exception as callback_error:
                            print(f"Error sending error event: {callback_error}")
                
                # Start background task for first iteration
                background_task = asyncio.create_task(improve_in_background())
                # Continue to next iteration or return (don't wait for background task)
                continue
            
            # For subsequent iterations or non-streaming: run normally
            # Step 2: Sutra critiques
            sutra_result = await self.sutra.process(
                yantra_output=current_solution,
                original_task=task,
                rag_chunks=rag_chunks,
                strict_rag=strict_rag,
                is_code_task=is_code,  # Pass is_code to Sutra
                use_fast_mode=use_fast_mode  # Enable fast mode for simple questions
            )
            iteration_data["sutra_critique"] = sutra_result["critique"]
            
            # Step 3: Agni improves
            agni_result = await self.agni.process(
                original_output=current_solution,
                critique=sutra_result["critique"],
                task=task,
                rag_chunks=rag_chunks,
                strict_rag=strict_rag,
                is_code_task=is_code,  # Pass is_code to Agni
                use_fast_mode=use_fast_mode  # Enable fast mode for simple questions
            )
            iteration_data["agni_output"] = agni_result["improved_output"]
            current_solution = agni_result["improved_output"]
            
            # Stream improved response
            if stream_callback is not None:
                try:
                    await stream_callback({
                        "type": "improved",
                        "iteration": iteration + 1,
                        "solution": agni_result["improved_output"],
                        "score": None,  # Will be updated after evaluation
                        "status": "improving"
                    })
                except (BrokenPipeError, ConnectionError, OSError) as e:
                    print(f"Connection closed during improved: {e}")
                except Exception as e:
                    print(f"Error in stream_callback: {e}")  # Don't fail if callback errors
            
            # Step 4: Evaluate (pass iteration number for progressive scoring)
            score_result = self.evaluator.evaluate(
                solution=current_solution,
                task=task,
                is_code=is_code,
                rag_chunks=rag_chunks,
                iteration_num=iteration
            )
            score = score_result["total"]
            iteration_data["score"] = score
            iteration_data["score_details"] = score_result
            
            # Stream final iteration result
            if stream_callback is not None:
                try:
                    improvement = score - iterations[-1]["score"] if iteration > 0 else 0.0
                    await stream_callback({
                        "type": "iteration_complete",
                        "iteration": iteration + 1,
                        "solution": current_solution,
                        "score": score,
                        "improvement": improvement,
                        "status": "complete"
                    })
                except (BrokenPipeError, ConnectionError, OSError) as e:
                    print(f"Connection closed during iteration_complete: {e}")
                except Exception as e:
                    print(f"Error in stream_callback: {e}")  # Don't fail if callback errors
            
            # Calculate improvement
            if iteration > 0:
                prev_score = iterations[-1]["score"]
                improvement = score - prev_score
                iteration_data["improvement"] = improvement
            else:
                iteration_data["improvement"] = 0.0
            
            iterations.append(iteration_data)
            
            # Update best solution
            if score > best_score:
                best_score = score
                best_solution = current_solution
            
            # Simple early stopping: if improvement is minimal, stop
            if iteration > 0:
                prev_score = iterations[-1]["score"]
                improvement = score - prev_score
                if improvement < self.min_improvement and iteration >= 1:
                    break
        
        # Wait for background task to complete (if it exists) before sending final event
        if background_task is not None:
            try:
                await background_task
            except Exception as e:
                print(f"Background task error: {e}")
        
        # Store best solution in memory (but not for strict RAG queries)
        if best_score > 0.6 and not strict_rag:  # Only store if score is decent and not strict RAG
            asyncio.create_task(
                asyncio.to_thread(
                    self.smriti.store,
                    task=task,
                    solution=best_solution,
                    quality_score=best_score,
                    metadata={
                        "is_code": is_code,
                        "used_rag": use_rag,
                        "iterations": len(iterations)
                    }
                )
            )
        
        # Stream final result (after background task completes)
        if stream_callback is not None:
            try:
                await stream_callback({
                    "type": "final",
                    "solution": best_solution,
                    "score": best_score,
                    "iterations": len(iterations),
                    "status": "done"
                })
            except (BrokenPipeError, ConnectionError, OSError) as e:
                print(f"Connection closed during final: {e}")
            except Exception as e:
                print(f"Error in stream_callback (final): {e}")  # Don't fail if callback errors
        
        return {
            "task": task,
            "final_solution": best_solution,
            "final_score": best_score,
            "iterations": iterations,
            "total_iterations": len(iterations),
            "used_rag": use_rag,
            "rag_chunks": rag_chunks if use_rag else None
        }

