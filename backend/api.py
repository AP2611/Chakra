"""FastAPI server for the agent system."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
from orchestrator import Orchestrator

app = FastAPI(title="Agent System API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = Orchestrator()


class TaskRequest(BaseModel):
    task: str
    context: Optional[str] = None
    use_rag: bool = False
    is_code: bool = True


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


@app.get("/")
async def root():
    return {"message": "Agent System API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/process", response_model=ProcessResponse)
async def process_task(request: TaskRequest):
    """Process a task through the agent system."""
    try:
        result = await orchestrator.process(
            task=request.task,
            context=request.context,
            use_rag=request.use_rag,
            is_code=request.is_code
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/stats")
async def memory_stats():
    """Get memory statistics."""
    # This would require adding a method to Smriti
    return {"message": "Memory stats endpoint - to be implemented"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

