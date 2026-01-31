"""Agni - Improvement Agent that rewrites solutions fixing issues."""
from typing import Optional, List, Dict, Any
from .base_agent import BaseAgent


class Agni(BaseAgent):
    """Improvement agent that fixes issues and optimizes solutions."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "qwen2.5:1.5b"):
        super().__init__("Agni", ollama_url, model)
    
    async def process(
        self,
        original_output: str,
        critique: str,
        task: str,
        rag_chunks: Optional[List[str]] = None,
        strict_rag: bool = False
    ) -> Dict[str, Any]:
        """Rewrite solution addressing all critiques."""
        
        if strict_rag and rag_chunks:
            system_prompt = (
                "You are Agni, an expert optimizer. "
                "Rewrite the solution fixing all issues identified in the critique. "
                "CRITICAL: You MUST use ONLY information from the provided document chunks. "
                "Remove ALL information that is not in the documents. "
                "If information is missing from the documents, explicitly state that it's not available."
            )
        else:
            system_prompt = (
                "You are Agni, a disciplined expert optimizer. "
                "Your job: Systematically improve the solution by addressing ALL critique points. "
                "MANDATORY: Address every issue identified in the critique. "
                "Do not just fix bugs - ADD features, IMPROVE quality, ENHANCE robustness. "
                "Make the solution noticeably better in every way. "
                "Be thorough but efficient - focus on high-impact improvements."
            )
        
        user_prompt_parts = [
            f"Original Task: {task}",
            f"\n--- Original Output ---\n{original_output}",
            f"\n--- Critique and Issues Found ---\n{critique}",
        ]
        
        if rag_chunks:
            user_prompt_parts.append("\n--- Document Context ---")
            for i, chunk in enumerate(rag_chunks, 1):
                user_prompt_parts.append(f"\n[Document Chunk {i}]\n{chunk}")
            
            if strict_rag:
                user_prompt_parts.append(
                    "\n⚠️⚠️⚠️ MAXIMUM ACCURACY MODE - CRITICAL RULES ⚠️⚠️⚠️:\n"
                    "1. Remove ALL information that is NOT explicitly stated in the document chunks above.\n"
                    "2. If the critique flags ANY hallucinations, unsupported claims, or external knowledge, REMOVE them completely.\n"
                    "3. Only include information that is DIRECTLY and EXPLICITLY stated in the document chunks.\n"
                    "4. If information is missing from the documents, you MUST state: 'This information is not available in the uploaded documents.'\n"
                    "5. For each fact in your answer, cite the specific document chunk or page number.\n"
                    "6. Do NOT add ANY external knowledge, inferences, or assumptions, even if they seem helpful or obvious.\n"
                    "7. If the critique says something is not in the documents, remove it immediately.\n"
                    "8. Prioritize accuracy over completeness - incomplete but accurate is better than complete but inaccurate.\n"
                    "9. Double-check every sentence against the document chunks to ensure it's supported.\n"
                    "10. If you're unsure if something is in the documents, don't include it."
                )
            else:
                user_prompt_parts.append(
                    "\nEnsure all claims are properly grounded in the document context."
                )
        
        user_prompt_parts.append(
            "\n--- Your Task: Systematic Improvement ---\n"
            "MANDATORY: Address EVERY issue identified in the critique. Systematically add:\n"
            "1. Fix ALL bugs and errors mentioned in critique\n"
            "2. ADD error handling (try/except, None checks, validation)\n"
            "3. ADD type hints/annotations to ALL functions\n"
            "4. ADD docstrings (purpose, parameters, returns, examples)\n"
            "5. ADD performance optimizations (efficient algorithms, avoid redundancy)\n"
            "6. ADD input validation (None, empty, invalid types, ranges)\n"
            "7. ADD edge case handling (None, empty, negative, zero, boundary cases)\n"
            "8. ADD unit tests (multiple test cases covering main and edge cases)\n"
            "9. IMPROVE code structure (modularize, separate concerns)\n"
            "10. ADD security measures (input validation, prevent injection)\n"
            "11. REMOVE duplication (refactor repeated code)\n"
            "12. ADD missing imports (ensure all required libraries)\n"
            "13. IMPROVE clarity (comments, clear names, remove magic numbers)\n"
            "14. FOLLOW best practices (PEP8, naming, code style)\n"
            "15. Make production-ready (robust, tested, documented, maintainable)\n\n"
            "REQUIREMENT: The improved version MUST address all critique points. "
            "Add at least 3-5 substantial improvements that weren't in the original. "
            "Prioritize high-impact improvements: error handling, type hints, tests, and documentation."
        )
        
        user_prompt = "\n".join(user_prompt_parts)
        
        response = await self._call_ollama(user_prompt, system_prompt)
        
        return {
            "agent": self.name,
            "improved_output": response,
            "original_output": original_output,
            "critique": critique,
            "task": task
        }

