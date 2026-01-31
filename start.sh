#!/bin/bash

# Start script for Chakra Agent System

echo "🚀 Starting Chakra Agent System..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start MySQL container
echo "📦 Starting MySQL container..."
docker-compose up -d mysql

# Wait for MySQL to be ready
echo "⏳ Waiting for MySQL to be ready..."
sleep 5

# Check MySQL health
for i in {1..30}; do
    if docker exec chakra_mysql mysqladmin ping -h localhost -u root -prootpassword --silent; then
        echo "✅ MySQL is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ MySQL failed to start. Please check docker-compose logs."
        exit 1
    fi
    sleep 1
done

# Install Python dependencies if needed
if [ ! -d "backend/venv" ]; then
    echo "📦 Setting up Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "📦 Activating Python virtual environment..."
    cd backend
    source venv/bin/activate
    cd ..
fi

# Install Node dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Start backend in background
echo "🔧 Starting backend server..."
cd backend
source venv/bin/activate
python api.py &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend server..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ All services started!"
echo ""
echo "📊 Backend API: http://localhost:8000"
echo "🎨 Frontend UI: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for user interrupt
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker-compose down; exit" INT

# Keep script running
wait

