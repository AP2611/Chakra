#!/bin/bash

# Start the backend API server
echo "Starting Agent System Backend..."
echo "Make sure Ollama is running with qwen2.5:1.5b model installed"
echo ""

cd backend
python api.py

