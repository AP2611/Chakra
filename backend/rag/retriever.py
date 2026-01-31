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
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        query_phrases = [query_lower]  # Include full query as phrase
        
        # Extract 2-3 word phrases from query for better matching
        query_tokens = query_lower.split()
        for i in range(len(query_tokens) - 1):
            query_phrases.append(" ".join(query_tokens[i:i+2]))
        
        scored_chunks = []
        for chunk in self.chunks:
            chunk_text = chunk["text"].lower()
            chunk_words = set(chunk_text.split())
            
            # 1. Jaccard similarity (word overlap)
            intersection = len(query_words & chunk_words)
            union = len(query_words | chunk_words)
            jaccard_score = intersection / union if union > 0 else 0
            
            # 2. Phrase matching (exact phrase matches are more important)
            phrase_score = 0.0
            for phrase in query_phrases:
                if phrase in chunk_text:
                    phrase_score += 0.3  # Boost for phrase matches
            
            # 3. Keyword frequency (how many query words appear)
            keyword_count = sum(1 for word in query_words if word in chunk_text)
            keyword_score = keyword_count / len(query_words) if query_words else 0
            
            # 4. Position bonus (earlier in document might be more relevant)
            position_bonus = 0.0  # Could add if we track position
            
            # Combined score with weights
            total_score = (
                jaccard_score * 0.4 +
                min(phrase_score, 1.0) * 0.4 +
                keyword_score * 0.2
            )
            
            scored_chunks.append((total_score, chunk["text"]))
        
        # Sort by score and return top-k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Return chunks even with low scores if they're the best we have
        # But filter out completely irrelevant ones (score < 0.05)
        filtered_chunks = [(score, text) for score, text in scored_chunks if score >= 0.05]
        
        if not filtered_chunks and scored_chunks:
            # If nothing passes threshold, return top 3 anyway
            filtered_chunks = scored_chunks[:3]
        
        return [chunk_text for score, chunk_text in filtered_chunks[:top_k]]
    
    def add_document(self, content: str, source: str):
        """Add a new document to the index with improved chunking strategy."""
        # Split by paragraphs first
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        
        # Create smaller, overlapping chunks for better retrieval
        chunk_size = 500  # Characters per chunk
        overlap = 100  # Overlap between chunks
        
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

