"""Test RAG retrieval to verify it's working correctly."""
from rag.retriever import SimpleRAGRetriever

def test_rag():
    """Test RAG retrieval."""
    print("=" * 60)
    print("TESTING RAG RETRIEVAL")
    print("=" * 60)
    
    rag = SimpleRAGRetriever()
    
    print(f"\nTotal chunks in index: {len(rag.chunks)}")
    
    if len(rag.chunks) == 0:
        print("\n⚠️  No chunks found in RAG index!")
        print("   Please upload documents first using the /upload-document endpoint")
        return
    
    # Show first few chunks
    print("\nFirst 3 chunks preview:")
    for i, chunk in enumerate(rag.chunks[:3], 1):
        print(f"\n  Chunk {i} (source: {chunk.get('source', 'unknown')}):")
        print(f"    {chunk['text'][:150]}...")
    
    # Test retrieval
    test_queries = [
        "What is the main topic?",
        "Explain the key concepts",
        "Summarize the document"
    ]
    
    print("\n" + "=" * 60)
    print("TESTING RETRIEVAL")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        chunks = rag.retrieve(query, top_k=5)
        print(f"  Retrieved {len(chunks)} chunks")
        if chunks:
            for i, chunk in enumerate(chunks, 1):
                print(f"    Chunk {i}: {chunk[:100]}...")
        else:
            print("    ⚠️  No chunks retrieved!")

if __name__ == "__main__":
    test_rag()

