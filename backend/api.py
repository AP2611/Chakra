"""FastAPI server for the agent system."""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
import json
import asyncio

app = FastAPI(title="Agent System API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080", "http://localhost:8081"],  # Vite default ports
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
        # Retrieve relevant chunks (balanced for speed and accuracy)
        rag_chunks = rag_retriever.retrieve(request.question, top_k=8)  # Reduced from 15 to 8
        
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
            max_iterations=1  # Only 1 iteration for speed
        )
        
        # Record analytics in background (non-blocking)
        duration_ms = (time.time() - start_time) * 1000
        asyncio.create_task(
            asyncio.to_thread(
                analytics.record_task,
                request.question,
                result["final_score"],
                result["iterations"],
                duration_ms,
                "document"
            )
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
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in query_document: {error_msg}\n{error_trace}")  # Log to console
        raise HTTPException(status_code=500, detail=f"Error querying document: {error_msg}")


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
        
        # Record analytics in background (non-blocking)
        duration_ms = (time.time() - start_time) * 1000
        asyncio.create_task(
            asyncio.to_thread(
                analytics.record_task,
                request.task,
                result["final_score"],
                result["iterations"],
                duration_ms,
                "code" if request.is_code else "document"
            )
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in process_task: {error_msg}\n{error_trace}")  # Log to console
        raise HTTPException(status_code=500, detail=f"Error processing task: {error_msg}")


@app.post("/process-stream")
async def process_task_stream(request: TaskRequest):
    """Process a task with streaming responses (fast first response)."""
    start_time = time.time()
    
    async def generate():
        try:
            # Use unbounded queue for instant delivery (no blocking)
            queue = asyncio.Queue(maxsize=0)  # Unbounded queue for instant delivery
            
            async def stream_callback(data):
                # Put immediately without waiting (non-blocking for instant delivery)
                await queue.put(data)
            
            # Start processing in background
            async def process_background():
                try:
                    result = await orchestrator.process(
                        task=request.task,
                        context=request.context,
                        use_rag=request.use_rag,
                        is_code=request.is_code,
                        stream_callback=stream_callback
                    )
                    
                    # Record analytics AFTER all background tasks complete (non-blocking)
                    # This ensures we have complete iteration data including improvements
                    duration_ms = (time.time() - start_time) * 1000
                    asyncio.create_task(
                        asyncio.to_thread(
                            analytics.record_task,
                            request.task,
                            result["final_score"],
                            result["iterations"],
                            duration_ms,
                            "code" if request.is_code else "document"
                        )
                    )
                    
                    await queue.put({"type": "end"})
                except Exception as e:
                    error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
                    await queue.put({"type": "error", "error": error_msg})
            
            # Start background processing
            asyncio.create_task(process_background())
            
            # Stream responses as they come - immediate delivery
            while True:
                data = await queue.get()
                
                if data["type"] == "end":
                    break
                elif data["type"] == "error":
                    yield f"data: {json.dumps(data)}\n\n"
                    break
                else:
                    # Yield immediately for instant delivery to frontend
                    yield f"data: {json.dumps(data)}\n\n"
                    
        except Exception as e:
            error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
            yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
    
    # Use StreamingResponse with no buffering for instant delivery
    return StreamingResponse(
        generate(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering if present
        }
    )


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
