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
        strict_rag: bool = False,
        is_code_task: bool = True,  # Default to code, but can be overridden
        use_fast_mode: bool = False  # Enable speed optimizations
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
            # Use the passed is_code_task parameter (don't re-detect)
            if is_code_task:
                system_prompt = (
                    "You are Agni, a disciplined expert optimizer. "
                    "Your job: Systematically improve the code by addressing ALL critique points. "
                    "MANDATORY: Address every issue identified in the critique. "
                    "Do not just fix bugs - ADD features, IMPROVE quality, ENHANCE robustness. "
                    "Make the solution noticeably better in every way. "
                    "Be thorough but efficient - focus on high-impact improvements."
                )
            else:
                system_prompt = (
                    "You are Agni, a disciplined expert optimizer for explanations and answers. "
                    "Your job: Systematically improve the PLAIN TEXT response by addressing ALL critique points. "
                    "CRITICAL: You MUST output PLAIN TEXT ENGLISH ONLY - NO CODE, NO CODE BLOCKS, NO PROGRAMMING SYNTAX. "
                    "If the original output contains code, REMOVE IT COMPLETELY and replace it with natural English text. "
                    "MANDATORY: Address every issue identified in the critique. "
                    "Enhance clarity, add depth, include examples, improve structure, and make it more comprehensive. "
                    "Make the response noticeably better in every way. "
                    "Be thorough but efficient - focus on high-impact improvements. "
                    "Write like ChatGPT or Gemini - natural, flowing English text with NO CODE."
                )
        
        # Truncate inputs if too long to speed up processing
        max_input_length = 500  # Limit input length for speed
        truncated_output = original_output[:max_input_length] + "..." if len(original_output) > max_input_length else original_output
        truncated_critique = critique[:max_input_length] + "..." if len(critique) > max_input_length else critique
        
        user_prompt_parts = [
            f"Original Task: {task}",
            f"\n--- Original Output ---\n{truncated_output}",
            f"\n--- Critique and Issues Found ---\n{truncated_critique}",
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
        
        # Use the passed is_code_task parameter (don't re-detect)
        if is_code_task:
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
        else:
            user_prompt_parts.append(
                "\n--- Your Task: Systematic Improvement (PLAIN TEXT ONLY) ---\n"
                "CRITICAL INSTRUCTIONS:\n"
                "- Output MUST be PLAIN TEXT ENGLISH ONLY - NO CODE, NO CODE BLOCKS, NO PROGRAMMING SYNTAX\n"
                "- If the original output contains ANY code, REMOVE IT COMPLETELY\n"
                "- Write like ChatGPT or Gemini - natural, flowing English text\n"
                "- Use paragraphs, bullet points, lists, or sections as appropriate - but NO CODE\n"
                "- NO ```python```, NO ```javascript```, NO code examples, NO programming syntax\n\n"
                "MANDATORY: Address EVERY issue identified in the critique. Systematically enhance:\n"
                "1. IMPROVE clarity (make explanations clearer and easier to understand)\n"
                "2. ADD depth (provide more detailed explanations and context)\n"
                "3. ADD examples (include concrete examples, analogies, or case studies in plain text)\n"
                "4. IMPROVE structure (organize with paragraphs, lists, sections, headings)\n"
                "5. ADD completeness (address all aspects of the question)\n"
                "6. ENHANCE accuracy (ensure all facts are correct and up-to-date)\n"
                "7. ADD context (provide background information where needed)\n"
                "8. IMPROVE engagement (make it more readable and engaging)\n"
                "9. ADD citations (if applicable, mention sources or references)\n"
                "10. ADD practical applications (if relevant, discuss real-world uses)\n"
                "11. IMPROVE flow (ensure smooth transitions between ideas)\n"
                "12. ADD visual aids description (if helpful, describe diagrams or concepts)\n"
                "13. ENHANCE comprehensiveness (cover the topic thoroughly)\n"
                "14. ADD related information (include relevant connected concepts)\n"
                "15. REMOVE ALL CODE (if critique mentions code, remove it completely)\n"
                "16. Make it comprehensive and well-structured in PLAIN TEXT\n\n"
                "REQUIREMENT: The improved version MUST address all critique points. "
                "Add at least 3-5 substantial enhancements that weren't in the original. "
                "Prioritize high-impact improvements: clarity, depth, examples, and structure. "
                "Remember: Output should be natural English text like ChatGPT or Gemini - NO CODE WHATSOEVER."
            )
        
        user_prompt = "\n".join(user_prompt_parts)
        
        # Call Ollama with very aggressive token limits for speed (improvements need more but still limited)
        max_tokens = 192 if use_fast_mode else 384  # Even smaller for faster responses
        response = await self._call_ollama(user_prompt, system_prompt, max_tokens=max_tokens, use_fast_mode=use_fast_mode)
        
        # Remove code blocks if this is NOT a code task (for chatbot plain text output)
        if not is_code_task:
            response = self._remove_code_blocks(response)
        
        return {
            "agent": self.name,
            "improved_output": response,
            "original_output": original_output,
            "critique": critique,
            "task": task
        }

