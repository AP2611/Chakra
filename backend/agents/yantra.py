"""Yantra - Generation Agent that produces initial solutions."""
from typing import Optional, List, Dict, Any, Callable, Awaitable
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
        strict_rag: bool = False,
        is_code_task: bool = True,  # Default to code, but can be overridden
        use_fast_mode: bool = False,  # Enable speed optimizations
        token_callback: Optional[Callable[[str], Awaitable[None]]] = None  # Callback for token streaming (async function)
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
            # Use the passed is_code_task parameter (don't re-detect)
            if is_code_task:
                system_prompt = (
                    "You are Yantra, an expert problem solver. "
                    "STRICT RULE: Generate ONLY the absolute MINIMAL working version. "
                    "This is iteration 1 - create the SIMPLEST possible solution that works for the basic case only. "
                    "\nMANDATORY EXCLUSIONS (do NOT include any of these):\n"
                    "- Error handling (completely skip)\n"
                    "- Type hints (completely skip)\n"
                    "- Documentation/docstrings (completely skip)\n"
                    "- Optimization (completely skip)\n"
                    "- Edge case handling (only handle the main happy path)\n"
                    "- Unit tests (completely skip)\n"
                    "- Input validation (completely skip)\n"
                    "- Comments (only if absolutely critical)\n\n"
                    "Your goal: Write the bare minimum code that solves the basic case. "
                    "All improvements (error handling, type hints, docs, tests, optimization) will be added in later iterations. "
                    "Do NOT add anything beyond the absolute minimum required to make it work."
                )
            else:
                system_prompt = (
                    "You are Yantra, an expert explainer and conversationalist. "
                    "Your job: Provide a clear, concise initial answer to the question in PLAIN TEXT ENGLISH. "
                    "CRITICAL: You MUST respond in natural, conversational English text - NO CODE, NO CODE BLOCKS, NO PROGRAMMING SYNTAX. "
                    "This is iteration 1 - give a basic but correct response. "
                    "Keep it simple and straightforward. "
                    "Focus on answering the core question without excessive detail. "
                    "Write like ChatGPT or Gemini - natural, flowing English text. "
                    "Later iterations will add depth, examples, and comprehensive explanations."
                )
        
        # Build user prompt
        user_prompt_parts = [f"Task: {task}"]
        
        # Add instruction for basic version if not strict RAG
        if not strict_rag:
            if is_code_task:
                user_prompt_parts.append(
                    "\n⚠️ STRICT MINIMAL MODE - ITERATION 1 ⚠️\n"
                    "Create ONLY the absolute minimum working solution. STRICTLY EXCLUDE:\n"
                    "- NO error handling (completely skip)\n"
                    "- NO type hints (completely skip)\n"
                    "- NO documentation/docstrings (completely skip)\n"
                    "- NO optimization (completely skip)\n"
                    "- NO edge cases (only handle main happy path)\n"
                    "- NO unit tests (completely skip)\n"
                    "- NO input validation (completely skip)\n"
                    "- MINIMAL comments (only if critical)\n\n"
                    "Write ONLY the bare minimum code that solves the basic case. "
                    "All enhancements will be added in later iterations. "
                    "Focus on correctness for the basic case only - nothing more."
                )
            else:
                user_prompt_parts.append(
                    "\n📝 ITERATION 1 - Basic Response (PLAIN TEXT ONLY)\n"
                    "CRITICAL INSTRUCTIONS:\n"
                    "- Respond in NATURAL, CONVERSATIONAL ENGLISH TEXT ONLY\n"
                    "- NO CODE, NO CODE BLOCKS, NO PROGRAMMING SYNTAX\n"
                    "- NO ```python```, NO ```javascript```, NO code examples\n"
                    "- Write like ChatGPT or Gemini - flowing, natural English\n"
                    "- Provide a clear, concise answer to the question\n"
                    "- Keep it simple and direct. Focus on the core answer\n"
                    "- Later iterations will add depth, examples, and comprehensive explanations\n"
                    "- Use paragraphs, bullet points, or lists as appropriate - but NO CODE"
                )
        
        if rag_chunks:
            user_prompt_parts.append("\n--- Relevant Document Context ---")
            # Include ALL chunks for maximum context (don't truncate chunks)
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
        
        # Call Ollama with balanced token limits (increased for longer responses)
        max_tokens = 384 if use_fast_mode else 640  # Increased from 256/512 for longer responses
        
        # Use streaming if token_callback is provided (for first response streaming)
        if token_callback:
            response = await self._call_ollama_stream(
                user_prompt, 
                system_prompt, 
                max_tokens=max_tokens, 
                use_fast_mode=use_fast_mode,
                token_callback=token_callback
            )
        else:
            response = await self._call_ollama(user_prompt, system_prompt, max_tokens=max_tokens, use_fast_mode=use_fast_mode)
        
        # Remove code blocks if this is NOT a code task (for chatbot plain text output)
        if not is_code_task:
            response = self._remove_code_blocks(response)
        
        return {
            "agent": self.name,
            "output": response,
            "task": task,
            "used_rag": rag_chunks is not None and len(rag_chunks) > 0,
            "used_examples": past_examples is not None and len(past_examples) > 0
        }

