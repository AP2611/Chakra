# Chakra - Recursive Agent System

A multi-agent system with recursive learning capabilities that generates, critiques, improves, and learns from code and document-based solutions.

## Features

- **🧑‍💻 Yantra** - Generates initial solutions
- **🔍 Sutra** - Critiques and finds issues
- **🛠 Agni** - Improves solutions based on critiques
- **🧠 Smriti** - Stores and retrieves learning experiences
- **📚 RAG Integration** - Document-based context retrieval
- **🔄 Recursive Learning** - Iterative improvement loop
- **📈 Evaluation Engine** - Quality scoring system

## Architecture

```
User Task
    ↓
[RAG Retrieval] (optional)
    ↓
[Smriti Memory] → Past Examples
    ↓
Yantra → Initial Solution
    ↓
Sutra → Critique
    ↓
Agni → Improved Solution
    ↓
Evaluator → Score
    ↓
[If improved] → Smriti Memory
    ↓
[Repeat until plateau]
```

## Quick Start

### Backend Setup

1. **Install Ollama** and pull the model:
   ```bash
   ollama pull qwen2.5:1.5b
   ```

2. **Install Python dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Start the API server**:
   ```bash
   python api.py
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Configure API URL** (optional):
   Create `.env` file:
   ```
   VITE_API_URL=http://localhost:8000
   ```

## Usage

1. Open the application in your browser (default: http://localhost:8080)
2. Enter a task description in the Code Assistant
3. Optionally enable RAG for document-based context
4. Click "Generate & Improve"
5. Watch the agents work through iterations
6. View the final solution and iteration history

## Project Structure

```
.
├── backend/
│   ├── agents/          # Agent implementations
│   │   ├── yantra.py    # Generation agent
│   │   ├── sutra.py     # Critique agent
│   │   ├── agni.py      # Improvement agent
│   │   └── smriti.py    # Memory agent
│   ├── rag/             # RAG system
│   ├── evaluation/      # Evaluation engine
│   ├── orchestrator.py  # Main orchestrator
│   └── api.py          # FastAPI server
├── src/
│   ├── components/
│   │   └── code-assistant/  # Frontend UI
│   └── pages/
└── package.json
```

## Technology Stack

- **Backend**: Python, FastAPI, Ollama (qwen2.5:1.5b)
- **Frontend**: React, TypeScript, Vite, shadcn/ui, Tailwind CSS
- **Storage**: SQLite (for memory), JSON (for RAG index)

## Development

### Running Tests

```bash
npm test
```

### Building for Production

```bash
npm run build
```

## License

MIT
