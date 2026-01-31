"""Yantra - Generation Agent that produces initial solutions."""
from typing import Optional, List, Dict, Any
from .base_agent import BaseAgent


class Yantra(BaseAgent):
    """Generation agent that creates initial solutions."""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "qwen2.5:1.5b"):
        super().__init__("Yantra", ollama_url, model)
    
    async def process(
        self,
        task: str,
        context: Optional[str] = None,
        rag_chunks: Optional[List[str]] = None,
        past_examples: Optional[List[str]] = None,
        strict_rag: bool = False
    ) -> Dict[str, Any]:
        """Generate initial solution."""
        
        # Build system prompt
        if strict_rag and rag_chunks:
            system_prompt = (
                "You are Yantra, an expert problem solver with EXTREME accuracy requirements. "
                "Your PRIMARY and ONLY job is to answer based EXCLUSIVELY on the provided document context. "
                "\n\nCRITICAL RULES:\n"
                "1. Read ALL provided document chunks carefully and completely.\n"
                "2. Extract information ONLY from the documents - do NOT add any external knowledge.\n"
                "3. If information is not explicitly stated in the documents, say 'This information is not available in the uploaded documents.'\n"
                "4. Be extremely precise - quote exact phrases from the documents when possible.\n"
                "5. Include page numbers or chunk references when available.\n"
                "6. Do NOT infer, assume, or add information not in the documents.\n"
                "7. If the documents contradict each other, mention both perspectives.\n"
                "8. Prioritize accuracy over completeness - it's better to say 'not found' than to guess."
            )
        else:
            system_prompt = (
                "You are Yantra, an expert problem solver. "
                "CRITICAL: Generate ONLY a MINIMAL working version. "
                "This is iteration 1 - create the SIMPLEST possible solution that works. "
                "DO NOT include:\n"
                "- Error handling (none at all)\n"
                "- Type hints (none)\n"
                "- Documentation/docstrings (none)\n"
                "- Optimization (none)\n"
                "- Edge case handling (only main happy path)\n"
                "- Unit tests (none)\n"
                "- Input validation (minimal)\n"
                "- Comments (minimal)\n\n"
                "Just make it WORK for the basic case. All improvements come in later iterations."
            )
        
        # Build user prompt
        user_prompt_parts = [f"Task: {task}"]
        
        # Add instruction for basic version if not strict RAG
        if not strict_rag:
            user_prompt_parts.append(
                "\n⚠️⚠️⚠️ GENERATE MINIMAL VERSION - ITERATION 1 ⚠️⚠️⚠️\n"
                "Create the ABSOLUTE MINIMUM working solution. SKIP ALL OF THESE:\n"
                "- NO error handling (skip completely)\n"
                "- NO type hints (skip completely)\n"
                "- NO documentation/docstrings (skip completely)\n"
                "- NO optimization (skip completely)\n"
                "- NO edge cases (only handle the main happy path)\n"
                "- NO unit tests (skip completely)\n"
                "- NO input validation (skip completely)\n"
                "- MINIMAL comments (only if absolutely necessary)\n\n"
                "Just write the bare minimum code that solves the basic case. "
                "Later iterations will add error handling, type hints, docs, tests, optimization, etc."
            )
        
        if rag_chunks:
            user_prompt_parts.append("\n--- Relevant Document Context ---")
            for i, chunk in enumerate(rag_chunks, 1):
                user_prompt_parts.append(f"\n[Document Chunk {i}]\n{chunk}")
            
            if strict_rag:
                user_prompt_parts.append(
                    "\n⚠️⚠️⚠️ CRITICAL INSTRUCTIONS FOR MAXIMUM ACCURACY MODE ⚠️⚠️⚠️:\n"
                    "1. Read ALL document chunks above COMPLETELY before answering.\n"
                    "2. Answer ONLY using information EXPLICITLY stated in the document chunks.\n"
                    "3. Do NOT use ANY external knowledge, general knowledge, or assumptions.\n"
                    "4. If information is not in the documents, you MUST state: 'This information is not available in the uploaded documents.'\n"
                    "5. Quote exact phrases from the documents when possible, using quotation marks.\n"
                    "6. Include page numbers or chunk references (e.g., '[Page X]' or '[Chunk Y]') for each fact.\n"
                    "7. Do NOT infer, extrapolate, or make logical leaps beyond what is directly stated.\n"
                    "8. If the question asks for something not in the documents, clearly state that.\n"
                    "9. Prioritize accuracy - it's better to be incomplete than incorrect.\n"
                    "10. Double-check your answer against the document chunks to ensure every claim is supported."
                )
            else:
                user_prompt_parts.append(
                    "\nIMPORTANT: Base your answer primarily on the provided document context above. "
                    "You may supplement with general knowledge if needed, but prioritize the document content."
                )
        
        if past_examples:
            user_prompt_parts.append("\n--- Successful Past Solutions for Similar Tasks ---")
            for i, example in enumerate(past_examples, 1):
                user_prompt_parts.append(f"\n[Example {i}]\n{example}")
            user_prompt_parts.append(
                "\nUse these examples as reference for best practices and patterns."
            )
        
        if context:
            user_prompt_parts.append(f"\n--- Additional Context ---\n{context}")
        
        user_prompt = "\n".join(user_prompt_parts)
        
        # Call Ollama
        response = await self._call_ollama(user_prompt, system_prompt)
        
        return {
            "agent": self.name,
            "output": response,
            "task": task,
            "used_rag": rag_chunks is not None and len(rag_chunks) > 0,
            "used_examples": past_examples is not None and len(past_examples) > 0
        }

