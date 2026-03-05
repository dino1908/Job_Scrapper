#!/bin/bash

# Job Scrapper - Startup Script
# This script starts both backend and frontend servers

echo "🚀 Starting Job Scrapper Application..."
echo ""

# Check if backend is set up
if [ ! -d "backend/venv" ]; then
    echo "❌ Backend not set up. Running setup first..."
    cd backend
    chmod +x setup.sh
    ./setup.sh
    cd ..
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not installed. Installing..."
    cd frontend
    npm install
    cd ..
fi

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Warning: backend/.env not found"
    echo "Please create backend/.env (non-secret config)"
    echo "Example:"
    echo "  DATABASE_URL=sqlite:///./data/job_scrapper.db"
    echo ""
    echo "For API keys, use backend/.env.secrets:"
    echo "  MISTRAL_API_KEY=your_key_here"
    echo ""
    read -p "Press enter to continue anyway, or Ctrl+C to exit..."
fi

# Check if secrets file exists
if [ ! -f "backend/.env.secrets" ]; then
    echo "⚠️  Warning: backend/.env.secrets not found"
    echo "Create it and add API keys, for example:"
    echo "  MISTRAL_API_KEY=your_key_here"
    echo ""
    read -p "Press enter to continue anyway, or Ctrl+C to exit..."
fi

# Start backend
echo ""
echo "📦 Starting backend server..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Start frontend
echo ""
echo "🎨 Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Application started!"
echo ""
echo "📍 Backend:  http://localhost:8000"
echo "📍 Frontend: http://localhost:3000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "👋 Goodbye!"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for user to stop
wait
