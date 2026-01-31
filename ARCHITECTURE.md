# System Architecture

## Overview

This is a multi-agent system that implements recursive learning for code generation and document-based question answering. The system uses four specialized agents that work together through an orchestrator to iteratively improve solutions.

## Agent System

### 🧑‍💻 Yantra - Generation Agent

**Purpose**: Generate initial solutions (code or answers)

**Responsibilities**:
- Takes user task as input
- Optionally uses RAG chunks for document-based context
- Optionally uses past examples from memory
- Produces initial solution

**Location**: `backend/agents/yantra.py`

**Prompt Structure**:
- System: "You are Yantra, an expert problem solver..."
- User: Task + RAG chunks + past examples

### 🔍 Sutra - Critique Agent

**Purpose**: Analyze solutions and find issues

**Responsibilities**:
- Reviews Yantra's output
- Identifies bugs, inaccuracies, inefficiencies
- Checks for unsupported claims (RAG validation)
- Provides detailed critique with fixes

**Location**: `backend/agents/sutra.py`

**Prompt Structure**:
- System: "You are Sutra, a strict expert reviewer..."
- User: Original output + task + RAG chunks (for verification)

### 🛠 Agni - Improvement Agent

**Purpose**: Rewrite solutions fixing all issues

**Responsibilities**:
- Takes original output + critique
- Addresses all identified issues
- Improves correctness, performance, clarity
- Fixes grounding mistakes (for RAG)

**Location**: `backend/agents/agni.py`

**Prompt Structure**:
- System: "You are Agni, an expert optimizer..."
- User: Original output + critique + task + RAG chunks

### 🧠 Smriti - Memory Agent

**Purpose**: Store and retrieve learning experiences

**Responsibilities**:
- Stores successful solutions with quality scores
- Retrieves similar past tasks
- Provides best examples to Yantra
- Enables experience-based learning

**Location**: `backend/agents/smriti.py`

**Storage**: SQLite database at `backend/data/memory.db`

## Recursive Learning Loop

```
1. Yantra generates solution v1
   ↓
2. Sutra critiques v1
   ↓
3. Agni improves → v2
   ↓
4. Evaluator scores v2
   ↓
5. If score improved → Store in Smriti
   ↓
6. Repeat 1-3 for N iterations or until score plateaus
```

**Configuration**:
- `max_iterations`: Maximum iterations (default: 3)
- `min_improvement`: Minimum score improvement to continue (default: 0.05)

**Location**: `backend/orchestrator.py`

## RAG System

**Purpose**: Retrieve relevant document chunks for context

**Features**:
- Simple keyword-based retrieval
- Stores documents in `backend/data/documents/`
- Indexes chunks in JSON format
- Returns top-k relevant chunks

**Integration**:
- Chunks injected into Yantra prompt
- Sutra verifies claims against chunks
- Agni fixes grounding mistakes

**Location**: `backend/rag/retriever.py`

## Evaluation Engine

**Purpose**: Score solution quality

**Metrics** (for code):
- Correctness (40% weight)
- Quality (30% weight)
- Completeness (30% weight)

**Metrics** (for RAG answers):
- Grounding (50% weight) - % supported by documents
- Clarity (30% weight)
- Completeness (20% weight)

**Location**: `backend/evaluation/evaluator.py`

## API Server

**Framework**: FastAPI

**Endpoints**:
- `POST /process` - Process a task through the agent system
- `GET /health` - Health check

**Location**: `backend/api.py`

**Request Format**:
```json
{
  "task": "Create a React hook...",
  "context": "Optional context",
  "use_rag": false,
  "is_code": true
}
```

**Response Format**:
```json
{
  "task": "...",
  "final_solution": "...",
  "final_score": 0.85,
  "iterations": [...],
  "total_iterations": 2,
  "used_rag": false,
  "rag_chunks": null
}
```

## Frontend

**Framework**: React + TypeScript + Vite

**Key Components**:
- `CodeAssistant` - Main UI for task input and results
- Displays iterations with agent outputs
- Shows scores and improvements
- Tabs for Yantra/Sutra/Agni outputs

**Location**: `src/components/code-assistant/CodeAssistant.tsx`

## Data Flow

```
User Input
    ↓
Frontend (React)
    ↓ HTTP POST
API Server (FastAPI)
    ↓
Orchestrator
    ↓
[RAG Retrieval] → Document Chunks
    ↓
[Memory Retrieval] → Past Examples
    ↓
Yantra → Initial Solution
    ↓
Sutra → Critique
    ↓
Agni → Improved Solution
    ↓
Evaluator → Score
    ↓
[If improved] → Memory Storage
    ↓
[Repeat if needed]
    ↓
Return to Frontend
```

## File Structure

```
backend/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py      # Base class for all agents
│   ├── yantra.py          # Generation agent
│   ├── sutra.py           # Critique agent
│   ├── agni.py            # Improvement agent
│   └── smriti.py          # Memory agent
├── rag/
│   ├── __init__.py
│   └── retriever.py       # RAG system
├── evaluation/
│   ├── __init__.py
│   └── evaluator.py       # Evaluation engine
├── data/
│   ├── memory.db          # SQLite database (created at runtime)
│   └── documents/         # RAG documents
├── orchestrator.py        # Main orchestrator
├── api.py                  # FastAPI server
├── test_agents.py         # Test script
└── requirements.txt       # Python dependencies

src/
├── components/
│   └── code-assistant/
│       └── CodeAssistant.tsx  # Main UI
└── ...
```

## Configuration

### Backend

Edit `backend/orchestrator.py`:
```python
orchestrator = Orchestrator(
    max_iterations=3,      # Max improvement iterations
    min_improvement=0.05    # Min score improvement to continue
)
```

### Ollama

Default configuration:
- URL: `http://localhost:11434`
- Model: `qwen2.5:1.5b`

Change in agent constructors if needed.

## Learning Behavior

1. **First Iteration**: Yantra uses past examples from Smriti (if available)
2. **Subsequent Iterations**: Yantra generates without examples (to avoid repetition)
3. **Storage**: Only solutions with score > 0.6 are stored
4. **Retrieval**: Similar tasks retrieved using text similarity (Jaccard)
5. **Updates**: If same task exists, only update if new score is better

## Extensibility

### Adding New Agents

1. Create class inheriting from `BaseAgent`
2. Implement `process()` method
3. Add to `agents/__init__.py`
4. Integrate into orchestrator

### Improving RAG

- Replace `SimpleRAGRetriever` with embedding-based retrieval
- Add vector database (e.g., Chroma, Pinecone)
- Implement semantic similarity search

### Enhancing Evaluation

- Add LLM-based evaluation
- Implement test execution for code
- Add more sophisticated metrics

## Performance Considerations

- Agents run sequentially (can be parallelized)
- Ollama API calls are async
- Memory operations are synchronous (SQLite)
- RAG retrieval is fast (in-memory)

## Security Notes

- No authentication (add for production)
- CORS enabled for localhost
- File uploads not validated (add validation)
- SQLite database not encrypted (consider for sensitive data)

