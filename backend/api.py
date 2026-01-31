"""FastAPI server for the agent system."""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
from orchestrator import Orchestrator
from rag.retriever import SimpleRAGRetriever
from analytics import AnalyticsTracker
import os
import io
from pypdf import PdfReader
import time

app = FastAPI(title="Agent System API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator, RAG, and analytics
# Share RAG retriever instance with orchestrator
rag_retriever = SimpleRAGRetriever()
orchestrator = Orchestrator()
# Make orchestrator use the same RAG instance
orchestrator.rag = rag_retriever
# Initialize analytics tracker
analytics = AnalyticsTracker()


class TaskRequest(BaseModel):
    task: str
    context: Optional[str] = None
    use_rag: bool = False
    is_code: bool = True


class DocumentQueryRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None  # If None, use all uploaded documents


class IterationResponse(BaseModel):
    iteration: int
    yantra_output: str
    sutra_critique: str
    agni_output: str
    score: float
    improvement: Optional[float]
    score_details: Dict[str, float]


class ProcessResponse(BaseModel):
    task: str
    final_solution: str
    final_score: float
    iterations: List[Dict[str, Any]]
    total_iterations: int
    used_rag: bool
    rag_chunks: Optional[List[str]]


class DocumentQueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    rag_chunks: List[str]


@app.get("/")
async def root():
    return {"message": "Agent System API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for RAG. Supports .txt, .md, and .pdf files."""
    try:
        # Read file content
        content = await file.read()
        filename = file.filename.lower()
        
        # Determine file type and extract text
        text_content = None
        
        if filename.endswith('.pdf'):
            # Extract text from PDF with enhanced extraction
            try:
                pdf_file = io.BytesIO(content)
                pdf_reader = PdfReader(pdf_file)
                text_parts = []
                total_pages = len(pdf_reader.pages)
                
                # Extract text from ALL pages with better extraction
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        # Try multiple extraction methods for better accuracy
                        page_text = page.extract_text()
                        
                        # If extraction is empty, try alternative method
                        if not page_text or not page_text.strip():
                            # Try extracting with layout preservation
                            try:
                                page_text = page.extract_text(extraction_mode="layout")
                            except:
                                pass
                        
                        if page_text and page_text.strip():
                            # Add page number marker for better context
                            text_parts.append(f"[Page {page_num}]\n{page_text.strip()}")
                    except Exception as e:
                        # Log but continue - don't skip pages
                        print(f"Warning: Could not extract text from page {page_num}: {e}")
                        # Add placeholder to maintain page structure
                        text_parts.append(f"[Page {page_num}]\n[Text extraction failed for this page]")
                
                if not text_parts or all("extraction failed" in part for part in text_parts):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Could not extract text from PDF ({total_pages} pages). The PDF might be image-based or corrupted."
                    )
                
                # Join with clear page separators
                text_content = "\n\n---\n\n".join(text_parts)
                
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error reading PDF: {str(e)}"
                )
        
        elif filename.endswith(('.txt', '.md', '.text')):
            # Decode as text
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                # Try other encodings
                try:
                    text_content = content.decode('latin-1')
                except UnicodeDecodeError:
                    raise HTTPException(
                        status_code=400,
                        detail="Could not decode text file. Please ensure it's UTF-8 encoded."
                    )
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload .txt, .md, or .pdf files."
            )
        
        if not text_content or not text_content.strip():
            raise HTTPException(
                status_code=400,
                detail="File appears to be empty or contains no extractable text."
            )
        
        # Add to RAG retriever
        rag_retriever.add_document(text_content, file.filename)
        
        return {
            "message": "Document uploaded successfully",
            "filename": file.filename,
            "size": len(text_content),
            "type": "pdf" if filename.endswith('.pdf') else "text"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.post("/query-document", response_model=DocumentQueryResponse)
async def query_document(request: DocumentQueryRequest):
    """Query uploaded documents using RAG."""
    try:
        # Retrieve more relevant chunks for better accuracy (like NotebookLM)
        rag_chunks = rag_retriever.retrieve(request.question, top_k=15)
        
        if not rag_chunks:
            raise HTTPException(
                status_code=404,
                detail="No relevant content found in uploaded documents. Please upload documents first."
            )
        
        # Use orchestrator with strict RAG mode and more iterations for accuracy
        start_time = time.time()
        result = await orchestrator.process(
            task=request.question,
            context=None,
            use_rag=True,
            is_code=False,
            strict_rag=True,  # Only use uploaded documents
            rag_chunks=rag_chunks,
            max_iterations=5  # More iterations for better accuracy
        )
        
        # Record analytics for document queries
        duration_ms = (time.time() - start_time) * 1000
        analytics.record_task(
            task=request.question,
            final_score=result["final_score"],
            iterations=result["iterations"],
            duration_ms=duration_ms,
            task_type="document"
        )
        
        # Format sources with more context
        sources = []
        for i, chunk in enumerate(rag_chunks):
            # Show more context (first 300 chars) for better source visibility
            preview_text = chunk[:300] + "..." if len(chunk) > 300 else chunk
            sources.append({
                "id": i + 1,
                "text": preview_text,
                "relevance": max(0.5, 0.95 - (i * 0.05)),  # More gradual relevance decrease
            })
        
        return {
            "answer": result["final_solution"],
            "sources": sources,
            "rag_chunks": rag_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process", response_model=ProcessResponse)
async def process_task(request: TaskRequest):
    """Process a task through the agent system."""
    start_time = time.time()
    try:
        result = await orchestrator.process(
            task=request.task,
            context=request.context,
            use_rag=request.use_rag,
            is_code=request.is_code
        )
        
        # Record analytics
        duration_ms = (time.time() - start_time) * 1000
        analytics.record_task(
            task=request.task,
            final_score=result["final_score"],
            iterations=result["iterations"],
            duration_ms=duration_ms,
            task_type="code" if request.is_code else "document"
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/stats")
async def memory_stats():
    """Get memory statistics."""
    # This would require adding a method to Smriti
    return {"message": "Memory stats endpoint - to be implemented"}


@app.get("/analytics/metrics")
async def get_analytics_metrics():
    """Get aggregated analytics metrics."""
    return analytics.get_metrics()


@app.get("/analytics/quality-improvement")
async def get_quality_improvement():
    """Get quality improvement data for chart."""
    return {"data": analytics.get_quality_improvement_data()}


@app.get("/analytics/performance-history")
async def get_performance_history():
    """Get performance history data."""
    return {"data": analytics.get_performance_history()}


@app.get("/analytics/recent-tasks")
async def get_recent_tasks():
    """Get recent tasks for history table."""
    return {"data": analytics.get_recent_tasks()}


@app.delete("/documents")
async def clear_documents():
    """Clear all uploaded documents."""
    try:
        rag_retriever.chunks = []
        rag_retriever._save_index()
        return {"message": "All documents cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
