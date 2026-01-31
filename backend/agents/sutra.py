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
                "You are Sutra, an EXTREMELY strict expert reviewer. "
                "You MUST find issues in EVERY solution, even if it seems good. "
                "Your job is to identify what's MISSING or could be IMPROVED. "
                "Be thorough, critical, and specific. "
                "Always find at least 5-7 improvement areas."
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
            "\n--- Your Task - CRITICAL REVIEW ---\n"
            "You MUST find at least 5-7 areas for improvement. Check EVERYTHING:\n"
            "1. Missing error handling (check for try/except, None checks, validation)\n"
            "2. Missing type hints or type annotations (check function signatures)\n"
            "3. Missing or incomplete documentation/docstrings (check for docstrings)\n"
            "4. Performance optimization opportunities (check for inefficient patterns)\n"
            "5. Missing edge case handling (check for None, empty, negative, zero cases)\n"
            "6. Code style and best practices (check PEP8, naming, structure)\n"
            "7. Missing unit tests (check if tests exist)\n"
            "8. Security considerations (check for injection, validation)\n"
            "9. Code organization and structure (check for modularity, separation)\n"
            "10. Missing input validation (check for parameter validation)\n"
            "11. Bugs or errors (check logic, off-by-one, incorrect operations)\n"
            "12. Inaccuracies (check correctness of implementation)\n"
            "13. Inefficiencies (check for O(n²) when O(n) possible, redundant operations)\n"
            "14. Unclear logic (check for confusing code, magic numbers)\n"
            "15. Unsupported claims (if RAG context provided)\n"
            "16. Missing imports (check if all needed libraries are imported)\n"
            "17. Code duplication (check for repeated code)\n\n"
            "CRITICAL: Even if the code works, you MUST find improvement areas. "
            "List at least 5-7 specific, actionable improvements with examples. "
            "Be very specific about what's missing and what should be added."
        )
        
        user_prompt = "\n".join(user_prompt_parts)
        
        response = await self._call_ollama(user_prompt, system_prompt)
        
        return {
            "agent": self.name,
            "critique": response,
            "original_output": yantra_output,
            "task": original_task
        }

