"""Sutra - Critique Agent that analyzes and finds issues."""
from typing import Optional, List, Dict, Any
from .base_agent import BaseAgent


class Sutra(BaseAgent):
    """Critique agent that identifies problems in solutions."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "qwen2.5:1.5b"):
        super().__init__("Sutra", ollama_url, model)
    
    async def process(
        self,
        yantra_output: str,
        original_task: str,
        rag_chunks: Optional[List[str]] = None,
        strict_rag: bool = False
    ) -> Dict[str, Any]:
        """Analyze output and find issues."""
        
        if strict_rag and rag_chunks:
            system_prompt = (
                "You are Sutra, a strict expert reviewer. "
                "Your primary job is to verify that ALL information in the output comes ONLY from the provided documents. "
                "Flag ANY statement that is not directly supported by the document chunks. "
                "Be extremely strict - even minor additions of external knowledge should be flagged."
            )
        else:
            system_prompt = (
                "You are Sutra, a disciplined expert reviewer. "
                "Your job: Systematically identify what's MISSING or needs IMPROVEMENT. "
                "Be thorough, critical, and specific. "
                "MANDATORY: Find at least 5-7 concrete improvement areas. "
                "Focus on actionable issues that can be fixed in the next iteration."
            )
        
        user_prompt_parts = [
            f"Original Task: {original_task}",
            f"\n--- Yantra's Output ---\n{yantra_output}",
        ]
        
        if rag_chunks:
            user_prompt_parts.append("\n--- Document Context (for verification) ---")
            for i, chunk in enumerate(rag_chunks, 1):
                user_prompt_parts.append(f"\n[Chunk {i}]\n{chunk}")
            
            if strict_rag:
                user_prompt_parts.append(
                    "\n⚠️ STRICT VERIFICATION MODE:\n"
                    "1. Check EVERY claim in the output against the document chunks above.\n"
                    "2. Flag ANY information that is NOT in the provided documents as 'HALLUCINATION'.\n"
                    "3. Identify statements that are inferences or assumptions not directly stated in the documents.\n"
                    "4. Note if the answer includes general knowledge that should not be there.\n"
                    "5. Be extremely strict - the output should ONLY contain information from the documents."
                )
            else:
                user_prompt_parts.append(
                    "\nCheck if all claims in the output are supported by the document context. "
                    "Flag any hallucinations or unsupported statements."
                )
        
        user_prompt_parts.append(
            "\n--- Your Task: Systematic Review ---\n"
            "MANDATORY: Find at least 5-7 concrete improvement areas. Systematically check:\n"
            "1. Missing error handling (try/except, None checks, validation)\n"
            "2. Missing type hints/annotations (function signatures)\n"
            "3. Missing documentation/docstrings\n"
            "4. Performance issues (inefficient patterns, redundant operations)\n"
            "5. Missing edge cases (None, empty, negative, zero, boundary cases)\n"
            "6. Code quality (PEP8, naming, structure, clarity)\n"
            "7. Missing tests (unit tests, test coverage)\n"
            "8. Security issues (input validation, injection risks)\n"
            "9. Code organization (modularity, separation of concerns)\n"
            "10. Input validation gaps (parameter checks, type validation)\n"
            "11. Logic bugs (off-by-one, incorrect operations, edge cases)\n"
            "12. Code duplication (repeated patterns that should be refactored)\n"
            "13. Missing imports (required libraries not imported)\n"
            "14. Unclear code (magic numbers, confusing logic, poor naming)\n\n"
            "REQUIREMENT: List 5-7 specific, actionable improvements. "
            "For each issue, clearly state: (1) What's missing/wrong, (2) Why it matters, (3) How to fix it. "
            "Be concrete and specific - avoid vague statements."
        )
        
        user_prompt = "\n".join(user_prompt_parts)
        
        response = await self._call_ollama(user_prompt, system_prompt)
        
        return {
            "agent": self.name,
            "critique": response,
            "original_output": yantra_output,
            "task": original_task
        }

