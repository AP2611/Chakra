"""Orchestrator that coordinates all agents in the recursive learning loop."""
from typing import Dict, Any, List, Optional
import asyncio
from agents import Yantra, Sutra, Agni, Smriti
from rag.retriever import SimpleRAGRetriever
from evaluation.evaluator import Evaluator


class Orchestrator:
    """Orchestrates the multi-agent system with recursive learning."""
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2.5:1.5b",
        max_iterations: int = 3,
        min_improvement: float = 0.05
    ):
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
        is_code: bool = True
    ) -> Dict[str, Any]:
        """Process a task through the recursive learning loop."""
        
        # Retrieve RAG chunks if needed
        rag_chunks = None
        if use_rag:
            rag_chunks = self.rag.retrieve(task, top_k=3)
        
        # Retrieve similar past examples from memory
        past_examples = []
        similar_tasks = self.smriti.retrieve_similar(task, limit=3)
        if similar_tasks:
            past_examples = [ex["solution"] for ex in similar_tasks]
        
        iterations = []
        best_score = 0.0
        best_solution = None
        current_solution = None
        
        for iteration in range(self.max_iterations):
            iteration_data = {
                "iteration": iteration + 1,
                "yantra_output": None,
                "sutra_critique": None,
                "agni_output": None,
                "score": None,
                "improvement": None
            }
            
            # Step 1: Yantra generates solution
            yantra_result = await self.yantra.process(
                task=task,
                context=context,
                rag_chunks=rag_chunks,
                past_examples=past_examples if iteration == 0 else None  # Only use examples in first iteration
            )
            iteration_data["yantra_output"] = yantra_result["output"]
            current_solution = yantra_result["output"]
            
            # Step 2: Sutra critiques
            sutra_result = await self.sutra.process(
                yantra_output=current_solution,
                original_task=task,
                rag_chunks=rag_chunks
            )
            iteration_data["sutra_critique"] = sutra_result["critique"]
            
            # Step 3: Agni improves
            agni_result = await self.agni.process(
                original_output=current_solution,
                critique=sutra_result["critique"],
                task=task,
                rag_chunks=rag_chunks
            )
            iteration_data["agni_output"] = agni_result["improved_output"]
            current_solution = agni_result["improved_output"]
            
            # Step 4: Evaluate
            score_result = self.evaluator.evaluate(
                solution=current_solution,
                task=task,
                is_code=is_code,
                rag_chunks=rag_chunks
            )
            score = score_result["total"]
            iteration_data["score"] = score
            iteration_data["score_details"] = score_result
            
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
            
            # Check if we should continue
            if iteration > 0:
                improvement = score - iterations[-2]["score"]
                if improvement < self.min_improvement:
                    # Score plateaued, stop
                    break
        
        # Store best solution in memory
        if best_score > 0.6:  # Only store if score is decent
            self.smriti.store(
                task=task,
                solution=best_solution,
                quality_score=best_score,
                metadata={
                    "is_code": is_code,
                    "used_rag": use_rag,
                    "iterations": len(iterations)
                }
            )
        
        return {
            "task": task,
            "final_solution": best_solution,
            "final_score": best_score,
            "iterations": iterations,
            "total_iterations": len(iterations),
            "used_rag": use_rag,
            "rag_chunks": rag_chunks if use_rag else None
        }

