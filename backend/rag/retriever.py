"""RAG (Retrieval-Augmented Generation) system for document retrieval."""
import os
from typing import List, Dict, Optional
from pathlib import Path
import json


class SimpleRAGRetriever:
    """Simple RAG retriever for document chunks."""
    
    def __init__(self, documents_dir: str = "backend/data/documents"):
        self.documents_dir = documents_dir
        self.chunks: List[Dict[str, str]] = []
        self._load_documents()
    
    def _load_documents(self):
        """Load and chunk documents."""
        os.makedirs(self.documents_dir, exist_ok=True)
        
        # Load from JSON index if it exists
        index_path = os.path.join(self.documents_dir, "index.json")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)
        else:
            # Scan for text files
            for file_path in Path(self.documents_dir).glob("*.txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Simple chunking by paragraphs
                    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                    for i, para in enumerate(paragraphs):
                        self.chunks.append({
                            "text": para,
                            "source": file_path.name,
                            "chunk_id": f"{file_path.stem}_{i}"
                        })
    
    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve top-k relevant chunks with improved scoring."""
        if not self.chunks:
            return []
        
        query_lower = query.lower().strip()
        query_words = set(query_lower.split())
        
        # Remove stop words for better matching (common words that don't add meaning)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom', 'where', 'when', 'why', 'how'}
        query_words = {w for w in query_words if w not in stop_words and len(w) > 2}
        
        # If no meaningful words left, use all words
        if not query_words:
            query_words = set(query_lower.split())
        
        query_phrases = [query_lower]  # Include full query as phrase
        
        # Extract 2-3 word phrases from query for better matching
        query_tokens = query_lower.split()
        for i in range(len(query_tokens) - 1):
            phrase = " ".join(query_tokens[i:i+2])
            if len(phrase) > 3:  # Only meaningful phrases
                query_phrases.append(phrase)
        
        scored_chunks = []
        for chunk in self.chunks:
            chunk_text_original = chunk["text"]  # Keep original for return
            chunk_text = chunk_text_original.lower()
            chunk_words = set(chunk_text.split())
            
            # 1. Jaccard similarity (word overlap) - improved with better handling
            intersection = len(query_words & chunk_words)
            union = len(query_words | chunk_words)
            jaccard_score = intersection / union if union > 0 else 0
            
            # Boost jaccard score if there's any overlap at all
            if intersection > 0:
                jaccard_score = max(jaccard_score, 0.1)  # Minimum score for any overlap
            
            # 2. Phrase matching (exact phrase matches are more important) - improved
            phrase_score = 0.0
            for phrase in query_phrases:
                if phrase in chunk_text:
                    # Longer phrases are more important
                    phrase_score += (0.2 + len(phrase.split()) * 0.1)
            
            # 3. Keyword frequency (how many query words appear) - improved
            keyword_count = sum(1 for word in query_words if word in chunk_text)
            keyword_score = keyword_count / len(query_words) if query_words else 0
            
            # Boost keyword score if at least one keyword matches
            if keyword_count > 0:
                keyword_score = max(keyword_score, 0.15)  # Minimum score for keyword match
            
            # 4. Word frequency (how often query words appear in chunk)
            word_freq_score = sum(chunk_text.count(word) for word in query_words) / max(len(chunk_text.split()), 1)
            
            # 5. Length bonus (longer chunks with matches are better)
            length_bonus = min(len(chunk_text) / 1000, 0.1) if intersection > 0 else 0
            
            # Combined score with improved weights
            total_score = (
                jaccard_score * 0.3 +
                min(phrase_score, 1.5) * 0.3 +  # Allow higher phrase scores
                keyword_score * 0.2 +
                min(word_freq_score, 0.5) * 0.15 +  # Word frequency
                length_bonus * 0.05
            )
            
            scored_chunks.append((total_score, chunk_text_original))  # Use original text
        
        # Sort by score and return top-k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Very lenient filtering - return chunks even with very low scores
        # Only filter out completely irrelevant ones (score < 0.001)
        # But prioritize higher-scored chunks
        filtered_chunks = [(score, text) for score, text in scored_chunks if score >= 0.001]
        
        if not filtered_chunks and scored_chunks:
            # If nothing passes threshold, return top chunks anyway (even with score 0)
            # This ensures we always return something if chunks exist
            filtered_chunks = scored_chunks[:top_k]
        elif len(filtered_chunks) < top_k:
            # If we have fewer than top_k, return what we have plus some lower-scored ones
            filtered_chunks = scored_chunks[:top_k]
        
        # Always return at least top_k chunks if available, even with low scores
        # This ensures we have enough context for the LLM
        if len(scored_chunks) >= top_k:
            filtered_chunks = scored_chunks[:top_k]
        elif filtered_chunks:
            # Use what we have
            pass
        else:
            # Last resort: return any chunks we have
            filtered_chunks = scored_chunks[:min(top_k, len(scored_chunks))]
        
        # Debug: Log what we're returning
        if filtered_chunks:
            print(f"RAG: Returning {len(filtered_chunks[:top_k])} chunks with scores: {[f'{s:.3f}' for s, _ in filtered_chunks[:top_k]]}")
        
        # Return original text (not lowercased) for better context
        return [chunk_text for score, chunk_text in filtered_chunks[:top_k]]
    
    def add_document(self, content: str, source: str):
        """Add a new document to the index with improved chunking strategy."""
        # Split by paragraphs first
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        
        # Create larger, overlapping chunks for better context preservation
        chunk_size = 1000  # Characters per chunk (increased from 500 for better context)
        overlap = 200  # Overlap between chunks (increased from 100)
        
        for para in paragraphs:
            if len(para) <= chunk_size:
                # Small paragraph - add as single chunk
                self.chunks.append({
                    "text": para,
                    "source": source,
                    "chunk_id": f"{source}_{len(self.chunks)}"
                })
            else:
                # Large paragraph - split into overlapping chunks
                start = 0
                chunk_num = 0
                while start < len(para):
                    end = start + chunk_size
                    chunk_text = para[start:end]
                    
                    # Try to break at sentence boundaries
                    if end < len(para):
                        # Look for sentence endings near the end
                        for punct in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                            last_punct = chunk_text.rfind(punct)
                            if last_punct > chunk_size * 0.7:  # If found in last 30%
                                chunk_text = para[start:start + last_punct + 1]
                                end = start + last_punct + 1
                                break
                    
                    if chunk_text.strip():
                        self.chunks.append({
                            "text": chunk_text.strip(),
                            "source": source,
                            "chunk_id": f"{source}_{len(self.chunks)}"
                        })
                    
                    # Move start with overlap
                    start = max(start + 1, end - overlap)
                    chunk_num += 1
        
        # Save to index
        self._save_index()
    
    def _save_index(self):
        """Save chunks to index file."""
        index_path = os.path.join(self.documents_dir, "index.json")
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2)

