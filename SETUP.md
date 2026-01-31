# Setup Guide

## Prerequisites

1. **Node.js** (v18 or higher)
2. **Python** (v3.8 or higher)
3. **Ollama** installed and running

## Step-by-Step Setup

### 1. Install Ollama

Download and install Ollama from https://ollama.com

### 2. Pull the Required Model

```bash
ollama pull qwen2.5:1.5b
```

Verify the model is available:
```bash
ollama list
```

### 3. Start Ollama (if not running as service)

```bash
ollama serve
```

Keep this terminal open. The default port is 11434.

### 4. Setup Backend

```bash
cd backend
pip install -r requirements.txt
```

### 5. Test Backend (Optional)

```bash
python test_agents.py
```

This will verify that:
- Ollama is accessible
- The model is available
- Agents can communicate with Ollama

### 6. Start Backend Server

In a new terminal:

```bash
cd backend
python api.py
```

Or use the startup script:
```bash
./start_backend.sh
```

The API will be available at `http://localhost:8000`

### 7. Setup Frontend

In the project root:

```bash
npm install
```

### 8. Start Frontend

In a new terminal:

```bash
npm run dev
```

The frontend will be available at `http://localhost:8080` (or the port shown in the terminal)

### 9. Configure API URL (Optional)

If your backend is running on a different port or host, create a `.env` file:

```
VITE_API_URL=http://localhost:8000
```

## Verification

1. Open `http://localhost:8080` in your browser
2. You should see the Code Assistant interface
3. Enter a simple task like: "Write a Python function to calculate the sum of a list"
4. Click "Generate & Improve"
5. Watch the agents work through iterations

## Troubleshooting

### Backend Issues

**Error: "Error calling Ollama API"**
- Make sure Ollama is running: `ollama serve`
- Verify the model is installed: `ollama list`
- Check if Ollama is accessible: `curl http://localhost:11434/api/tags`

**Error: "Module not found"**
- Make sure you're in the `backend` directory
- Run `pip install -r requirements.txt` again

### Frontend Issues

**Error: "Failed to fetch" or CORS errors**
- Make sure the backend is running on port 8000
- Check the browser console for the exact error
- Verify `VITE_API_URL` in `.env` matches your backend URL

**Port already in use**
- Change the port in `vite.config.ts` or kill the process using the port

## Next Steps

- Add documents to `backend/data/documents/` for RAG functionality
- Customize agent prompts in `backend/agents/`
- Adjust iteration limits in `backend/orchestrator.py`

